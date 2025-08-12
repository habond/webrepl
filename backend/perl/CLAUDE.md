# Perl Backend - Session-Based REPL Server

FastAPI-based Perl execution backend with session-based persistent execution contexts.

## Architecture

The Perl backend implements a FastAPI server that executes Perl code through subprocess calls while maintaining session state through a file-based history accumulation system.

### Key Features

- **Session-Based Execution**: Each session maintains its own isolated environment
- **History File Accumulation**: Code execution is persisted by appending to session-specific history files
- **Subprocess Execution**: Uses Python's subprocess module to execute Perl scripts safely
- **30-Second Timeout Protection**: Prevents runaway scripts from consuming resources
- **Error Handling**: Comprehensive error capture with proper HTTP status codes

## Implementation Details

### Session Management

Each session is identified by a unique session ID and maintains:

- **Working Directory**: Isolated directory at `/tmp/perl_sessions/{sessionId}`
- **History File**: `history.pl` file that accumulates all executed code
- **Session Metadata**: Creation time, last accessed time, execution count

### Code Execution Flow

1. **Session Initialization**: 
   - Creates session directory if it doesn't exist
   - Initializes `history.pl` with strict mode and warnings: `use strict; use warnings;`
   - Updates session metadata

2. **Code Execution**:
   - Appends new code to the history file temporarily
   - Executes the entire history file with Perl interpreter
   - If successful, permanently appends code to history
   - Captures stdout/stderr output
   - Enforces 30-second timeout

3. **Session Reset**:
   - Clears the session directory
   - Removes all files including history
   - Recreates fresh session environment

### API Endpoints

#### `GET /health`
Health check endpoint returning server status and session count.

**Response**:
```json
{
  "status": "healthy",
  "language": "perl", 
  "sessions": 0
}
```

#### `POST /execute/{session_id}`
Execute Perl code in the specified session context.

**Request Body**:
```json
{
  "code": "print \"Hello World!\";"
}
```

**Response**:
```json
{
  "output": "Hello World!",
  "error": null
}
```

**Error Response**:
```json
{
  "output": "",
  "error": "Compilation error message"
}
```

#### `POST /reset/{session_id}`
Reset the session execution state.

**Response**:
```json
{
  "message": "Session reset successfully"
}
```

#### `GET /sessions`
List all active sessions with metadata.

**Response**:
```json
{
  "sessions": [
    {
      "id": "session-id",
      "created_at": "2025-08-12T00:00:00.000000",
      "last_accessed": "2025-08-12T00:05:00.000000", 
      "execution_count": 5
    }
  ]
}
```

## Session Persistence

### History File Format

The `history.pl` file maintains all executed code in chronological order:

```perl
#!/usr/bin/perl
use strict;
use warnings;

# Execution 1
print "Hello";

# Execution 2  
my $name = "World";
print $name;

# Execution 3
print "!";
```

### Variable Persistence

Perl variables persist across executions within the same session because the entire history file is re-executed each time. This allows:

- Global variables to maintain state
- Subroutine definitions to persist
- Module imports to remain available
- Complex data structures to be built incrementally

### Session Isolation

Each session operates in complete isolation:

- Separate working directories prevent file conflicts
- Session-specific history files ensure code isolation  
- Independent execution environments prevent variable leakage
- Isolated metadata tracking per session

## Error Handling

### Compilation Errors
Perl syntax errors are captured and returned in the `error` field without affecting session state.

### Runtime Errors
Runtime exceptions are captured and returned, but successful code is still appended to history.

### Timeout Protection
Long-running scripts are terminated after 30 seconds with appropriate error messages.

### Session Cleanup
Failed sessions are properly cleaned up to prevent resource leaks.

## Development

### Local Development

```bash
cd backend/perl

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing

```bash
# Health check
curl http://localhost:8000/health

# Execute code
curl -X POST http://localhost:8000/execute/test-session \
  -H "Content-Type: application/json" \
  -d '{"code": "print 42;"}'

# Reset session
curl -X POST http://localhost:8000/reset/test-session
```

### Docker Development

```bash
# Build container
docker build -t webrepl-backend-perl .

# Run container
docker run -p 8000:8000 webrepl-backend-perl

# Access container shell
docker exec -it <container-id> /bin/bash
```

## Configuration

### Environment Variables

- `ENVIRONMENT`: Set to "development" or "production"
- `BACKEND_PORT`: Server port (default: 8000)  
- `CORS_ORIGINS`: Comma-separated allowed origins
- `SESSION_MANAGER_URL`: URL to session manager service

### Logging

The backend uses Python's logging module with INFO level by default. Logs include:

- Session creation and deletion events
- Code execution attempts and results
- Error conditions and timeouts
- Health check requests

## Security Considerations

### Sandboxing
- Code execution is limited to the session's working directory
- No network access within the container environment
- 30-second execution timeout prevents resource abuse
- Subprocess isolation prevents system-level access

### Input Validation
- Request payloads are validated with Pydantic models
- Empty code submissions return HTTP 400 errors
- Session IDs are treated as opaque strings

### Error Information
- Perl error messages are sanitized before returning
- System paths are not exposed in error responses
- Internal server errors return generic messages

## Performance

### Execution Model
Each code execution re-runs the entire session history, which:
- Ensures consistent variable state
- Allows complex incremental development
- May impact performance for very long sessions
- Provides reliable execution semantics

### Optimization Opportunities
- Session cleanup for idle sessions
- History file size limits
- Execution result caching
- Memory usage monitoring

## Integration

### Session Manager Integration
The Perl backend integrates with the centralized session manager for:
- Session metadata persistence
- Cross-language session coordination
- Terminal history storage
- Session lifecycle management

### Frontend Integration
The React frontend communicates with the Perl backend through:
- nginx proxy routing (`/api/perl/*`)
- JSON request/response format
- WebSocket connections for real-time updates (future enhancement)
- Error state management