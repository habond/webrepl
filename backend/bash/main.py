import subprocess
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Environment variables
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8080").split(",")

# Configure CORS
if ENVIRONMENT == "development":
    # Development: Allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Production: Restrict to specified origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Session storage: Each session has its own execution environment
sessions: Dict[str, Dict[str, Any]] = {}

class CodeRequest(BaseModel):
    code: str

class ExecuteResponse(BaseModel):
    output: str
    error: Optional[str] = None

def get_or_create_session(session_id: str) -> Dict[str, Any]:
    """Get existing session or create new one"""
    if session_id not in sessions:
        sessions[session_id] = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_accessed": datetime.now(timezone.utc).isoformat(),
            "execution_count": 0,
            "working_directory": f"/tmp/bash_sessions/{session_id}",
            "environment": os.environ.copy()
        }
        # Create session-specific working directory
        os.makedirs(sessions[session_id]["working_directory"], exist_ok=True)
        logger.info(f"Created new Bash session: {session_id}")
    
    sessions[session_id]["last_accessed"] = datetime.now(timezone.utc).isoformat()
    return sessions[session_id]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "bash-backend"}

@app.post("/execute/{session_id}", response_model=ExecuteResponse)
async def execute_code(session_id: str, request: CodeRequest):
    """Execute Bash code in a session-specific environment"""
    
    if not request.code or request.code.strip() == "":
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
    session = get_or_create_session(session_id)
    session["execution_count"] += 1
    
    try:
        # Execute the bash command in the session's working directory
        result = subprocess.run(
            request.code,
            shell=True,
            capture_output=True,
            text=True,
            cwd=session["working_directory"],
            env=session["environment"],
            timeout=30  # 30 second timeout
        )
        
        # Combine stdout and stderr for output
        output = result.stdout
        error = result.stderr if result.stderr else None
        
        # If command failed with non-zero exit code, include that in error
        if result.returncode != 0 and not error:
            error = f"Command exited with code {result.returncode}"
        
        logger.info(f"Session {session_id}: Executed command (count: {session['execution_count']})")
        
        return ExecuteResponse(output=output, error=error)
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Session {session_id}: Command timed out")
        return ExecuteResponse(
            output="",
            error="Command execution timed out after 30 seconds"
        )
    except Exception as e:
        logger.error(f"Session {session_id}: Execution error: {str(e)}")
        return ExecuteResponse(
            output="",
            error=f"Error executing command: {str(e)}"
        )

@app.post("/reset/{session_id}")
async def reset_session(session_id: str):
    """Reset a specific session"""
    if session_id in sessions:
        # Clean up working directory
        working_dir = sessions[session_id]["working_directory"]
        if os.path.exists(working_dir):
            try:
                # Remove all files in the working directory
                subprocess.run(f"rm -rf {working_dir}/*", shell=True, check=False)
            except:
                pass
        
        # Remove session from memory
        del sessions[session_id]
        logger.info(f"Reset session: {session_id}")
        
    return {"message": "Session reset successfully"}

@app.get("/sessions")
async def list_sessions():
    """List all active sessions with metadata"""
    session_list = []
    for session_id, session_data in sessions.items():
        session_list.append({
            "id": session_id,
            "created_at": session_data["created_at"],
            "last_accessed": session_data["last_accessed"],
            "execution_count": session_data["execution_count"],
            "working_directory": session_data["working_directory"]
        })
    return {"sessions": session_list}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)