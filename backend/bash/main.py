import subprocess
import os
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
import json

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

async def stream_command_output(session_id: str, code: str) -> AsyncGenerator[str, None]:
    """Stream command output using Server-Sent Events"""
    session = get_or_create_session(session_id)
    session["execution_count"] += 1
    
    process = None
    try:
        # Set environment to reduce buffering
        env = session["environment"].copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["TERM"] = "dumb"
        
        # Write the command to a temporary script file to ensure proper execution
        import tempfile
        import os
        
        # Create temporary script file for proper bash execution
        script_fd, script_path = tempfile.mkstemp(suffix='.sh', dir=session["working_directory"])
        try:
            script_content = f"#!/bin/bash\nset -e\n{code}\n"
            with os.fdopen(script_fd, 'w') as script_file:
                script_file.write(script_content)
            
            # Make the script executable
            os.chmod(script_path, 0o755)
            
            process = await asyncio.create_subprocess_exec(
                '/bin/bash', script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=session["working_directory"],
                env=env
            )
        except Exception as e:
            # Cleanup script file on error
            try:
                os.unlink(script_path)
            except:
                pass
            raise e
        
        # Stream output line by line from both stdout and stderr
        async def stream_output():
            """Stream lines from stdout and stderr as they become available"""
            
            # Read output line by line as it becomes available
            while True:
                # Check if process is still running
                if process.returncode is not None:
                    break
                
                # Try to read a line from stdout
                try:
                    line = await asyncio.wait_for(process.stdout.readline(), timeout=0.1)
                    if line:
                        decoded_line = line.decode('utf-8', errors='replace')
                        yield f"data: {json.dumps({'type': 'output', 'content': decoded_line})}\n\n"
                    else:
                        # Empty line means EOF - check stderr too
                        try:
                            stderr_line = await asyncio.wait_for(process.stderr.readline(), timeout=0.01)
                            if stderr_line:
                                decoded_line = stderr_line.decode('utf-8', errors='replace')
                                yield f"data: {json.dumps({'type': 'error', 'content': decoded_line})}\n\n"
                        except asyncio.TimeoutError:
                            pass
                        # If no stdout and process might be done, break
                        break
                except asyncio.TimeoutError:
                    # No output available yet, but process might still be running
                    # Check stderr too
                    try:
                        stderr_line = await asyncio.wait_for(process.stderr.readline(), timeout=0.01)
                        if stderr_line:
                            decoded_line = stderr_line.decode('utf-8', errors='replace')
                            yield f"data: {json.dumps({'type': 'error', 'content': decoded_line})}\n\n"
                    except asyncio.TimeoutError:
                        pass
                    # Continue waiting for more output
                    continue
        
        # Stream output and wait for process completion concurrently
        output_done = False
        
        async def stream_and_check():
            nonlocal output_done
            async for line in stream_output():
                yield line
            output_done = True
        
        # Create tasks for streaming and process completion
        stream_task = stream_and_check()
        
        # Continue streaming until both output is done AND process completes
        async for line in stream_task:
            yield line
            
        # Wait for process to complete
        return_code = await process.wait()
        
        # Cleanup the temporary script file
        try:
            os.unlink(script_path)
        except:
            pass
        
        # Send completion event
        yield f"data: {json.dumps({'type': 'complete', 'returnCode': return_code})}\n\n"
        
        logger.info(f"Session {session_id}: Streamed command execution completed")
        
    except asyncio.TimeoutError:
        logger.warning(f"Session {session_id}: Command timed out")
        yield f"data: {json.dumps({'type': 'error', 'content': 'Command execution timed out after 30 seconds'})}\n\n"
        if process:
            process.kill()
            await process.wait()
        # Cleanup script file
        try:
            os.unlink(script_path)
        except:
            pass
    except Exception as e:
        logger.error(f"Session {session_id}: Streaming execution error: {str(e)}")
        yield f"data: {json.dumps({'type': 'error', 'content': f'Error executing command: {str(e)}'})}\n\n"
        if process:
            try:
                process.kill()
                await process.wait()
            except:
                pass
        # Cleanup script file
        try:
            os.unlink(script_path)
        except:
            pass

@app.post("/execute-stream/{session_id}")
async def execute_code_stream(session_id: str, request: CodeRequest):
    """Execute Bash code with streaming output using Server-Sent Events"""
    
    if not request.code or request.code.strip() == "":
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
    return StreamingResponse(
        stream_command_output(session_id, request.code),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
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