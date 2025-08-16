import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional, Any

import httpx
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.orm.attributes import flag_modified

from database import get_db, init_db, SessionModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Terminal entry models
from typing import Union

class TerminalEntry(BaseModel):
    id: str
    type: str  # 'input', 'output', 'error'
    content: str
    timestamp: Union[datetime, str]  # Accept both datetime and string

# Environment state models
class EnvironmentState(BaseModel):
    language: str
    serialized_data: Optional[str] = None  # Base64 encoded serialized environment
    last_updated: datetime

# Session data models  
class Session(BaseModel):
    id: str
    name: str
    language: str  # Single language per session - immutable after creation
    created_at: datetime
    last_accessed: datetime
    execution_count: int = 0
    history: List[TerminalEntry] = []
    environment: Optional[EnvironmentState] = None  # Serialized execution environment

class CreateSessionRequest(BaseModel):
    name: Optional[str] = None
    language: str = "python"  # Default to python

class AddHistoryEntryRequest(BaseModel):
    entry: TerminalEntry

class UpdateHistoryEntryRequest(BaseModel):
    content: str

class UpdateEnvironmentRequest(BaseModel):
    language: str
    serialized_data: Optional[str] = None  # Base64 encoded serialized state

class RenameSessionRequest(BaseModel):
    name: str

class SessionInfo(BaseModel):
    id: str
    name: str
    language: str  # Single language per session
    created_at: datetime
    last_accessed: datetime
    execution_count: int
    history: List[TerminalEntry] = []
    environment: Optional[EnvironmentState] = None

# Language backend endpoints
LANGUAGE_BACKENDS = {
    "python": os.getenv("PYTHON_BACKEND_URL", "http://backend-python:8000"),
    "javascript": os.getenv("JAVASCRIPT_BACKEND_URL", "http://backend-javascript:8000"), 
    "ruby": os.getenv("RUBY_BACKEND_URL", "http://backend-ruby:8000"),
    "php": os.getenv("PHP_BACKEND_URL", "http://backend-php:8000"),
    "kotlin": os.getenv("KOTLIN_BACKEND_URL", "http://backend-kotlin:8000"),
    "haskell": os.getenv("HASKELL_BACKEND_URL", "http://backend-haskell:8000")
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    print("Session Manager starting up...")
    init_db()
    yield
    # Shutdown: Cleanup if needed
    print("Session Manager shutting down...")

app = FastAPI(
    title="Session Manager API",
    description="Centralized session management for multi-language REPL",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
environment = os.getenv("ENVIRONMENT", "development")
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:8080")
if environment == "development":
    allowed_origins = ["*"]
else:
    allowed_origins = cors_origins_env.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions
def db_session_to_pydantic(db_session: SessionModel) -> SessionInfo:
    """Convert database session model to Pydantic model"""
    history = []
    if db_session.history:
        for entry in db_session.history:
            history.append(TerminalEntry(**entry))
    
    environment = None
    if db_session.environment_data:
        environment = EnvironmentState(
            language=db_session.environment_language,
            serialized_data=db_session.environment_data,
            last_updated=db_session.environment_updated
        )
    
    return SessionInfo(
        id=db_session.id,
        name=db_session.name,
        language=db_session.language,
        created_at=db_session.created_at,
        last_accessed=db_session.last_accessed,
        execution_count=db_session.execution_count,
        history=history,
        environment=environment
    )

@app.get("/health")
async def health_check(db: DBSession = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "session-manager", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "service": "session-manager", "database": "disconnected", "error": str(e)}

@app.get("/sessions")
async def list_sessions(db: DBSession = Depends(get_db)):
    """List all active sessions"""
    sessions = db.query(SessionModel).all()
    session_list = [db_session_to_pydantic(session) for session in sessions]
    
    return {
        "sessions": session_list,
        "total": len(session_list)
    }

@app.get("/admin/sessions")
async def admin_list_sessions(db: DBSession = Depends(get_db)):
    """Admin endpoint: List all sessions with detailed information for admin interface"""
    sessions = db.query(SessionModel).all()
    
    admin_sessions = []
    for session in sessions:
        history_count = len(session.history) if session.history else 0
        last_history_entry = None
        
        if session.history and len(session.history) > 0:
            # Get the most recent history entry
            last_entry = session.history[-1]
            last_history_entry = {
                "type": last_entry.get("type"),
                "content": last_entry.get("content", "")[:100] + "..." if len(last_entry.get("content", "")) > 100 else last_entry.get("content", ""),
                "timestamp": last_entry.get("timestamp")
            }
        
        # Include full history for detailed inspection
        full_history = []
        if session.history:
            full_history = session.history
        
        # Include environment details
        environment_details = None
        if session.environment_data:
            environment_details = {
                "language": session.environment_language,
                "data": session.environment_data,
                "last_updated": session.environment_updated,
                "data_size": len(session.environment_data) if session.environment_data else 0
            }
        
        admin_session = {
            "id": session.id,
            "name": session.name,
            "language": session.language,
            "created_at": session.created_at,
            "last_accessed": session.last_accessed,
            "execution_count": session.execution_count,
            "history_count": history_count,
            "last_history_entry": last_history_entry,
            "has_environment": session.environment_data is not None,
            "environment_language": session.environment_language,
            "environment_updated": session.environment_updated,
            "full_history": full_history,
            "environment_details": environment_details
        }
        admin_sessions.append(admin_session)
    
    # Sort by last accessed (most recent first)
    admin_sessions.sort(key=lambda x: x["last_accessed"], reverse=True)
    
    return {
        "sessions": admin_sessions,
        "total": len(admin_sessions),
        "summary": {
            "total_sessions": len(admin_sessions),
            "by_language": {lang: len([s for s in admin_sessions if s["language"] == lang]) 
                          for lang in set(s["language"] for s in admin_sessions)},
            "active_sessions": len([s for s in admin_sessions if s["execution_count"] > 0]),
            "total_executions": sum(s["execution_count"] for s in admin_sessions)
        }
    }

@app.post("/sessions", response_model=SessionInfo)
async def create_session(request: CreateSessionRequest, db: DBSession = Depends(get_db)):
    """Create a new session"""
    session_id = str(uuid.uuid4())
    
    # Count existing sessions for default naming
    session_count = db.query(SessionModel).count()
    session_name = request.name or f"Session {session_count + 1}"
    
    db_session = SessionModel(
        id=session_id,
        name=session_name,
        language=request.language,
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow(),
        execution_count=0,
        history=[]
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session_to_pydantic(db_session)

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: DBSession = Depends(get_db)):
    """Delete a session and cleanup from all language backends"""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Cleanup session from the session's language backend
    cleanup_result = None
    backend_url = LANGUAGE_BACKENDS.get(db_session.language)
    if backend_url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{backend_url}/reset/{session_id}")
                cleanup_result = response.status_code == 200
        except Exception as e:
            print(f"Failed to cleanup {db_session.language} backend for session {session_id}: {e}")
            cleanup_result = False
    
    # Remove from database
    db.delete(db_session)
    db.commit()
    
    return {
        "message": "Session deleted successfully",
        "session_id": session_id,
        "cleanup_successful": cleanup_result
    }

@app.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str, db: DBSession = Depends(get_db)):
    """Get session information"""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update last accessed time
    db_session.last_accessed = datetime.utcnow()
    db.commit()
    
    return db_session_to_pydantic(db_session)

@app.put("/sessions/{session_id}/rename")
async def rename_session(session_id: str, request: RenameSessionRequest, db: DBSession = Depends(get_db)):
    """Rename a session"""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db_session.name = request.name
    db_session.last_accessed = datetime.utcnow()
    db.commit()
    
    return {"message": "Session renamed successfully", "session_id": session_id, "new_name": request.name}

@app.put("/sessions/{session_id}/activity")
async def update_session_activity(session_id: str, language: str, db: DBSession = Depends(get_db)):
    """Update session activity when code is executed"""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not db_session:
        # Auto-create session if it doesn't exist (for backward compatibility)
        session_count = db.query(SessionModel).count()
        db_session = SessionModel(
            id=session_id,
            name=f"Session {session_count + 1}",
            language=language,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            execution_count=0,
            history=[]
        )
        db.add(db_session)
    else:
        # Enforce single language per session
        if db_session.language != language:
            raise HTTPException(
                status_code=400, 
                detail=f"Session {session_id} is configured for {db_session.language}, cannot execute {language} code"
            )
        
        # Update session metadata
        db_session.last_accessed = datetime.utcnow()
        db_session.execution_count += 1
    
    db.commit()
    
    return {"message": "Session activity updated"}

@app.post("/sessions/{session_id}/history")
async def add_history_entry(session_id: str, request: AddHistoryEntryRequest, db: DBSession = Depends(get_db)):
    """Add a terminal entry to session history"""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get existing history and create a NEW list (don't modify in place)
    existing_history = db_session.history if db_session.history else []
    
    # Add new entry - convert to dict with string timestamp
    entry_dict = {
        'id': request.entry.id,
        'type': request.entry.type,
        'content': request.entry.content,
        'timestamp': request.entry.timestamp.isoformat() if isinstance(request.entry.timestamp, datetime) else request.entry.timestamp
    }
    
    # Create a completely new list (critical for SQLAlchemy change detection)
    new_history = existing_history + [entry_dict]
    
    # Update session with the NEW list object
    db_session.history = new_history
    db_session.last_accessed = datetime.utcnow()
    
    # Explicitly mark the history attribute as modified for SQLAlchemy
    flag_modified(db_session, 'history')
    
    try:
        db.commit()
        logger.info(f"Successfully saved {len(new_history)} history entries to database")
    except Exception as e:
        logger.error(f"Database commit error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save history: {str(e)}")
    
    return {"message": "History entry added", "entry_count": len(new_history)}

@app.put("/sessions/{session_id}/history/{entry_id}")
async def update_history_entry(session_id: str, entry_id: str, request: UpdateHistoryEntryRequest, db: DBSession = Depends(get_db)):
    """Update content of a specific terminal entry in session history"""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get existing history
    existing_history = db_session.history if db_session.history else []
    
    # Find and update the specific entry
    entry_found = False
    new_history = []
    for entry in existing_history:
        if entry.get('id') == entry_id:
            # Update the content of this entry
            updated_entry = {**entry, 'content': request.content}
            new_history.append(updated_entry)
            entry_found = True
        else:
            new_history.append(entry)
    
    if not entry_found:
        raise HTTPException(status_code=404, detail="History entry not found")
    
    # Update session with the modified history
    db_session.history = new_history
    db_session.last_accessed = datetime.utcnow()
    
    # Explicitly mark the history attribute as modified for SQLAlchemy
    flag_modified(db_session, 'history')
    
    try:
        db.commit()
        logger.info(f"Successfully updated history entry {entry_id} in session {session_id}")
    except Exception as e:
        logger.error(f"Database commit error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update history entry: {str(e)}")
    
    return {"message": "History entry updated", "entry_id": entry_id}

@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, db: DBSession = Depends(get_db)):
    """Get terminal history for a specific session"""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db_session.last_accessed = datetime.utcnow()
    db.commit()
    
    history = db_session.history if db_session.history else []
    
    return {"history": history, "count": len(history)}

@app.delete("/sessions/{session_id}/history")
async def clear_session_history(session_id: str, db: DBSession = Depends(get_db)):
    """Clear terminal history for a specific session"""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db_session.history = []
    db_session.last_accessed = datetime.utcnow()
    
    # Explicitly mark the history attribute as modified
    flag_modified(db_session, 'history')
    
    db.commit()
    
    return {"message": "History cleared", "session_id": session_id}

@app.get("/sessions/{session_id}/environment")
async def get_session_environment(session_id: str, db: DBSession = Depends(get_db)):
    """Get the serialized environment state for a session"""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db_session.last_accessed = datetime.utcnow()
    db.commit()
    
    if not db_session.environment_data:
        return {"environment": None, "message": "No environment state stored"}
    
    environment = EnvironmentState(
        language=db_session.environment_language,
        serialized_data=db_session.environment_data,
        last_updated=db_session.environment_updated
    )
    
    return {"environment": environment}

@app.put("/sessions/{session_id}/environment")
async def update_session_environment(session_id: str, request: UpdateEnvironmentRequest, db: DBSession = Depends(get_db)):
    """Update the serialized environment state for a session"""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db_session.environment_data = request.serialized_data
    db_session.environment_language = request.language
    db_session.environment_updated = datetime.utcnow()
    db_session.last_accessed = datetime.utcnow()
    db.commit()
    
    return {"message": "Environment state updated", "session_id": session_id}

@app.delete("/sessions/{session_id}/environment")
async def clear_session_environment(session_id: str, db: DBSession = Depends(get_db)):
    """Clear the serialized environment state for a session"""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db_session.environment_data = None
    db_session.environment_language = None
    db_session.environment_updated = None
    db_session.last_accessed = datetime.utcnow()
    db.commit()
    
    return {"message": "Environment state cleared", "session_id": session_id}

if __name__ == "__main__":
    import uvicorn
    backend_port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=backend_port)