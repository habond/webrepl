# Backend - Multi-Language REPL Servers v2.1

Collection of language-specific REPL backend implementations with centralized session management and real-time streaming capabilities.

## Architecture v2.0

The backend architecture consists of:
- **Session Manager**: Centralized SQLite-based session persistence (`backend/session-manager/`)
- **Language Backends**: Independent containerized execution environments
- **Session Isolation**: Each session maintains separate execution environments across all languages

### Session-Based API Interface
All backends implement session-aware REST endpoints:
- `POST /execute/{sessionId}` - Execute code in session-specific context
- `POST /execute-stream/{sessionId}` - Execute code with real-time streaming (Python, Bash)
- `POST /reset/{sessionId}` - Clear execution state for specific session
- `GET /health` - Health check endpoint

### Common Response Format
```json
{
  "output": "execution output",
  "error": "error message or null"
}
```

### Session Management Endpoints
The session manager provides:
- `GET /sessions` - List all active sessions with metadata
- `POST /sessions` - Create new session
- `DELETE /sessions/{sessionId}` - Delete session and cleanup
- `PUT /sessions/{sessionId}/rename` - Rename session

## Available Languages

### Python (`/backend/python/`)
- **Framework**: FastAPI with uvicorn
- **Features**: Session-based persistent namespaces using `exec(code, session_namespace)`
- **Streaming**: Server-Sent Events (SSE) with threading-based real-time output
- **Port**: 8000 (container internal)
- **Container**: `webrepl-backend-python`
- **Documentation**: `backend/python/CLAUDE.md`

### JavaScript (`/backend/javascript/`)
- **Framework**: Express.js with Node.js VM
- **Features**: Session-based persistent contexts with timeout protection
- **Port**: 8000 (container internal)
- **Container**: `webrepl-backend-javascript`
- **Documentation**: `backend/javascript/CLAUDE.md`

### Ruby (`/backend/ruby/`)
- **Framework**: Sinatra with safe eval
- **Features**: Session-based persistent bindings
- **Port**: 8000 (container internal)
- **Container**: `webrepl-backend-ruby`
- **Documentation**: `backend/ruby/CLAUDE.md`

### PHP (`/backend/php/`)
- **Framework**: PHP built-in server with eval
- **Features**: Session-based persistent variable context
- **Port**: 8000 (container internal)
- **Container**: `webrepl-backend-php`
- **Documentation**: `backend/php/CLAUDE.md`

### Kotlin (`/backend/kotlin/`)
- **Framework**: Ktor server with Kotlin Script Engine (JSR-223)
- **Features**: Session-based persistent variable bindings using serialized contexts
- **Port**: 8000 (container internal)
- **Container**: `webrepl-backend-kotlin`
- **Documentation**: `backend/kotlin/CLAUDE.md`

### Haskell (`/backend/haskell/`)
- **Framework**: Scotty web framework with Haskell Interpreter (hint)
- **Features**: Session-based code execution with GHC runtime evaluation
- **Port**: 8000 (container internal)
- **Container**: `webrepl-backend-haskell`
- **Documentation**: `backend/haskell/CLAUDE.md`

### Bash (`/backend/bash/`)
- **Framework**: FastAPI with subprocess execution
- **Features**: Session-based isolated working directories, 30-second timeout protection
- **Port**: 8000 (container internal)
- **Container**: `webrepl-backend-bash`
- **Documentation**: `backend/bash/CLAUDE.md`

### Perl (`/backend/perl/`)
- **Framework**: FastAPI with subprocess execution
- **Features**: Session-based persistent execution environments with history file accumulation, 30-second timeout protection
- **Port**: 8000 (container internal)
- **Container**: `webrepl-backend-perl`
- **Documentation**: `backend/perl/CLAUDE.md`

## Session Architecture

### Session Isolation
- Each session ID creates completely isolated execution environments
- Variables, imports, and state are isolated between different session IDs
- Sessions persist until explicitly deleted or container restart

### Session Metadata
Sessions track:
- `created_at`: Session creation timestamp
- `last_accessed`: Last execution or access time
- `execution_count`: Number of code executions in session
- `session_name`: Optional user-assigned name

### API Communication Flow
```
Frontend → nginx proxy (/api/{language}/*) → Language-specific backend container (port 8000)
```

**Session-Based Routes**:
- `/api/python/execute/{sessionId}` → `backend-python:8000/execute/{sessionId}`
- `/api/python/execute-stream/{sessionId}` → `backend-python:8000/execute-stream/{sessionId}` (SSE streaming)
- `/api/javascript/execute/{sessionId}` → `backend-javascript:8000/execute/{sessionId}`
- `/api/ruby/execute/{sessionId}` → `backend-ruby:8000/execute/{sessionId}`
- `/api/php/execute/{sessionId}` → `backend-php:8000/execute/{sessionId}`
- `/api/kotlin/execute/{sessionId}` → `backend-kotlin:8000/execute/{sessionId}`
- `/api/haskell/execute/{sessionId}` → `backend-haskell:8000/execute/{sessionId}`
- `/api/perl/execute/{sessionId}` → `backend-perl:8000/execute/{sessionId}`
- `/api/bash/execute/{sessionId}` → `backend-bash:8000/execute/{sessionId}`
- `/api/{language}/reset/{sessionId}` → `backend-{language}:8000/reset/{sessionId}`
- `/api/sessions/*` → `session-manager:8000/sessions/*` (session management endpoints)

## Adding New Languages

When adding a new language backend:

1. Create `backend/{language}/` directory
2. Implement session-aware API endpoints (`/execute/{sessionId}`, `/reset/{sessionId}`, `/health`)
3. Use the common response format
4. Add session isolation logic
5. Add Docker configuration with container name `webrepl-backend-{language}`
6. Update `docker-compose.yml` with new service
7. Update nginx proxy configuration for new language routes
8. Document in language-specific CLAUDE.md

## Testing

### Automated Test Suite Runner

**Run all backend tests**:
```bash
cd backend
./test.sh
```

The backend test suite runner:
- Automatically discovers backends with test suites
- Runs all available backend tests in parallel
- Provides colored output with detailed results summary
- Reports passed/failed/skipped backends with proper exit codes

**Current backends with test suites**:
- **bash**: 15 comprehensive test cases with session isolation and streaming
- **javascript**: 22 comprehensive test cases with session persistence and ES6 features

### Individual Backend Testing

Backends with test suites can be tested individually:

```bash
# Test specific backend
cd backend/bash && ./test.sh
cd backend/javascript && ./test.sh
```

### Manual Testing

Backends can also be tested by accessing their health endpoints and executing sample code through the API.

## Development

### Backend-Only Development
For backend development without the frontend:

```bash
cd backend
docker-compose up --build
```

This starts all language backends and the session manager service.

### Individual Backend Development
Each language backend is independently developed and containerized. See individual language directories for specific development instructions.

### Container Architecture
- **Network**: Bridge network `webrepl-network` for inter-container communication
- **Session Manager**: SQLite database for session persistence
- **Language Backends**: Independent containers with session-aware APIs
- **Orchestration**: Two docker-compose files - main project and backend-only for development