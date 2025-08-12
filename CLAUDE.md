# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Multi-Language Web REPL v2.0

A containerized web-based REPL with React frontend supporting multiple programming languages. Features a terminal-like interface for executing stateful code in Python, JavaScript, Ruby, PHP, Kotlin, Haskell, Perl, and Bash with advanced session management, automatic cleanup, structured logging, and comprehensive development tooling.

## Core Architecture

### Multi-Language Backend Architecture
Each supported language runs as a separate containerized backend:

**Python Backend** (`backend/python/`):
- FastAPI with session-based persistent namespaces using `exec(code, session_namespace)`
- Variables and imports persist between requests within each session
- Container: `webrepl-backend-python` on port 8000

**JavaScript Backend** (`backend/javascript/`):
- Express.js with Node.js VM for sandboxed execution
- Session-based persistent contexts with timeout protection  
- Container: `webrepl-backend-javascript` on port 8000

**Ruby Backend** (`backend/ruby/`):
- Sinatra with safe eval execution
- Session-based persistent bindings between requests
- Container: `webrepl-backend-ruby` on port 8000

**PHP Backend** (`backend/php/`):
- PHP built-in server with eval execution
- Session-based persistent variable context
- Container: `webrepl-backend-php` on port 8000

**Kotlin Backend** (`backend/kotlin/`):
- Ktor server with Kotlin Script Engine (JSR-223) for safe evaluation
- Session-based persistent variable bindings using serialized contexts
- Container: `webrepl-backend-kotlin` on port 8000

**Haskell Backend** (`backend/haskell/`):
- Scotty web framework with Haskell Interpreter (hint) for safe evaluation
- Session-based code execution with GHC runtime
- Container: `webrepl-backend-haskell` on port 8000

**Bash Backend** (`backend/bash/`):
- FastAPI server with subprocess execution for shell commands
- Session-based isolated working directories at `/tmp/bash_sessions/{sessionId}`
- 30-second timeout protection and full stdout/stderr capture
- Container: `webrepl-backend-bash` on port 8000

**Perl Backend** (`backend/perl/`):
- FastAPI server with subprocess execution for Perl scripts
- Session-based persistent execution environments with history file accumulation
- 30-second timeout protection and session-isolated working directories
- Container: `webrepl-backend-perl` on port 8000

**Session Manager** (`backend/session-manager/`):
- FastAPI service with SQLite database for session persistence
- Centralized session CRUD operations and metadata management
- Terminal history and environment state serialization
- Container: `webrepl-session-manager` on port 8000

**Session Management**: Each user session has its own GUID-based execution environment with automatic cleanup and monitoring. Sessions are completely isolated from each other with metadata tracking (execution count, creation time, last access). Session data persists in SQLite database with terminal history.

### Terminal-Style Frontend
The React frontend (`App.tsx`) implements a terminal interface using:
- `TerminalEntry` interface with `type: 'input' | 'output' | 'error'`
- Chronological history display (not separate input/output sections)
- Auto-focus input field with Enter key execution
- Real-time scroll-to-bottom behavior
- URL-based session routing: Each session gets a unique UUID in the URL path (e.g., `/<uuid>`)
- **Required Session Creation**: Terminal is disabled until user creates a session and selects a language

### User Flow v2.1

The application now enforces intentional session creation before allowing code execution:

1. **Initial State**: When no sessions exist, the terminal is hidden/disabled and shows a "No Active Session" message
2. **Session Creation**: User must click either:
   - The "+" button in the session sidebar header, or
   - The "Create your first session" button when no sessions exist
3. **Language Selection**: A single language selection menu appears with options for Python, JavaScript, Ruby, PHP, Kotlin, Haskell, Perl, or Bash
4. **Session Activation**: After selecting a language, a new session is created and the terminal becomes available
5. **Code Execution**: User can now execute code in their chosen language environment
6. **Session Persistence**: All variables, imports, and execution state persist within the session until explicitly deleted

**Key UX Improvements**:
- **No Default Sessions**: Eliminates automatic "Default Session" creation
- **Intentional Language Choice**: Forces users to consciously choose their programming environment
- **Clear Visual Feedback**: Disabled terminal clearly indicates that session creation is required
- **Single Menu System**: Unified language selection eliminates duplicate menu confusion

### Keyboard Shortcuts

The application supports keyboard shortcuts for rapid session switching:

**Mac:**
- `⌘⌥1` through `⌘⌥9` - Switch directly to session 1-9
- `⌘⌥[` - Switch to previous session
- `⌘⌥]` - Switch to next session

**Windows/Linux:**
- `Ctrl+Alt+1` through `Ctrl+Alt+9` - Switch directly to session 1-9
- `Ctrl+Alt+[` - Switch to previous session
- `Ctrl+Alt+]` - Switch to next session

**Features:**
- Hotkeys work even when the terminal input is focused
- Visual hints show hotkey combinations next to session names
- Keyboard shortcuts reference panel at bottom of session sidebar
- Input field automatically refocuses after switching sessions

### API Communication Flow
```
Frontend → nginx proxy (/api/{language}/*) → Language-specific backend container (port 8000)
```

**Session-Based API Routes**:
- `/api/python/execute/{sessionId}` → `backend-python:8000/execute/{sessionId}`
- `/api/javascript/execute/{sessionId}` → `backend-javascript:8000/execute/{sessionId}`
- `/api/ruby/execute/{sessionId}` → `backend-ruby:8000/execute/{sessionId}`
- `/api/php/execute/{sessionId}` → `backend-php:8000/execute/{sessionId}`
- `/api/kotlin/execute/{sessionId}` → `backend-kotlin:8000/execute/{sessionId}`
- `/api/haskell/execute/{sessionId}` → `backend-haskell:8000/execute/{sessionId}`
- `/api/perl/execute/{sessionId}` → `backend-perl:8000/execute/{sessionId}`
- `/api/bash/execute/{sessionId}` → `backend-bash:8000/execute/{sessionId}`
- `/api/{language}/reset/{sessionId}` → `backend-{language}:8000/reset/{sessionId}`
- `/api/sessions/*` → `session-manager:8000/*` (session management endpoints)

nginx uses regex patterns to capture and forward the full path including session ID to the backends.

### Container Architecture
- **Frontend**: nginx:alpine serving static React build + language-specific API proxy
- **Session Manager**: FastAPI service with SQLite database for session persistence (`webrepl-session-manager`)
- **Python Backend**: Python 3.11-slim with FastAPI (`webrepl-backend-python`)
- **JavaScript Backend**: Node.js 20-alpine with Express (`webrepl-backend-javascript`)
- **Ruby Backend**: Ruby 3.1-slim with Sinatra (`webrepl-backend-ruby`)
- **PHP Backend**: PHP 8.2-cli with built-in server (`webrepl-backend-php`)
- **Kotlin Backend**: OpenJDK 17 with Ktor server (`webrepl-backend-kotlin`)
- **Haskell Backend**: Haskell 9.4 with Scotty server (`webrepl-backend-haskell`)
- **Perl Backend**: Python 3.11-slim with FastAPI (`webrepl-backend-perl`)
- **Bash Backend**: Python 3.11-slim with FastAPI (`webrepl-backend-bash`)
- **Network**: Bridge network `webrepl-network` for inter-container communication
- **Persistence**: Session metadata and terminal history stored in SQLite. Language execution environments persist in backend memory until restart.
- **Orchestration**: Two docker-compose files - main project and backend-only for testing

## Testing

Backends can be tested by accessing their health endpoints and executing sample code through the API.

## Quick Start (Docker)

The easiest way to run the application is using the control script:

```bash
# Start the application
./control.sh start

# Stop the application
./control.sh stop

# Restart the application (rebuild and restart)
./control.sh restart

# Show container status
./control.sh status

# View logs (use -f to follow)
./control.sh logs -f

# Show help
./control.sh help
```

Access at: http://localhost:8080

## Environment Variables Configuration

The application supports comprehensive environment variable configuration for flexible deployment across different environments. All settings are configured via the `.env` file in the project root.

### Available Environment Variables

**Core Application Settings:**
```bash
# Application ports
FRONTEND_PORT=8080              # Frontend nginx port
BACKEND_PORT=8000               # All backend services port
VITE_DEV_PORT=5173             # Vite development server port

# Environment and CORS
ENVIRONMENT=development         # development|production
CORS_ORIGINS=http://localhost:8080  # Comma-separated CORS origins
```

**Service Communication URLs:**
```bash
# Session Manager
SESSION_MANAGER_URL=http://session-manager:8000

# Language Backend URLs
PYTHON_BACKEND_URL=http://backend-python:8000
JAVASCRIPT_BACKEND_URL=http://backend-javascript:8000
RUBY_BACKEND_URL=http://backend-ruby:8000
PHP_BACKEND_URL=http://backend-php:8000
KOTLIN_BACKEND_URL=http://backend-kotlin:8000
HASKELL_BACKEND_URL=http://backend-haskell:8000
```

**Container Hostnames:**
```bash
# Used by nginx proxy configuration
SESSION_MANAGER_HOST=session-manager
PYTHON_BACKEND_HOST=backend-python
JAVASCRIPT_BACKEND_HOST=backend-javascript
RUBY_BACKEND_HOST=backend-ruby
PHP_BACKEND_HOST=backend-php
KOTLIN_BACKEND_HOST=backend-kotlin
HASKELL_BACKEND_HOST=backend-haskell
```

**Frontend Configuration (Vite):**
```bash
# Frontend-specific variables (prefixed with VITE_)
VITE_SESSION_REFRESH_INTERVAL=30000  # Session refresh interval in milliseconds
VITE_BACKEND_PORT=8000               # Backend port for display purposes
```

**Database Configuration:**
```bash
DATABASE_PATH=./data/sessions.db     # SQLite database file path
```

### Environment Variable Usage

**Development Mode:**
- `ENVIRONMENT=development` enables CORS for all origins (`["*"]`)
- Detailed logging and error reporting
- Hot reloading for frontend development

**Production Mode:**
- `ENVIRONMENT=production` restricts CORS to specified origins
- Optimized builds and reduced logging
- Security hardening enabled

### Customizing Deployment

To customize the application for your environment, modify the `.env` file:

```bash
# Example: Production deployment on different ports
FRONTEND_PORT=3000
BACKEND_PORT=9000
ENVIRONMENT=production
CORS_ORIGINS=https://myapp.com,https://www.myapp.com

# Example: Point to external services
SESSION_MANAGER_URL=http://external-session-manager:9000
DATABASE_PATH=/mnt/data/sessions.db
```

**Docker Compose Integration:**
Environment variables are automatically passed to all containers with sensible defaults. No code changes required - just update the `.env` file and restart:

```bash
./control.sh restart
```

### Alternative Docker Commands

You can also use Docker Compose directly if needed:

- View logs: `docker-compose logs -f` (or `./control.sh logs -f`)
- Restart services: `docker-compose restart`
- Rebuild and start: `docker-compose up --build` (or `./control.sh restart`)
- Stop services: `docker-compose down` (or `./control.sh stop`)

## Project Structure

```
webrepl/
├── frontend/           # React terminal interface
├── backend/           # Multi-language REPL backends
│   ├── session-manager/ # Centralized session management service
│   ├── python/        # Python FastAPI backend
│   ├── javascript/    # Node.js Express backend  
│   ├── ruby/         # Ruby Sinatra backend
│   ├── php/          # PHP built-in server backend
│   ├── kotlin/       # Kotlin Ktor server backend
│   ├── haskell/      # Haskell Scotty server backend
│   └── docker-compose.yml # Backend-only orchestration
├── docker-compose.yml # Main project orchestration
└── control.sh        # Application control script (start/stop/restart/status/logs)
```

## Local Development Setup (Alternative to Docker)

**Note**: Docker is the recommended development approach. Use local setup only if you need to debug or develop without containers.

### Backend (Python)

```bash
cd backend/python
# Create virtual environment for local development
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Running Locally (without Docker)

### Start the Backend (Python)

```bash
cd backend/python
source venv/bin/activate  # On Windows: venv\Scripts\activate
make dev
# or
uvicorn main:app --host 0.0.0.0 --port 8000
```

Backend available at: http://localhost:8000

### Start the Frontend

```bash
cd frontend
npm run dev
```

Frontend available at: http://localhost:5173

## Development Commands

### Production (Docker)
```bash
# Application control
./control.sh start     # Start entire stack
./control.sh restart   # Restart entire stack (rebuild and restart)
./control.sh stop      # Stop entire stack
./control.sh status    # Show container status
./control.sh logs -f   # View logs (follow)

# Manual Docker operations
docker compose up --build -d backend   # Rebuild specific service
docker compose up --build -d frontend
docker compose logs -f [backend|frontend]  # View logs for specific service
```


### Backend Development (FastAPI)
```bash
cd backend/python

# For local development only (not needed for Docker)
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Development server
make dev  # or: uvicorn main:app --host 0.0.0.0 --port 8000

# Code quality
make check    # Run all checks (lint + type-check)
make format   # Format with black + ruff
make lint     # Check with ruff + black
make type-check  # Check with mypy
```

### Frontend Development (React + TypeScript)
```bash
cd frontend
npm install

# Development
npm run dev          # Vite dev server (http://localhost:5173)
npm run build        # Production build
npm run preview      # Preview production build

# Code quality  
npm run lint         # ESLint check (includes formatting)
npm run lint:fix     # ESLint autofix (includes formatting)
tsc                  # TypeScript check
```

## API Endpoints

### `POST /api/{language}/execute/{sessionId}`
Execute code in the specified language backend for the given session.
**Request**: `{"code": "print('hello')"}`
**Response**: `{"output": "hello\n", "error": null}`

### `POST /api/{language}/reset/{sessionId}`  
Clear the execution state for the specified language and session.
**Response**: `{"message": "Namespace reset successfully"}`

**Parameters**:
- `{language}`: One of `python`, `javascript`, `ruby`, `php`, `kotlin`, `haskell`, `perl`, `bash`
- `{sessionId}`: UUID string identifying the user session

**Session Isolation**: Each session maintains completely separate execution environments. Variables, imports, and state are isolated between different session IDs.

### Session Management Endpoints

### `GET /api/sessions`
List all active sessions and their metadata.
**Response**: 
```json
{
  "sessions": [
    {
      "id": "uuid-1",
      "name": "My Session",
      "language": "python",
      "created_at": "2025-08-08T22:00:00Z",
      "last_accessed": "2025-08-08T22:30:00Z", 
      "execution_count": 15,
      "history": []
    }
  ]
}
```

### `POST /api/sessions`
Create a new session.
**Request**: `{"name": "My Session", "language": "python"}`
**Response**: `{"id": "uuid", "name": "My Session", "language": "python", ...}`

### `DELETE /api/sessions/{sessionId}`
Delete a specific session and its data.
**Response**: `{"message": "Session deleted successfully"}`

### `PUT /api/sessions/{sessionId}/rename`
Rename a session.
**Request**: `{"name": "New Session Name"}`
**Response**: `{"message": "Session renamed successfully"}`

## Key Implementation Details

### Architecture v2.0 Improvements
- **Session Management**: Centralized session handling with automatic cleanup and metadata tracking
- **Error Handling**: Standardized error responses across all backends with proper HTTP status codes
- **Development Experience**: Hot reloading, structured logging, and comprehensive development tooling
- **Type Safety**: Enhanced TypeScript configurations and strict error handling
- **Monitoring**: Built-in session statistics and performance metrics

### Configuration Approach
- **Environment Variables**: Comprehensive `.env` file configuration for all application settings
- **TypeScript**: Single consolidated `tsconfig.json` (no project references)
- **Code Quality**: ESLint handles all formatting and linting (no separate Prettier)
- **CORS**: Environment-based configuration for flexible development (`ENVIRONMENT` and `CORS_ORIGINS` variables)
- **Build Optimization**: Comprehensive `.dockerignore` files for faster builds
- **Logging**: Structured logging with configurable levels and context tracking
- **Container Configuration**: All services respect environment variables with sensible defaults

### CORS Configuration
Backend uses environment-based CORS configuration:
- **Development**: `ENVIRONMENT=development` (default) → allows all origins (`["*"]`)
- **Production**: `ENVIRONMENT=production` → restricts to origins specified in `CORS_ORIGINS`
- **Flexible Origins**: `CORS_ORIGINS` supports comma-separated list of allowed origins
- Set via environment variables, no code changes needed for different deployment environments

### Error Handling
- Frontend network errors → "Failed to connect to server"
- Python execution errors → Full traceback in `error` field
- Empty code → HTTP 400 "Code cannot be empty"

### Terminal Styling
CSS uses classic terminal colors (black background, green text `#00ff00`) with monospace fonts. Terminal lines are categorized by type (`input`, `output`, `error`) for styling.

### nginx Proxy Configuration
Critical: nginx config at `frontend/nginx.conf` routes `/api/{language}/` to `backend-{language}:8000/` (note trailing slashes). This strips the `/api/{language}` prefix before forwarding to the respective backend.

### Build Optimizations
- Frontend/backend have optimized `.dockerignore` files
- Smaller build contexts and faster Docker builds
- TypeScript compilation simplified to single `tsc` command

## Security Considerations

This application executes arbitrary code (Python, JavaScript, Ruby, PHP, Kotlin, Haskell, Perl) in sandboxed container environments. Each backend container has no network access to external services and limited filesystem access. Never expose this to untrusted networks without additional security measures.

## Component-Specific Documentation

- Backend implementation details: `backend/CLAUDE.md`
- Python backend implementation details: `backend/python/CLAUDE.md`
- JavaScript backend implementation details: `backend/javascript/CLAUDE.md`
- Ruby backend implementation details: `backend/ruby/CLAUDE.md`
- PHP backend implementation details: `backend/php/CLAUDE.md`
- Kotlin backend implementation details: `backend/kotlin/CLAUDE.md`
- Haskell backend implementation details: `backend/haskell/CLAUDE.md`
- Perl backend implementation details: `backend/perl/CLAUDE.md`
- Bash backend implementation details: `backend/bash/CLAUDE.md`
- Frontend implementation details: `frontend/CLAUDE.md`

# Frontend Architecture Deep Dive

### React Component Architecture
The frontend uses a custom hook-based architecture centered around three core hooks:

**useSessionManager** (`frontend/src/hooks/useSessionManager.ts`):
- Manages all session CRUD operations via `/api/sessions` endpoints
- Handles session persistence, auto-refresh every 30s, and state synchronization
- Provides `createSession`, `deleteSession`, `renameSession`, `getSession` methods
- Critical: Sessions are NOT persisted in localStorage - they exist only in backend memory

**useTerminal** (`frontend/src/hooks/useTerminal.ts`):
- Manages terminal history, input state, and terminal UI behavior
- Maintains per-session terminal state with automatic cleanup via `cleanupSessionState()`
- Handles Enter key execution, auto-focus, and scroll-to-bottom behavior
- Terminal history is cached per session but cleared when sessions are deleted

**useCodeExecution** (`frontend/src/hooks/useCodeExecution.ts`):
- Handles code execution API calls to `/api/{language}/execute/{sessionId}`
- Manages execution loading states and error handling
- Integrates with terminal history via the `addEntry` callback

### Session Management Architecture
Sessions are managed through a dedicated session-manager service (`backend/session-manager/`):
- **Database**: SQLite-based session persistence with metadata tracking
- **API Routes**: Full CRUD operations (`GET /sessions`, `POST /sessions`, `DELETE /sessions/{id}`, `PUT /sessions/{id}/rename`)
- **Session Isolation**: Each session maintains separate execution environments across all language backends
- **Automatic Cleanup**: Sessions track last_accessed, execution_count, and creation timestamps

### Language Backend Integration
Each language backend exposes session-aware endpoints:
- **Session Persistence**: `/execute/{sessionId}` maintains isolated execution environments per session
- **Session Reset**: `/reset/{sessionId}` clears only the specific session's execution state
- **Health Checks**: `/health` endpoints for container orchestration monitoring

### Session Manager Integration
The session manager (`backend/session-manager/`) provides centralized session persistence:
- **SQLite Database**: Stores session metadata, terminal history, and environment state
- **Session CRUD**: Full create, read, update, delete operations for sessions
- **Terminal History**: Persistent terminal entry storage across browser sessions
- **Environment Serialization**: Backend execution environments can be serialized/deserialized via session manager

# Development Workflow Commands


## Code Quality Commands
```bash
# Frontend (React/TypeScript)
cd frontend
npm run lint                    # ESLint check (includes formatting rules)
npm run lint:fix               # Auto-fix linting issues
tsc                            # TypeScript compilation check

# Python Backend
cd backend/python
make check                     # Run all checks (lint + type-check)
make format                    # Auto-format with black + ruff
make lint                      # Check with ruff + black --check
make type-check               # mypy type checking

# JavaScript Backend  
cd backend/javascript
npm start                     # Start production server
```

## Testing Commands
Backends can be tested by accessing their health endpoints and executing sample code through the API.

# Critical Implementation Details

### Session State Management
- **Frontend**: Sessions are managed via `useSessionManager` hook with auto-refresh
- **Backend**: Session data persists in session-manager SQLite database
- **Isolation**: Each session ID creates completely isolated execution environments
- **Cleanup**: Deleting sessions triggers both backend cleanup and frontend state cleanup via `cleanupSessionState()`

### API Architecture Patterns
- **Session-First Design**: All execution endpoints require `{sessionId}` parameter
- **Language Routing**: nginx routes `/api/{language}/*` to `backend-{language}:8000/*`
- **Error Standardization**: All backends return consistent `{"output": "...", "error": "..."}` format
- **CORS Configuration**: Environment-based (`ENVIRONMENT=development` allows all origins)

### Terminal UI Implementation
- **Entry Types**: `TerminalEntry` supports `'input' | 'output' | 'error'` with distinct styling
- **Real-time Updates**: Terminal auto-scrolls and focuses input after code execution
- **Session Switching**: Changing sessions loads that session's terminal history
- **Conditional Rendering**: Terminal only displays when an active session exists
- **Session Requirement UI**: Shows "No Active Session" message with instructions when no session is active
- **Styling System**: CSS uses terminal color scheme (`#7dd3fc` blue, dark backgrounds) with hover effects

### Container Orchestration
- **Main Stack**: `docker-compose.yml` orchestrates frontend + all backends
- **Backend-Only**: `backend/docker-compose.yml` for backend development/testing
- **Networking**: `webrepl-network` bridge network connects all containers
- **Build Optimization**: Comprehensive `.dockerignore` files minimize build contexts