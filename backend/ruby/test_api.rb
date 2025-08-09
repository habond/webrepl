#!/usr/bin/env ruby
# Test suite for Ruby REPL backend
# Tests the core functionality: execution, persistence, and reset

require 'net/http'
require 'json'
require 'uri'
require 'securerandom'

BASE_URL = 'http://localhost:8000'
TEST_SESSION_ID = SecureRandom.uuid

class TestRunner
  def initialize
    @passed = 0
    @failed = 0
  end

  def make_request(method, path, data = nil)
    uri = URI.parse("#{BASE_URL}#{path}")
    
    case method
    when :get
      request = Net::HTTP::Get.new(uri)
    when :post
      request = Net::HTTP::Post.new(uri)
      request.content_type = 'application/json'
      request.body = data.to_json if data
    end

    response = Net::HTTP.start(uri.hostname, uri.port) do |http|
      http.request(request)
    end

    {
      status: response.code.to_i,
      body: JSON.parse(response.body)
    }
  rescue => e
    raise "Request failed: #{e.message}"
  end

  def assert(condition, message)
    unless condition
      raise AssertionError, message
    end
  end

  def test_health_check
    response = make_request(:get, '/health')
    assert(response[:status] == 200, 'Health check status should be 200')
    assert(response[:body]['status'] == 'ok', 'Health status should be ok')
    assert(response[:body]['language'] == 'ruby', 'Language should be ruby')
    puts '✓ Health check passed'
  end

  def test_simple_expression
    response = make_request(:post, "/execute/#{TEST_SESSION_ID}", { code: '2 + 2' })
    assert(response[:status] == 200, 'Execute status should be 200')
    assert(response[:body]['output'] == "4\n", 'Output should be 4')
    assert(response[:body]['error'].nil?, 'Error should be nil')
    puts '✓ Simple expression evaluation passed'
  end

  def test_puts_output
    response = make_request(:post, "/execute/#{TEST_SESSION_ID}", { code: 'puts "Hello, Ruby!"' })
    assert(response[:status] == 200, 'Execute status should be 200')
    assert(response[:body]['output'] == "Hello, Ruby!\n", 'Output should match')
    assert(response[:body]['error'].nil?, 'Error should be nil')
    puts '✓ Puts output capture passed'
  end

  def test_variable_persistence
    # Set a variable
    response = make_request(:post, "/execute/#{TEST_SESSION_ID}", { code: '@test_var = 42' })
    assert(response[:status] == 200, 'Execute status should be 200')
    
    # Use the variable in another execution
    response = make_request(:post, "/execute/#{TEST_SESSION_ID}", { code: '@test_var * 2' })
    assert(response[:status] == 200, 'Execute status should be 200')
    assert(response[:body]['output'] == "84\n", 'Output should be 84')
    assert(response[:body]['error'].nil?, 'Error should be nil')
    puts '✓ Variable persistence passed'
  end

  def test_error_handling
    response = make_request(:post, "/execute/#{TEST_SESSION_ID}", { code: '1 / 0' })
    assert(response[:status] == 200, 'Execute status should be 200')
    assert(!response[:body]['error'].nil?, 'Error should not be nil')
    assert(response[:body]['error'].include?('ZeroDivisionError'), 'Error should be ZeroDivisionError')
    puts '✓ Error handling passed'
  end

  def test_reset_functionality
    # Set a variable
    response = make_request(:post, "/execute/#{TEST_SESSION_ID}", { code: '@reset_test_var = 999' })
    assert(response[:status] == 200, 'Execute status should be 200')
    
    # Reset the environment
    response = make_request(:post, "/reset/#{TEST_SESSION_ID}")
    assert(response[:status] == 200, 'Reset status should be 200')
    assert(response[:body]['message'] == 'Environment reset successfully', 'Reset message should match')
    
    # Try to access the variable (should be nil)
    response = make_request(:post, "/execute/#{TEST_SESSION_ID}", { code: '@reset_test_var' })
    assert(response[:status] == 200, 'Execute status should be 200')
    # In Ruby, undefined instance variables return nil
    assert(response[:body]['output'] == "" || response[:body]['output'] == "\n" || response[:body]['output'] == "nil\n", 
           'Variable should be nil after reset')
    puts '✓ Reset functionality passed'
  end

  def test_multiline_code
    code = <<~RUBY
      def factorial(n)
        return 1 if n <= 1
        n * factorial(n - 1)
      end
      puts factorial(5)
    RUBY
    
    response = make_request(:post, "/execute/#{TEST_SESSION_ID}", { code: code })
    assert(response[:status] == 200, 'Execute status should be 200')
    assert(response[:body]['output'] == "120\n", 'Output should be 120')
    assert(response[:body]['error'].nil?, 'Error should be nil')
    puts '✓ Multiline code execution passed'
  end

  def test_class_definition
    # Define a class
    code1 = <<~RUBY
      class TestPerson
        attr_accessor :name, :age
        
        def initialize(name, age)
          @name = name
          @age = age
        end
        
        def greeting
          "Hello, I'm \#{@name} and I'm \#{@age} years old"
        end
      end
    RUBY
    
    response = make_request(:post, "/execute/#{TEST_SESSION_ID}", { code: code1 })
    assert(response[:status] == 200, 'Execute status should be 200')
    
    # Use the class
    code2 = 'person = TestPerson.new("Alice", 30); puts person.greeting'
    response = make_request(:post, "/execute/#{TEST_SESSION_ID}", { code: code2 })
    assert(response[:status] == 200, 'Execute status should be 200')
    assert(response[:body]['output'] == "Hello, I'm Alice and I'm 30 years old\n", 'Output should match')
    puts '✓ Class definition and usage passed'
  end

  def test_array_operations
    code = '[1, 2, 3, 4, 5].map { |n| n * 2 }.sum'
    response = make_request(:post, "/execute/#{TEST_SESSION_ID}", { code: code })
    assert(response[:status] == 200, 'Execute status should be 200')
    assert(response[:body]['output'] == "30\n", 'Output should be 30')
    assert(response[:body]['error'].nil?, 'Error should be nil')
    puts '✓ Array operations passed'
  end

  def test_string_interpolation
    # Set a variable
    response = make_request(:post, "/execute/#{TEST_SESSION_ID}", { code: '@name = "Ruby"' })
    assert(response[:status] == 200, 'Execute status should be 200')
    
    # Use string interpolation
    response = make_request(:post, "/execute/#{TEST_SESSION_ID}", { code: 'puts "Hello from #{@name}!"' })
    assert(response[:status] == 200, 'Execute status should be 200')
    assert(response[:body]['output'] == "Hello from Ruby!\n", 'Output should match')
    puts '✓ String interpolation passed'
  end

  def run_all_tests
    puts "\n=== Ruby Backend Test Suite ===\n"
    
    tests = [
      :test_health_check,
      :test_simple_expression,
      :test_puts_output,
      :test_variable_persistence,
      :test_error_handling,
      :test_reset_functionality,
      :test_multiline_code,
      :test_class_definition,
      :test_array_operations,
      :test_string_interpolation
    ]
    
    tests.each do |test|
      begin
        send(test)
        @passed += 1
      rescue => e
        puts "✗ #{test} failed: #{e.message}"
        if e.message.include?('Connection refused')
          puts '  Make sure the Ruby backend is running on port 8000'
        end
        @failed += 1
      end
    end
    
    puts "\n=== Results: #{@passed}/#{tests.length} tests passed ===\n"
    @failed == 0
  end
end

# Custom error class for assertions
class AssertionError < StandardError; end

# Run tests
if __FILE__ == $0
  runner = TestRunner.new
  success = runner.run_all_tests
  exit(success ? 0 : 1)
end