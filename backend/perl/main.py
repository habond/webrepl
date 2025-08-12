"""
Perl Backend for Web REPL
Executes Perl code in isolated session environments
"""

import os
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Perl Backend")

# Configure CORS
environment = os.getenv("ENVIRONMENT", "development")
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:8080")

if environment == "development":
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

logger.info(f"Environment: {environment}")
logger.info(f"CORS origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session storage: maps session_id to session data
sessions: Dict[str, Dict] = {}

class CodeRequest(BaseModel):
    code: str

class ExecutionResponse(BaseModel):
    output: str
    error: Optional[str] = None

def get_session_dir(session_id: str) -> Path:
    """Get or create the session directory for a given session ID."""
    session_dir = Path(f"/tmp/perl_sessions/{session_id}")
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir

def get_or_create_session(session_id: str) -> Dict:
    """Get or create a session for the given session ID."""
    if session_id not in sessions:
        session_dir = get_session_dir(session_id)
        sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "execution_count": 0,
            "working_dir": str(session_dir),
            "history_file": str(session_dir / "history.pl")
        }
        logger.info(f"Created new Perl session: {session_id}")
        
        # Initialize history file with strict mode and warnings
        history_file = Path(sessions[session_id]["history_file"])
        history_file.write_text("#!/usr/bin/perl\nuse strict;\nuse warnings;\n\n")
    
    # Update last accessed time
    sessions[session_id]["last_accessed"] = datetime.now().isoformat()
    return sessions[session_id]

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "language": "perl", "sessions": len(sessions)}

@app.post("/execute/{session_id}", response_model=ExecutionResponse)
def execute_code(session_id: str, request: CodeRequest):
    """Execute Perl code in a session-isolated environment."""
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
    session = get_or_create_session(session_id)
    session["execution_count"] += 1
    
    try:
        # Get the session's history file
        history_file = Path(session["history_file"])
        existing_code = history_file.read_text()
        
        # Create a temporary file with all previous code plus the new code
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.pl',
            dir=session["working_dir"],
            delete=False
        ) as temp_file:
            # Write all previous code
            temp_file.write(existing_code)
            
            # Add the new code
            temp_file.write(f"\n# Execution {session['execution_count']}\n")
            temp_file.write(request.code)
            if not request.code.endswith('\n'):
                temp_file.write('\n')
            temp_file.flush()
            temp_path = temp_file.name
        
        # Execute the Perl script
        result = subprocess.run(
            ["perl", temp_path],
            capture_output=True,
            text=True,
            cwd=session["working_dir"],
            timeout=30
        )
        
        # If execution was successful, append the code to history
        if result.returncode == 0:
            with open(history_file, 'a') as f:
                f.write(f"\n# Execution {session['execution_count']}\n")
                f.write(request.code)
                if not request.code.endswith('\n'):
                    f.write('\n')
        
        # Clean up temp file
        os.unlink(temp_path)
        
        # Combine stdout and stderr for output
        output = result.stdout
        error = result.stderr if result.returncode != 0 else None
        
        logger.info(f"Session {session_id}: Executed Perl code (execution #{session['execution_count']})")
        
        return ExecutionResponse(
            output=output or "",
            error=error
        )
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Session {session_id}: Code execution timed out")
        return ExecutionResponse(
            output="",
            error="Execution timed out after 30 seconds"
        )
    except Exception as e:
        logger.error(f"Session {session_id}: Execution error: {str(e)}")
        return ExecutionResponse(
            output="",
            error=str(e)
        )

@app.post("/reset/{session_id}")
def reset_session(session_id: str):
    """Reset the session state for a given session ID."""
    if session_id in sessions:
        session_dir = Path(sessions[session_id]["working_dir"])
        
        # Remove all files in the session directory
        if session_dir.exists():
            for file in session_dir.iterdir():
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    import shutil
                    shutil.rmtree(file)
        
        # Remove session from memory
        del sessions[session_id]
        logger.info(f"Reset Perl session: {session_id}")
        
        # Recreate the session
        get_or_create_session(session_id)
        
        return {"message": "Session reset successfully"}
    else:
        return {"message": "Session not found, creating new session"}

@app.get("/sessions")
def list_sessions():
    """List all active sessions."""
    return {
        "sessions": [
            {
                "id": session_id,
                "created_at": data["created_at"],
                "last_accessed": data["last_accessed"],
                "execution_count": data["execution_count"]
            }
            for session_id, data in sessions.items()
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)