# JavaScript Backend - Node.js REPL Server v2.0

Node.js backend providing session-based stateful JavaScript REPL via HTTP API with persistent execution contexts.

## Stack

- **Runtime**: Node.js 20+ 
- **Framework**: Express.js with CORS middleware
- **Execution**: Node.js VM module for sandboxed code execution
- **Container**: node:20-alpine base image (`webrepl-backend-javascript`)
- **Session Management**: Session-based persistent VM contexts

## Features

- Session-based JavaScript execution with persistent variables per session
- Custom console.log/error capture and output redirection
- 5-second execution timeout for safety
- Session-specific context reset functionality
- Expression evaluation with automatic result display
- Comprehensive error handling and reporting
- Session isolation preventing cross-session variable access

## API Endpoints

### `POST /execute/{sessionId}`
Execute JavaScript code in session-specific persistent context.

**Request:**
```json
{
  "code": "const x = 42; console.log(x * 2);"
}
```

**Response:**
```json
{
  "output": "84\n",
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
  "language": "javascript",
  "version": "2.0.0",
  "stateless": false,
  "timestamp": "2025-01-01T00:00:00Z"
}
```

## Session Architecture

### Persistent VM Contexts
- Each session ID maintains its own isolated Node.js VM context
- Variables, functions, and objects persist between executions within sessions
- Sessions are completely isolated from each other
- Context persists until session is reset or container restart

### Session Isolation Example
```javascript
// Session A
const x = 10;
function greet(name) {
    return `Hello, ${name}!`;
}

// Session B (completely separate)
const x = 20;  // Different from Session A's x
const y = 30;  // Session A cannot see this variable
```

## Execution Model

The backend maintains session-specific VM contexts where:
- Variables and functions persist across executions within the same session
- Custom console object captures output and redirects to response
- 5-second timeout prevents infinite loops per execution
- Errors are caught and returned as structured JSON
- Each session has its own isolated global scope

## Development

### Local Development Setup
```bash
# Install dependencies
npm install

# Run development server with auto-reload
npm run dev

# Run production server
npm start
```

### Code Quality
```bash
# Install dependencies (includes dev dependencies)
npm install

# Start development with hot reload
npm run dev
```

## Docker

```bash
# Build image
docker build -t webrepl-backend-javascript .

# Run container
docker run -p 8000:8000 webrepl-backend-javascript

# Run tests in container
docker exec webrepl-backend-javascript node test_api.js
```

## Configuration

- **CORS**: Environment-based configuration
  - Development (`ENVIRONMENT=development`): Allows all origins
  - Production: Restricted to specific frontend origins
- **Port**: 8000 (internal container port)
- **Host**: 0.0.0.0 (binds to all interfaces)
- **Session Storage**: In-memory Map with session ID keys

## Code Execution Flow

1. Receive POST request with JavaScript code and session ID
2. Get or create session-specific VM context
3. Set up custom console object for output capture
4. Execute code in session VM context with 5-second timeout
5. Capture console output and any exceptions
6. Return structured response with output/error
7. Preserve context variables for subsequent executions

## Session Management Implementation

The JavaScript backend integrates with the centralized session-manager service for persistent session storage:

```javascript
// Get session context from session manager with deserialization
async function getSessionContext(sessionId) {
    try {
        const response = await axios.get(`${SESSION_MANAGER_URL}/sessions/${sessionId}/environment`)
        if (response.status === 200 && response.data.environment?.serialized_data) {
            return deserializeContext(response.data.environment.serialized_data)
        }
        return createFreshContext()
    } catch (error) {
        return createFreshContext()
    }
}

// Save session context to session manager with serialization
async function saveSessionContext(sessionId, vmContext) {
    try {
        const serializedData = serializeContext(vmContext)
        await axios.put(`${SESSION_MANAGER_URL}/sessions/${sessionId}/environment`, {
            language: 'javascript',
            serialized_data: serializedData
        })
    } catch (error) {
        console.warn('Failed to save session environment:', error)
    }
}
```

**Key Features**:
- **Persistent Storage**: Session data survives backend restarts via SQLite database
- **Serialization**: Variables and functions are serialized/deserialized for persistence
- **Variable Transformation**: `const`/`let` automatically transformed to `var` for VM context compatibility
- **Function Restoration**: Functions are restored from source code with proper context binding

## Error Handling

- **Syntax Errors**: JavaScript parsing errors caught and returned
- **Runtime Errors**: Exceptions during execution caught and formatted
- **Timeout Errors**: Long-running code terminated after 5 seconds
- **Empty Code**: Returns HTTP 400 with appropriate error message
- **Console Output**: Both `console.log()` and `console.error()` outputs are captured and included in response
- **Promise Handling**: Promises are automatically awaited and resolved values are returned instead of `[object Promise]`

## Security

- Code executes in isolated VM context with limited scope
- 5-second timeout prevents infinite loops and resource exhaustion
- No filesystem or network access from executed code
- Session isolation prevents cross-session data access
- CORS configured for frontend domain only in production

## Testing

The JavaScript backend includes a comprehensive test suite using containerized testing with session-manager integration.

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
- `tests/docker-compose.yml`: Orchestrates session-manager + javascript-backend + test runner containers
- `tests/test.py`: Pytest-based test suite with comprehensive endpoint coverage
- `tests/Dockerfile`: Python test runner container with pytest and requests
- `tests/requirements.txt`: Python dependencies (pytest + requests)
- Health checks ensure both session-manager and backend are ready before running tests

**Test Coverage**:
- Health endpoint validation
- Variable persistence across executions (`const`/`let` transformed to `var`)
- Function persistence and serialization/deserialization
- Session isolation between different session IDs
- Error handling (syntax errors, runtime errors, validation)
- ES6+ features (arrow functions, destructuring, classes, template literals)
- Promise resolution and async handling
- JSON operations and console output capture
- Expression evaluation and session reset functionality

#### Manual Testing
```bash
# Health check
curl http://localhost:8000/health

# Execute code (requires valid session)
curl -X POST http://localhost:8000/execute/session-uuid \
  -H "Content-Type: application/json" \
  -d '{"code": "const x = 42; console.log(x);"}'

# Reset session
curl -X POST http://localhost:8000/reset/session-uuid
```

**Note**: Manual testing requires a valid session created through the session-manager service.

## JavaScript Capabilities

The REPL supports full JavaScript ES2020+ features:
- **Variables**: `let`, `const`, `var` with proper scoping
- **Functions**: Regular functions, arrow functions, async/await
- **Objects**: Object literals, destructuring, spread operator
- **Arrays**: All array methods, array destructuring
- **Classes**: ES6 classes with inheritance
- **Modules**: Limited support (no import/export due to VM context)
- **Built-ins**: All JavaScript built-in objects and methods

## Performance Considerations

- VM context creation is expensive, so contexts are reused per session
- Session cleanup happens automatically on container restart
- Memory usage grows with number of active sessions
- Consider implementing session cleanup for production deployments

## File Structure

```
backend/javascript/
├── server.js           # Main Express.js application with session integration
├── errorHandler.js     # Standardized error handling and HTTP status codes
├── sessionManager.js   # Session management utilities (legacy)
├── package.json        # Node.js dependencies and scripts
├── Dockerfile          # Container configuration
├── .dockerignore       # Build exclusions
├── test.sh             # Test runner script for containerized testing
├── tests/              # Comprehensive test suite
│   ├── docker-compose.yml  # Test orchestration with session-manager
│   ├── Dockerfile      # Python test runner container
│   ├── requirements.txt     # Python test dependencies
│   └── test.py         # Pytest test suite (22 test cases)
└── CLAUDE.md           # This documentation
```