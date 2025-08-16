# Session Manager - Centralized Session Management Service v2.0

FastAPI service providing centralized session management for multi-language REPL with SQLite database persistence.

## Stack

- **Framework**: FastAPI 0.115+ with uvicorn
- **Database**: SQLite with SQLAlchemy ORM
- **Runtime**: Python 3.11
- **Container**: Python 3.11-slim base image (`webrepl-session-manager`)
- **Persistence**: SQLite database with volume mount for data persistence

## Features

- **Centralized Session Management**: CRUD operations for all REPL sessions
- **SQLite Persistence**: Session metadata and terminal history stored in database
- **Terminal History**: Persistent terminal entry storage across browser sessions with update capabilities
- **Streaming Support**: History entry updates for real-time output streaming persistence
- **Session Isolation**: Complete isolation between different session contexts
- **Language Backend Integration**: Automatic cleanup coordination with language backends
- **Admin Interface**: Detailed session inspection for debugging and monitoring
- **Environment Serialization**: Support for serialized execution environment storage

## API Endpoints

### Session Management

#### `GET /sessions`
List all active sessions with metadata.

**Response:**
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
      "history": [],
      "environment": null
    }
  ],
  "total": 1
}
```

#### `POST /sessions`
Create a new session.

**Request:**
```json
{
  "name": "My Session",
  "language": "python"
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "My Session",
  "language": "python",
  "created_at": "2025-08-08T22:00:00Z",
  "last_accessed": "2025-08-08T22:00:00Z",
  "execution_count": 0,
  "history": [],
  "environment": null
}
```

#### `GET /sessions/{sessionId}`
Get session information and update last accessed time.

**Response:** SessionInfo object with full session details

#### `DELETE /sessions/{sessionId}`
Delete a session and cleanup from language backend.

**Response:**
```json
{
  "message": "Session deleted successfully",
  "session_id": "uuid",
  "cleanup_successful": true
}
```

#### `PUT /sessions/{sessionId}/rename`
Rename a session.

**Request:**
```json
{
  "name": "New Session Name"
}
```

**Response:**
```json
{
  "message": "Session renamed successfully",
  "session_id": "uuid",
  "new_name": "New Session Name"
}
```

### Session Activity Management

#### `PUT /sessions/{sessionId}/activity`
Update session activity when code is executed. Auto-creates session if it doesn't exist.

**Parameters:** 
- `sessionId`: Session UUID
- `language`: Language name (query parameter)

**Response:**
```json
{
  "message": "Session activity updated"
}
```

### Terminal History Management

#### `POST /sessions/{sessionId}/history`
Add a terminal entry to session history.

**Request:**
```json
{
  "entry": {
    "id": "entry-uuid",
    "type": "input",
    "content": "print('hello')",
    "timestamp": "2025-08-08T22:30:00Z"
  }
}
```

**Response:**
```json
{
  "message": "History entry added",
  "entry_count": 5
}
```

#### `GET /sessions/{sessionId}/history`
Get terminal history for a specific session.

**Response:**
```json
{
  "history": [
    {
      "id": "entry-uuid",
      "type": "input",
      "content": "print('hello')",
      "timestamp": "2025-08-08T22:30:00Z"
    }
  ],
  "count": 1
}
```

#### `PUT /sessions/{sessionId}/history/{entryId}`
Update an existing terminal history entry (used for streaming output persistence).

**Request:**
```json
{
  "content": "Updated output content"
}
```

**Response:**
```json
{
  "message": "History entry updated successfully",
  "entry_id": "entry-uuid"
}
```

#### `DELETE /sessions/{sessionId}/history`
Clear terminal history for a specific session.

**Response:**
```json
{
  "message": "History cleared",
  "session_id": "uuid"
}
```

### Environment State Management

#### `GET /sessions/{sessionId}/environment`
Get the serialized environment state for a session.

**Response:**
```json
{
  "environment": {
    "language": "python",
    "serialized_data": "base64-encoded-state",
    "last_updated": "2025-08-08T22:30:00Z"
  }
}
```

#### `PUT /sessions/{sessionId}/environment`
Update the serialized environment state for a session.

**Request:**
```json
{
  "language": "python",
  "serialized_data": "base64-encoded-state"
}
```

#### `DELETE /sessions/{sessionId}/environment`
Clear the serialized environment state for a session.

### Admin Interface

#### `GET /admin/sessions`
Admin endpoint with detailed session information including full history and environment details.

**Response:** Extended session data with statistics and detailed inspection info

### Health Check

#### `GET /health`
Health check endpoint with database connectivity test.

**Response:**
```json
{
  "status": "healthy",
  "service": "session-manager",
  "database": "connected"
}
```

## Database Schema

### SessionModel Table
- `id`: Primary key, session UUID
- `name`: User-assigned session name
- `language`: Single language per session (immutable after creation)
- `created_at`: Session creation timestamp
- `last_accessed`: Last execution or access time
- `execution_count`: Number of code executions
- `history`: JSON array of terminal entries
- `environment_data`: Base64 encoded serialized environment state
- `environment_language`: Language of stored environment
- `environment_updated`: Last environment update timestamp

## Session Architecture

### Single Language Per Session
- Each session is bound to a single programming language at creation
- Language cannot be changed after session creation
- Attempts to execute different language code in a session return HTTP 400

### Session Lifecycle
1. **Creation**: Session created with UUID, name, and language
2. **Activity Tracking**: Execution count and last accessed time updated on code execution
3. **History Persistence**: Terminal entries stored in database with timestamps
4. **Environment Storage**: Optional serialized execution state storage
5. **Cleanup**: Session deletion triggers backend cleanup via HTTP calls

### Language Backend Integration
The session manager communicates with language backends for cleanup:

```python
LANGUAGE_BACKENDS = {
    "python": "http://backend-python:8000",
    "javascript": "http://backend-javascript:8000", 
    "ruby": "http://backend-ruby:8000",
    "php": "http://backend-php:8000",
    "kotlin": "http://backend-kotlin:8000"
}
```

When sessions are deleted, the session manager calls `POST {backend_url}/reset/{sessionId}` to cleanup execution state.

### Server-Sent Events (SSE) Integration

The session manager supports real-time streaming output persistence:

**History Update Flow for Streaming**:
1. Frontend receives SSE events from streaming-enabled backends
2. Terminal entries updated incrementally in frontend UI
3. Updates sent to session manager via `PUT /sessions/{sessionId}/history/{entryId}`
4. History persisted in database for page refresh scenarios

**Implementation Details**:
```python
@app.put("/sessions/{session_id}/history/{entry_id}")
async def update_history_entry(session_id: str, entry_id: str, request: UpdateHistoryEntryRequest):
    # Find and update specific entry by ID in history array
    for entry in session.history:
        if entry.get('id') == entry_id:
            entry['content'] = request.content
            flag_modified(session, 'history')  # Mark JSON column as modified
            break
```

**Benefits**:
- **Persistent Streaming**: SSE output preserved across browser sessions
- **Incremental Updates**: Efficient updates to existing entries without recreating entire history
- **Database Consistency**: Atomic updates ensure history integrity

## Development

### Local Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Development
```bash
# Build image
docker build -t webrepl-session-manager .

# Run container with volume
docker run -p 8000:8000 -v session_data:/app/data webrepl-session-manager
```

## Configuration

- **CORS**: Environment-based configuration
  - Development (`ENVIRONMENT=development`): Allows all origins  
  - Production: Restricted to specific frontend origins
- **Database**: SQLite file stored at `/app/data/sessions.db` (volume mounted)
- **Port**: 8000 (internal container port)
- **Host**: 0.0.0.0 (binds to all interfaces)

## Data Persistence

### SQLite Database
- Database file: `/app/data/sessions.db`
- Volume mount: `session_data:/app/data` for persistence across container restarts
- Automatic table creation on startup via `init_db()`

### Terminal History Persistence
- Terminal entries stored as JSON array in `history` column
- Support for updating existing entries for streaming output persistence
- Explicit SQLAlchemy change tracking using `flag_modified()` for JSON column updates
- Atomic updates to prevent history corruption
- Entry ID-based updates enable real-time streaming output persistence

### Environment Serialization
- Language backends can serialize execution state to base64 strings
- Stored in `environment_data` column with metadata
- Supports restore of execution contexts across sessions

## Error Handling

- **Database Errors**: Connection failures handled with rollback
- **Validation Errors**: Pydantic model validation with detailed error messages  
- **Backend Communication**: Timeout and connection error handling for language backend calls
- **Session Not Found**: HTTP 404 responses for invalid session IDs
- **Language Mismatch**: HTTP 400 when trying to execute wrong language in session

## Performance Considerations

- **Database Indexing**: Session ID is primary key for fast lookups
- **History Storage**: Large terminal histories may impact query performance
- **Memory Usage**: Session metadata cached in application memory
- **Cleanup Operations**: Asynchronous backend cleanup calls with timeout protection

## Security

- **Container Isolation**: Service runs in isolated container with limited network access
- **Database Security**: SQLite file permissions restricted to application user
- **Input Validation**: All API inputs validated through Pydantic models
- **CORS Protection**: Production CORS configuration restricts frontend origins

## Testing

The session manager can be tested by accessing the health endpoint and creating/managing sessions through the API endpoints.

## Admin Features

- **Session Statistics**: Summary of total sessions, executions, and language distribution
- **Detailed Inspection**: Full session history and environment details for debugging
- **Performance Monitoring**: Session creation times, execution counts, and access patterns