# Backend - Multi-Language REPL Servers v2.0

Collection of language-specific REPL backend implementations with centralized session management.

## Architecture v2.0

The backend architecture consists of:
- **Session Manager**: Centralized SQLite-based session persistence (`backend/session-manager/`)
- **Language Backends**: Independent containerized execution environments
- **Session Isolation**: Each session maintains separate execution environments across all languages

### Session-Based API Interface
All backends implement session-aware REST endpoints:
- `POST /execute/{sessionId}` - Execute code in session-specific context
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
- `/api/javascript/execute/{sessionId}` → `backend-javascript:8000/execute/{sessionId}`
- `/api/ruby/execute/{sessionId}` → `backend-ruby:8000/execute/{sessionId}`
- `/api/php/execute/{sessionId}` → `backend-php:8000/execute/{sessionId}`
- `/api/{language}/reset/{sessionId}` → `backend-{language}:8000/reset/{sessionId}`

## Adding New Languages

When adding a new language backend:

1. Create `backend/{language}/` directory
2. Implement session-aware API endpoints (`/execute/{sessionId}`, `/reset/{sessionId}`, `/health`)
3. Use the common response format
4. Add session isolation logic
5. Add Docker configuration with container name `webrepl-backend-{language}`
6. Update `docker-compose.yml` with new service
7. Update nginx proxy configuration for new language routes
8. Add comprehensive test suite
9. Document in language-specific CLAUDE.md

## Testing

Run the comprehensive test suite for all backends:

```bash
# Test all backends (auto-starts containers if needed)
backend/test.sh

# Test specific backend
backend/test.sh python
backend/test.sh javascript  
backend/test.sh ruby
backend/test.sh php

# Test with local backends (not Docker)
backend/test.sh --local

# Individual backend tests
docker exec webrepl-backend-python python test_api.py
docker exec webrepl-backend-javascript node test_api.js
docker exec webrepl-backend-ruby ruby test_api.rb
docker exec webrepl-backend-php php test_api.php
```

### Test Coverage
Each backend test suite verifies:
- Health check endpoint
- Simple expression evaluation
- Output capture (print/console.log/puts/echo)
- Variable persistence between executions within sessions
- Error handling and reporting
- Session reset functionality
- Multi-line code execution
- Session isolation (different sessions don't interfere)
- Language-specific features

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
- **Orchestration**: Two docker-compose files - main project and backend-only for testing