require 'sinatra'
require 'sinatra/cors'
require 'json'
require 'stringio'
require 'base64'
require 'net/http'
require 'uri'

# Configure Sinatra
set :bind, '0.0.0.0'
set :port, 8000

# Configure CORS
set :allow_origin, "*"
set :allow_methods, "GET,HEAD,POST,OPTIONS"
set :allow_headers, "content-type,if-modified-since"
set :expose_headers, "location,link"

# Session Manager URL
SESSION_MANAGER_URL = 'http://session-manager:8000'

# Ruby environment serialization functions
def serialize_binding(binding_obj)
  begin
    # Extract local and instance variables from the binding
    serializable = {
      'local_variables' => {},
      'instance_variables' => {}
    }
    
    binding_obj.local_variables.each do |var_name|
      value = binding_obj.local_variable_get(var_name)
      # Use Marshal to serialize Ruby objects
      serializable['local_variables'][var_name.to_s] = Base64.encode64(Marshal.dump(value))
    rescue => e
      # Skip variables that can't be serialized
      puts "Warning: Could not serialize local variable #{var_name}: #{e}"
    end
    
    binding_obj.eval('instance_variables').each do |var_name|
      value = binding_obj.eval(var_name.to_s)
      begin
        serializable['instance_variables'][var_name.to_s] = Base64.encode64(Marshal.dump(value))
      rescue => e
        puts "Warning: Could not serialize instance variable #{var_name}: #{e}"
      end
    end
    
    Base64.encode64(Marshal.dump(serializable))
  rescue => e
    puts "Failed to serialize binding: #{e}"
    ''
  end
end

def deserialize_binding(serialized_data)
  begin
    return binding if serialized_data.nil? || serialized_data.empty?
    
    data = Marshal.load(Base64.decode64(serialized_data))
    new_binding = binding
    
    # Restore local variables
    data['local_variables']&.each do |var_name, serialized_value|
      value = Marshal.load(Base64.decode64(serialized_value))
      new_binding.local_variable_set(var_name.to_sym, value)
    rescue => e
      puts "Warning: Could not restore local variable #{var_name}: #{e}"
    end
    
    # Restore instance variables
    data['instance_variables']&.each do |var_name, serialized_value|
      value = Marshal.load(Base64.decode64(serialized_value))
      new_binding.eval("#{var_name} = value")
    rescue => e
      puts "Warning: Could not restore instance variable #{var_name}: #{e}"
    end
    
    new_binding
  rescue => e
    puts "Failed to deserialize binding: #{e}"
    binding
  end
end

def get_session_binding(session_id)
  begin
    uri = URI("#{SESSION_MANAGER_URL}/sessions/#{session_id}/environment")
    response = Net::HTTP.get_response(uri)
    
    if response.code == '200'
      data = JSON.parse(response.body)
      if data['environment'] && data['environment']['serialized_data']
        return deserialize_binding(data['environment']['serialized_data'])
      end
    end
    
    binding
  rescue => e
    puts "Failed to get session environment: #{e}"
    binding
  end
end

def save_session_binding(session_id, binding_obj)
  begin
    serialized_data = serialize_binding(binding_obj)
    
    uri = URI("#{SESSION_MANAGER_URL}/sessions/#{session_id}/environment")
    http = Net::HTTP.new(uri.host, uri.port)
    
    request = Net::HTTP::Put.new(uri)
    request['Content-Type'] = 'application/json'
    request.body = {
      language: 'ruby',
      serialized_data: serialized_data
    }.to_json
    
    http.request(request)
  rescue => e
    puts "Failed to save session environment: #{e}"
  end
end

def verify_session_language(session_id)
  begin
    uri = URI("#{SESSION_MANAGER_URL}/sessions/#{session_id}")
    response = Net::HTTP.get_response(uri)
    
    if response.code == '200'
      data = JSON.parse(response.body)
      return data['language'] == 'ruby'
    end
    
    false
  rescue => e
    puts "Failed to verify session language: #{e}"
    false
  end
end

def notify_session_manager(session_id)
  begin
    uri = URI("#{SESSION_MANAGER_URL}/sessions/#{session_id}/activity?language=ruby")
    http = Net::HTTP.new(uri.host, uri.port)
    request = Net::HTTP::Put.new(uri)
    http.request(request)
  rescue => e
    puts "Failed to notify session manager: #{e}"
  end
end

# Capture stdout and stderr
class OutputCapture
  def self.capture
    old_stdout = $stdout
    old_stderr = $stderr
    stdout_io = StringIO.new
    stderr_io = StringIO.new
    
    $stdout = stdout_io
    $stderr = stderr_io
    
    result = nil
    error = nil
    
    begin
      result = yield
    rescue Exception => e
      error = e
    ensure
      $stdout = old_stdout
      $stderr = old_stderr
    end
    
    {
      result: result,
      stdout: stdout_io.string,
      stderr: stderr_io.string,
      error: error
    }
  end
end

# Health check endpoint
get '/health' do
  content_type :json
  { status: 'ok', language: 'ruby', stateless: true }.to_json
end

# Execute Ruby code endpoint
post '/execute/:session_id' do
  request.body.rewind
  data = JSON.parse(request.body.read)
  code = data['code']
  session_id = params['session_id']
  
  # Verify session is configured for Ruby
  unless verify_session_language(session_id)
    content_type :json
    status 400
    return { output: '', error: "Session #{session_id} is not configured for Ruby" }.to_json
  end
  
  if code.nil? || code.empty?
    content_type :json
    return { output: '', error: 'Code parameter is required' }.to_json
  end
  
  # Get session-specific binding from session manager
  session_binding = get_session_binding(session_id)
  
  # Capture output and execute code
  capture_result = OutputCapture.capture do
    eval(code, session_binding)
  end
  
  # Save updated binding back to session manager
  save_session_binding(session_id, session_binding)
  
  # Notify session manager of activity  
  notify_session_manager(session_id)
  
  output = capture_result[:stdout]
  
  # If there's a result and no printed output, show the result
  if capture_result[:result] && output.empty?
    output = capture_result[:result].inspect + "\n"
  end
  
  # Handle errors
  error = nil
  if capture_result[:error]
    error = "#{capture_result[:error].class}: #{capture_result[:error].message}"
  elsif !capture_result[:stderr].empty?
    error = capture_result[:stderr]
  end
  
  content_type :json
  { 
    output: output || '',
    error: error
  }.to_json
end

# Reset Ruby environment endpoint
post '/reset/:session_id' do
  begin
    session_id = params['session_id']
    
    # Clear environment in session manager
    uri = URI("#{SESSION_MANAGER_URL}/sessions/#{session_id}/environment")
    http = Net::HTTP.new(uri.host, uri.port)
    request = Net::HTTP::Delete.new(uri)
    
    response = http.request(request)
    
    if response.code == '200'
      content_type :json
      { message: 'Environment reset successfully' }.to_json
    elsif response.code == '404'
      content_type :json
      status 404
      { error: 'Session not found' }.to_json  
    else
      content_type :json
      status 500
      { error: 'Failed to reset environment' }.to_json
    end
  rescue => e
    puts "Reset error: #{e}"
    content_type :json
    status 500
    { error: 'Failed to reset environment' }.to_json
  end
end

# Handle OPTIONS for CORS preflight
options '*' do
  200
end