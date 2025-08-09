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

```javascript
// Session contexts stored in memory
const sessionContexts = new Map();

function getSessionContext(sessionId) {
    if (!sessionContexts.has(sessionId)) {
        const context = vm.createContext({
            console: createConsoleCapture(),
            // Other global objects...
        });
        sessionContexts.set(sessionId, context);
    }
    return sessionContexts.get(sessionId);
}

function resetSessionContext(sessionId) {
    const context = vm.createContext({
        console: createConsoleCapture(),
        // Reset to clean state...
    });
    sessionContexts.set(sessionId, context);
}
```

## Error Handling

- **Syntax Errors**: JavaScript parsing errors caught and returned
- **Runtime Errors**: Exceptions during execution caught and formatted
- **Timeout Errors**: Long-running code terminated after 5 seconds
- **Empty Code**: Returns HTTP 400 with appropriate error message

## Security

- Code executes in isolated VM context with limited scope
- 5-second timeout prevents infinite loops and resource exhaustion
- No filesystem or network access from executed code
- Session isolation prevents cross-session data access
- CORS configured for frontend domain only in production

## Testing

The backend can be tested by accessing the health endpoint and executing sample JavaScript code through the API.

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