# PHP Backend - PHP REPL Server v2.0

PHP backend providing session-based stateful PHP REPL via HTTP API using PHP's built-in server with persistent execution contexts.

## Stack

- **Runtime**: PHP 8.2 CLI
- **Server**: PHP Built-in Web Server
- **Execution**: Safe eval with session-based variable persistence
- **Container**: php:8.2-cli base image (`webrepl-backend-php`)
- **Session Management**: Session-based persistent variable contexts

## Features

- Session-based PHP execution with persistent variables and functions per session
- Custom output capture via PHP's output buffering mechanism
- Comprehensive error handling and exception reporting
- Session-specific context reset functionality
- Expression evaluation with automatic result display
- Session isolation preventing cross-session variable access
- Support for both expressions and statements

## API Endpoints

### `POST /execute/{sessionId}`
Execute PHP code in session-specific persistent context.

**Request:**
```json
{
  "code": "$x = 42; echo $x * 2;"
}
```

**Response:**
```json
{
  "output": "84",
  "error": null
}
```

### `POST /reset/{sessionId}`
Clear execution context and reset all variables for specific session.

**Response:**
```json
{
  "message": "Context reset successfully",
  "sessionId": "uuid"
}
```

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "language": "php",
  "version": "2.0.0",
  "stateless": false,
  "timestamp": "2025-01-01T00:00:00Z"
}
```

## Session Architecture

### Persistent Variable Contexts
- Each session ID maintains its own isolated variable context
- Variables, functions, and classes persist between executions within sessions
- Sessions are completely isolated from each other
- Context persists until session is reset or container restart

### Session Isolation Example
```php
// Session A
$x = 10;
function greet($name) {
    return "Hello, " . $name . "!";
}

// Session B (completely separate)
$x = 20;  // Different from Session A's $x
$y = 30;  // Session A cannot see this variable
```

## Execution Model

The backend maintains session-specific variable contexts where:
- Variables and functions persist across executions within the same session
- Output is captured via PHP's output buffering (ob_start/ob_get_contents)
- Parse errors, runtime errors, and exceptions are caught and returned as JSON
- Variable context is serialized/deserialized for session persistence
- Each session has its own isolated variable scope

## Development

### Local Development Setup
```bash
# Start development server
php -S 0.0.0.0:8000 server.php
```

### Docker
```bash
# Build image
docker build -t webrepl-backend-php .

# Run container
docker run -p 8000:8000 webrepl-backend-php
```

## Configuration

- **CORS**: Environment-based configuration
  - Development (`ENVIRONMENT=development`): Allows all origins
  - Production: Restricted to specific frontend origins
- **Port**: 8000 (internal container port)
- **Host**: 0.0.0.0 (binds to all interfaces)
- **Session Storage**: Serialized context data stored in memory

## Code Execution Flow

1. Receive POST request with PHP code and session ID
2. Get session context variables from session storage
3. Extract context variables into local scope using `$$key = $value`
4. Start output buffering to capture output
5. Try expression evaluation first, then statement execution if that fails
6. Capture updated variables back to context array using `get_defined_vars()`
7. Serialize and save updated context to session storage
8. Return structured response with output/error

## Session Management Implementation

```php
// Session contexts stored in memory
$session_contexts = [];

function getSessionContext($sessionId) {
    global $session_contexts;
    if (!isset($session_contexts[$sessionId])) {
        $session_contexts[$sessionId] = [];
    }
    return $session_contexts[$sessionId];
}

function saveSessionContext($sessionId, $context) {
    global $session_contexts;
    $session_contexts[$sessionId] = $context;
}

function resetSessionContext($sessionId) {
    global $session_contexts;
    $session_contexts[$sessionId] = [];
}
```

## Error Handling

- **Parse Errors**: PHP syntax errors caught and returned in `error` field
- **Runtime Errors**: PHP Error and Exception classes handled gracefully
- **Fatal Errors**: Fatal errors caught where possible
- **Empty Code**: Returns HTTP 400 with appropriate error message

## Expression vs Statement Detection

The backend intelligently handles both expressions and statements:

```php
// Expressions (return values)
2 + 2           // Returns: 4
$x = 5          // Returns: 5
strlen("hello") // Returns: 5

// Statements (no return value, but may produce output)
echo "Hello";   // Output: "Hello"
for ($i = 0; $i < 3; $i++) echo $i; // Output: "012"
```

## PHP Capabilities

The REPL supports comprehensive PHP language features:
- **Variables**: All PHP variable types ($scalars, $arrays, $objects)
- **Functions**: User-defined functions, closures, anonymous functions
- **Classes**: OOP with classes, inheritance, interfaces, traits
- **Built-ins**: All PHP built-in functions and constants
- **Control Flow**: if/else, loops, switch statements
- **Arrays**: Indexed and associative arrays with all array functions
- **Strings**: String manipulation and formatting functions

## Example Usage

```php
// Basic calculations
$result = 2 + 2;
echo $result;

// Array operations
$numbers = [1, 2, 3, 4, 5];
$doubled = array_map(function($n) { return $n * 2; }, $numbers);
print_r($doubled);

// String manipulation
$text = "Hello World";
echo strtoupper(strrev($text));

// Define a class (persists in session)
class Person {
    public $name;
    public $age;
    
    public function __construct($name, $age) {
        $this->name = $name;
        $this->age = $age;
    }
    
    public function greeting() {
        return "Hi, I'm {$this->name} and I'm {$this->age} years old";
    }
}

// Create instance (uses the previously defined class)
$person = new Person("Alice", 30);
echo $person->greeting();

// Associative arrays
$data = ["name" => "Bob", "age" => 25];
$data["location"] = "San Francisco";
print_r($data);
```

## Security

- Code executes in the same PHP process with container-level isolation
- No timeout protection implemented (consider adding for production)
- No filesystem access restrictions beyond container boundaries
- No network access restrictions beyond container boundaries
- Session isolation prevents cross-session variable access
- Context variables are serialized using PHP's serialize/unserialize functions
- CORS configured for frontend domain only in production

## Testing

The PHP backend includes a comprehensive test suite using containerized testing with session-manager integration.

#### Automated Test Suite

**Run all tests**:
```bash
./test.sh
```

The test script:
- Builds containerized test environment with session-manager dependency
- Runs comprehensive API tests via Docker Compose
- Tests both traditional execution and session persistence
- Ensures proper session isolation and cleanup
- Returns exit code 0 for success, 1 for failure

**Test Architecture**:
- `tests/docker-compose.yml`: Orchestrates session-manager + php-backend + test runner containers
- `tests/test.py`: Pytest-based test suite with comprehensive endpoint coverage
- `tests/Dockerfile`: Python test runner container with pytest and requests
- `tests/requirements.txt`: Python dependencies (pytest + requests)
- Health checks ensure both session-manager and backend are ready before running tests

**Test Coverage**:
- Health endpoint validation
- Variable persistence across executions
- Function and class persistence
- Session isolation between different session IDs
- Error handling (syntax errors, runtime errors, validation)
- PHP language features (arrays, classes, built-in functions)
- Control structures (loops, conditionals)
- JSON operations and string manipulation
- Expression evaluation and session reset functionality
- Complex PHP features (closures, array functions)

#### Manual Testing
```bash
# Health check
curl http://localhost:8000/health

# Execute code (requires valid session)
curl -X POST http://localhost:8000/execute/session-uuid \
  -H "Content-Type: application/json" \
  -d '{"code": "$x = 42; echo $x;"}'

# Reset session
curl -X POST http://localhost:8000/reset/session-uuid
```

**Note**: Manual testing requires a valid session created through the session-manager service.

## Performance Considerations

- Variable context serialization/deserialization adds overhead
- Session cleanup happens automatically on container restart
- Memory usage grows with number of active sessions and their data
- Consider implementing session cleanup for production deployments

## Implementation Notes

- Uses PHP's `eval()` function for code execution (inherent security risk - container isolation is critical)
- Variable persistence achieved through `get_defined_vars()` and dynamic variable creation using `$$key = $value`
- Expression vs statement detection using regex patterns and eval attempt
- Error handling covers ParseError, Error, Exception, and Throwable classes
- Output buffering captures all output including echo, print, var_dump, etc.

## Advanced PHP Features

The REPL supports advanced PHP capabilities:
- **Namespaces**: use statements and namespace declarations
- **Traits**: trait definition and usage
- **Closures**: Anonymous functions and closures with use() clause
- **Generators**: yield and generator functions
- **Magic Methods**: __construct, __toString, __get, __set, etc.
- **Static Methods**: Class::method() static method calls
- **Constants**: define() and const declarations

## File Structure

```
backend/php/
├── server.php          # Main PHP application with session integration
├── Dockerfile          # Container configuration
├── .dockerignore       # Build exclusions
├── test.sh             # Test runner script for containerized testing
├── tests/              # Comprehensive test suite
│   ├── docker-compose.yml  # Test orchestration with session-manager
│   ├── Dockerfile      # Python test runner container
│   ├── requirements.txt     # Python test dependencies
│   └── test.py         # Pytest test suite (24 test cases)
└── CLAUDE.md           # This documentation
```