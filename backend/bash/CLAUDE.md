# Bash Backend - Shell Command Execution Service

FastAPI-based backend service providing session-isolated Bash command execution with timeout protection and comprehensive output capture.

## Architecture

### Technology Stack
- **Framework**: FastAPI with Uvicorn ASGI server
- **Language**: Python 3.11
- **Execution**: Python subprocess module for shell command execution
- **Container**: Python:3.11-slim base image

### Key Features
- **Session Isolation**: Each session gets its own working directory at `/tmp/bash_sessions/{sessionId}`
- **Real-time Streaming**: Server-Sent Events (SSE) for incremental output streaming
- **Timeout Protection**: 30-second timeout for all command executions
- **Output Capture**: Full stdout and stderr capture with proper error handling
- **Environment Persistence**: Session-specific environment variables
- **Temporary Script Execution**: Commands executed via temporary script files for proper bash handling

## API Endpoints

### `POST /execute/{session_id}`
Execute Bash commands in a session-specific environment (traditional request/response).

**Request Body**:
```json
{
  "code": "ls -la && pwd"
}
```

**Response**:
```json
{
  "output": "total 8\ndrwxr-xr-x 2 root root 4096...\n/tmp/bash_sessions/abc-123",
  "error": null
}
```

**Features**:
- Commands execute in session-specific working directory
- Supports pipes, redirects, and shell features
- Captures both stdout and stderr
- Returns non-zero exit codes in error field

### `POST /execute-stream/{session_id}` (Server-Sent Events)
Execute Bash commands with real-time streaming output via SSE.

**Request Body**:
```json
{
  "code": "for i in {1..3}; do echo \"Processing $i\"; sleep 1; done"
}
```

**Response**: SSE stream with incremental events
```
data: {"type": "output", "content": "Processing 1\n"}
data: {"type": "output", "content": "Processing 2\n"}
data: {"type": "output", "content": "Processing 3\n"}
data: {"type": "complete", "returnCode": 0}
```

**SSE Event Types**:
- `output`: Stdout content chunk
- `error`: Stderr content chunk  
- `complete`: Command completion with return code

**Features**:
- Real-time incremental output streaming
- Temporary script file execution for proper bash command handling
- Async subprocess execution with `asyncio.create_subprocess_exec`
- Session-isolated working directory execution
- Proper handling of bash loops, pipes, and complex commands

### `POST /reset/{session_id}`
Reset a session by clearing its working directory and removing from memory.

**Response**:
```json
{
  "message": "Session reset successfully"
}
```

### `GET /health`
Health check endpoint for container orchestration.

**Response**:
```json
{
  "status": "healthy",
  "service": "bash-backend"
}
```

### `GET /sessions`
List all active Bash sessions with metadata.

**Response**:
```json
{
  "sessions": [
    {
      "id": "session-uuid",
      "created_at": "2025-08-10T12:00:00Z",
      "last_accessed": "2025-08-10T12:05:00Z",
      "execution_count": 5,
      "working_directory": "/tmp/bash_sessions/session-uuid"
    }
  ]
}
```

## Session Management

### Session Structure
Each session maintains:
- **Working Directory**: Isolated filesystem space at `/tmp/bash_sessions/{sessionId}`
- **Environment Variables**: Copy of system environment for command execution
- **Metadata**: Creation time, last access, execution count
- **Isolation**: Complete separation between different sessions

### Working Directory
- Created automatically on first command execution
- Persists for session lifetime
- Files created in one command are available in subsequent commands
- Cleaned up on session reset

### Command Execution
**Traditional Execution (`/execute/{session_id}`)**:
- Each command runs via `subprocess.run()` with shell=True
- Working directory set to session-specific path
- Environment variables passed to subprocess
- 30-second timeout prevents hanging commands

**Streaming Execution (`/execute-stream/{session_id}`)**:
- Commands executed via temporary script files for proper bash handling
- Async subprocess execution with `asyncio.create_subprocess_exec`
- Real-time stdout/stderr streaming via Server-Sent Events
- Session-isolated working directory and environment
- Incremental output capture with proper buffering

## Security Considerations

### Limitations
- Commands execute with container user privileges (root in container)
- No network isolation between commands
- No resource limits beyond timeout
- Shell injection possible (by design for REPL functionality)

### Best Practices
- Container runs in isolated Docker environment
- No access to host filesystem
- Network isolated from other services
- Should not be exposed to untrusted users

## Implementation Details

### Error Handling
- Timeout errors return descriptive message
- Command failures include exit code
- stderr captured separately from stdout
- Exceptions logged with session context

### Performance
- Lightweight subprocess creation per command
- No persistent shell process
- Minimal memory footprint per session
- Quick command execution startup

### Logging
- Session creation/deletion logged
- Command execution count tracked
- Errors logged with full context
- Health checks not logged (reduce noise)

## Development

### Local Development
```bash
cd backend/bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Health check
curl http://localhost:8000/health

# Execute command (traditional)
curl -X POST http://localhost:8000/execute/test-session \
  -H "Content-Type: application/json" \
  -d '{"code": "echo Hello && ls -la"}'

# Execute command with streaming (SSE)
curl -X POST http://localhost:8000/execute-stream/test-session \
  -H "Content-Type: application/json" \
  -d '{"code": "for i in {1..3}; do echo Line $i; sleep 1; done"}' \
  -H "Accept: text/event-stream"

# Reset session
curl -X POST http://localhost:8000/reset/test-session
```

### Docker Build
```bash
docker build -t webrepl-backend-bash .
docker run -p 8000:8000 webrepl-backend-bash
```

## Configuration

### Environment Variables
- `ENVIRONMENT`: Set to "development" or "production" for CORS configuration
- `CORS_ORIGINS`: Comma-separated list of allowed origins
- `BACKEND_PORT`: Port to run the service (default: 8000)

### CORS Settings
- **Development**: Allows all origins (`*`)
- **Production**: Restricts to configured origins

## File Structure

```
backend/bash/
├── main.py           # FastAPI application and endpoints
├── requirements.txt  # Python dependencies
├── Dockerfile       # Container configuration
├── .dockerignore    # Build exclusions
└── CLAUDE.md        # This documentation
```

## Common Use Cases

### File Operations
```bash
# Create and read files
echo "Hello" > test.txt
cat test.txt

# Directory operations
mkdir mydir
cd mydir && pwd
```

### Environment Variables
```bash
# Set and use variables (within single command)
MY_VAR="Hello" && echo $MY_VAR

# Check environment
env | grep PATH
```

### Process Management
```bash
# List processes
ps aux

# System information
uname -a
whoami
```

### Network Operations
```bash
# Check connectivity (if tools available)
ping -c 1 google.com
curl https://api.example.com
```

## Server-Sent Events (SSE) Implementation

### Streaming Architecture
The SSE streaming implementation provides real-time output for long-running commands:

**Key Components**:
- `stream_command_output()`: Async generator function for SSE streaming
- `execute_stream_endpoint()`: FastAPI endpoint returning `StreamingResponse`
- Temporary script file execution for proper bash command handling
- Real-time stdout/stderr capture with incremental updates

### Implementation Details

**Temporary Script Execution**:
```python
# Create temporary script file in session working directory
script_fd, script_path = tempfile.mkstemp(suffix='.sh', dir=session["working_directory"])
with os.fdopen(script_fd, 'w') as script_file:
    script_file.write(f"#!/bin/bash\nset -e\n{code}")
os.chmod(script_path, 0o755)

# Execute script with asyncio subprocess
process = await asyncio.create_subprocess_exec(
    '/bin/bash', script_path,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
    cwd=session["working_directory"]
)
```

**SSE Event Generation**:
```python
async def stream_command_output(session_id: str, code: str):
    # Process stdout and stderr in real-time
    while True:
        stdout_line = await process.stdout.readline()
        if stdout_line:
            yield f"data: {json.dumps({'type': 'output', 'content': stdout_line.decode()})}\n\n"
            
        stderr_line = await process.stderr.readline()
        if stderr_line:
            yield f"data: {json.dumps({'type': 'error', 'content': stderr_line.decode()})}\n\n"
            
        if process.returncode is not None:
            yield f"data: {json.dumps({'type': 'complete', 'returnCode': process.returncode})}\n\n"
            break
```

**Benefits**:
- **Real-time Feedback**: Users see output as commands execute
- **Better UX**: No waiting for long-running commands to complete  
- **Proper Bash Handling**: Complex commands execute correctly via script files
- **Session Isolation**: Each stream maintains proper session context

## Limitations

1. **No Persistent Variables**: Variables don't persist between commands (use files for persistence)
2. **Single Command Execution**: Each request executes one shell command
3. **No Interactive Programs**: Cannot run interactive programs like vim or top
4. **Timeout Limit**: Commands must complete within 30 seconds
5. **No Background Jobs**: Background processes terminated after command completes

## Integration Notes

- Integrates with frontend via nginx proxy at `/api/bash/*`
- SSE streaming endpoint: `/api/bash/execute-stream/{sessionId}`
- Session IDs managed by frontend/session-manager
- Follows same API pattern as other language backends
- Frontend automatically detects streaming support via `supportsStreaming: true` configuration
- Container named `webrepl-backend-bash` in Docker network