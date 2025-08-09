# Ruby Backend - Interactive Ruby REPL Server v2.0

Ruby backend providing session-based stateful Ruby REPL via HTTP API using the Sinatra framework with persistent execution bindings.

## Stack

- **Runtime**: Ruby 3.2
- **Framework**: Sinatra with CORS middleware
- **Execution**: Native Ruby eval() with session-based persistent bindings
- **Server**: Puma web server
- **Container**: ruby:3.2-slim base image (`webrepl-backend-ruby`)
- **Session Management**: Session-based persistent bindings

## Features

- Session-based Ruby execution with persistent variables and methods per session
- Output capture including puts/print statements and expression results
- Comprehensive error handling and exception reporting
- Session-specific environment reset functionality
- CORS support for web frontend integration
- Expression evaluation with automatic result display
- Session isolation preventing cross-session variable access

## API Endpoints

### `POST /execute/{sessionId}`
Execute Ruby code in session-specific persistent binding.

**Request:**
```json
{
  "code": "x = [1, 2, 3, 4, 5]\nputs x.sum"
}
```

**Response:**
```json
{
  "output": "15\n",
  "error": null
}
```

### `POST /reset/{sessionId}`
Clear Ruby environment and reset all variables for specific session.

**Response:**
```json
{
  "message": "Environment reset successfully",
  "sessionId": "uuid"
}
```

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "language": "ruby",
  "version": "2.0.0",
  "stateless": false,
  "timestamp": "2025-01-01T00:00:00Z"
}
```

## Session Architecture

### Persistent Bindings
- Each session ID maintains its own isolated Ruby binding context
- Variables, methods, classes, and constants persist between executions within sessions
- Sessions are completely isolated from each other
- Binding persists until session is reset or container restart

### Session Isolation Example
```ruby
# Session A
x = 10
def greet(name)
  "Hello, #{name}!"
end

# Session B (completely separate)
x = 20  # Different from Session A's x
y = 30  # Session A cannot see this variable
```

## Execution Model

The backend maintains session-specific Ruby bindings where:
- Variables, methods, and classes persist across executions within the same session
- Built-in Ruby methods and classes remain available in all sessions
- Output from puts/print and expression results are captured via StringIO
- Errors are caught and returned as structured JSON
- Each session has its own isolated binding context

## Ruby Capabilities

The REPL supports full Ruby language features:
- **Data Structures**: Arrays, Hashes, Strings, Symbols, Sets
- **Object-Oriented**: Classes, modules, inheritance, mixins
- **Functional**: Blocks, procs, lambdas, iterators
- **Built-in Methods**: Enumerable, string manipulation, math, file operations
- **Metaprogramming**: Dynamic method definition, reflection, eval
- **Advanced Features**: Regular expressions, constants, global variables

## Development

### Local Development Setup
```bash
# Install dependencies (if Gemfile exists)
bundle install

# Run the server
ruby app.rb

# Run tests
ruby test_api.rb
```

### Docker
```bash
# Build image
docker build -t webrepl-backend-ruby .

# Run container
docker run -p 8000:8000 webrepl-backend-ruby

# Run tests in container
docker exec webrepl-backend-ruby ruby test_api.rb
```

## Configuration

- **CORS**: Environment-based configuration
  - Development (`ENVIRONMENT=development`): Allows all origins
  - Production: Restricted to specific frontend origins
- **Port**: 8000 (internal container port)
- **Host**: 0.0.0.0 (binds to all interfaces)
- **Session Storage**: In-memory Hash with session ID keys

## Code Execution Flow

1. Receive POST request with Ruby code and session ID
2. Get or create session-specific Ruby binding
3. Set up StringIO objects for output capture
4. Execute code in session binding using `eval(code, session_binding)`
5. Capture output and any exceptions
6. Return structured response with output/error
7. Preserve binding context for subsequent executions

## Session Management Implementation

```ruby
# Session bindings stored in memory
$session_bindings = {}

def get_session_binding(session_id)
  $session_bindings[session_id] ||= binding
end

def reset_session_binding(session_id)
  $session_bindings[session_id] = binding
end
```

## Error Handling

- **Syntax Errors**: Ruby parsing errors caught and returned
- **Runtime Errors**: Exceptions during execution caught and formatted
- **Standard Errors**: StandardError and subclasses handled gracefully
- **Empty Code**: Returns HTTP 400 with appropriate error message

## Example Usage

```ruby
# Basic calculations
2 + 2

# Array operations
numbers = [1, 2, 3, 4, 5]
numbers.map { |n| n * 2 }

# String manipulation
"hello".upcase.reverse

# Define a class (persists in session)
class Person
  attr_accessor :name, :age
  
  def initialize(name, age)
    @name = name
    @age = age
  end
  
  def greeting
    "Hi, I'm #{@name} and I'm #{@age} years old"
  end
end

# Create instance (uses the previously defined class)
person = Person.new("Alice", 30)
person.greeting

# Hash operations
data = { name: "Bob", age: 25 }
data[:location] = "San Francisco"
puts data

# Regular expressions
text = "Hello World 123"
text.scan(/\d+/)  # Extract numbers

# Block iteration
(1..5).each { |i| puts "Number: #{i}" }
```

## Security

- Code executes in main Ruby process within container isolation
- No timeout protection implemented (consider adding for production)
- Session isolation prevents cross-session data access
- Environment can be reset per session to clear problematic state
- CORS configured for frontend domain only in production

## Testing

The test suite (`test_api.rb`) verifies:
- Health check endpoint functionality
- Basic expression evaluation and output capture
- Variable and method persistence between executions within same session
- Session isolation (different sessions don't share variables)
- Error handling for syntax and runtime errors
- Environment reset functionality per session
- Multi-line code execution
- Class and module definition persistence
- Built-in Ruby method availability

```bash
# Run tests locally
ruby test_api.rb

# Run tests in Docker container
docker exec webrepl-backend-ruby ruby test_api.rb
```

## Performance Considerations

- Ruby binding creation is lightweight, bindings are reused per session
- Session cleanup happens automatically on container restart
- Memory usage grows with number of active sessions and their defined objects
- Consider implementing session cleanup for production deployments

## Advanced Ruby Features

The REPL supports advanced Ruby capabilities:
- **Constants**: Module and class constants with proper scoping
- **Global Variables**: $global_variables accessible across session
- **Instance Variables**: @instance_vars in top-level context
- **Class Variables**: @@class_vars when defined within classes
- **Method Visibility**: private, protected, public method definitions
- **Module Inclusion**: include, extend, prepend for mixins