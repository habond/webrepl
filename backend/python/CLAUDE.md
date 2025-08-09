# Backend - FastAPI Python REPL v2.0

FastAPI server that executes Python code in session-based sandboxed environments with persistent namespaces.

## Stack

- **Framework**: FastAPI 0.115.7
- **Runtime**: Python 3.11
- **Server**: Uvicorn
- **Container**: Python 3.11-slim base image (`webrepl-backend-python`)
- **Session Management**: Session-based persistent namespaces

## API Endpoints

### `POST /execute/{sessionId}`
Execute Python code in session-specific persistent namespace.

**Request:**
```json
{
  "code": "x = 42\nprint(f'x = {x}')"
}
```

**Response:**
```json
{
  "output": "x = 42\n",
  "error": null
}
```

### `POST /reset/{sessionId}`
Clear session-specific execution namespace.

**Response:**
```json
{
  "message": "Namespace reset successfully",
  "sessionId": "uuid"
}
```

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "language": "python",
  "version": "2.0.0",
  "stateless": false,
  "timestamp": "2025-01-01T00:00:00Z"
}
```

## Session Architecture

### Persistent Namespaces
- Each session ID maintains its own isolated execution namespace
- Variables, imports, and function definitions persist between executions
- Sessions are completely isolated from each other
- Namespace persists until session is reset or container restart

### Session Isolation Example
```python
# Session A
x = 10
def greet(name):
    return f"Hello, {name}!"

# Session B (completely separate)
x = 20  # Different from Session A's x
y = 30  # Session A cannot see this variable
```

## Security

- Code execution is isolated within the container
- No file system access outside container  
- No network access from executed code
- Each session uses its own isolated namespace
- Session namespaces prevent cross-session variable access

## Development

### Local Development Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run development server
make dev
# or
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
python test_api.py
```

### Code Quality
```bash
# Run all checks (lint + type-check)
make check

# Auto-format code
make format

# Lint code
make lint
# or
ruff check .
black --check .

# Type checking
make type-check  
# or
mypy .
```

## Configuration

- **CORS**: Environment-based configuration
  - Development (`ENVIRONMENT=development`): Allows all origins
  - Production: Restricted to specific frontend origins
- **Port**: 8000 (internal container port)
- **Host**: 0.0.0.0 (binds to all interfaces)
- **Session Storage**: In-memory dictionary with session ID keys

## Code Execution Flow

1. Receive POST request with Python code and session ID
2. Get or create session-specific namespace dictionary
3. Create isolated StringIO buffers for stdout/stderr
4. Execute code in session namespace using `exec(code, session_namespace)`
5. Capture output and any exceptions
6. Update session namespace with new variables/functions
7. Return structured response with output/error

## Session Management Implementation

```python
# Session namespaces stored in memory
session_namespaces = {}

def get_session_namespace(session_id: str) -> dict:
    """Get or create namespace for session."""
    if session_id not in session_namespaces:
        session_namespaces[session_id] = {"__builtins__": __builtins__}
    return session_namespaces[session_id]

def reset_session_namespace(session_id: str):
    """Reset session namespace to clean state."""
    session_namespaces[session_id] = {"__builtins__": __builtins__}
```

## Error Handling

- **Parse Errors**: Python syntax errors caught and returned in `error` field
- **Runtime Errors**: Exceptions during execution caught and returned
- **Import Errors**: Module import failures handled gracefully
- **Empty Code**: Returns HTTP 400 with appropriate error message

## Testing

The test suite (`test_api.py`) verifies:
- Health check endpoint functionality
- Basic expression evaluation
- Print statement output capture  
- Variable persistence between executions within same session
- Session isolation (different sessions don't share variables)
- Error handling for syntax and runtime errors
- Multi-line code execution
- Namespace reset functionality
- Import statement persistence

```bash
# Run tests locally
python test_api.py

# Run tests in Docker container
docker exec webrepl-backend-python python test_api.py
```

## Development Commands

Available Makefile targets:
- `make dev` - Start development server with auto-reload
- `make check` - Run all code quality checks
- `make format` - Auto-format code with black and ruff
- `make lint` - Check code style and linting
- `make type-check` - Run mypy type checking