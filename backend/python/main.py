import io
import os
import sys
import logging
import base64
import pickle
from typing import Any, Dict
from datetime import datetime
import httpx

from fastapi import FastAPI, HTTPException, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from error_handler import ErrorHandler, ErrorType, ExecutionResult, get_http_status_for_error_type

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Python REPL API",
    description="Session-based Python REPL with automatic cleanup and monitoring",
    version="2.0.0"
)

# Session Manager URL
SESSION_MANAGER_URL = "http://session-manager:8000"

async def serialize_namespace(namespace: Dict[str, Any]) -> str:
    """Serialize a Python namespace to base64-encoded string"""
    try:
        serialized_bytes = pickle.dumps(namespace)
        return base64.b64encode(serialized_bytes).decode('utf-8')
    except Exception as e:
        logger.warning(f"Failed to serialize namespace: {e}")
        return ""

async def deserialize_namespace(serialized_data: str) -> Dict[str, Any]:
    """Deserialize a base64-encoded string back to Python namespace"""
    try:
        if not serialized_data:
            return {}
        serialized_bytes = base64.b64decode(serialized_data.encode('utf-8'))
        return pickle.loads(serialized_bytes)
    except Exception as e:
        logger.warning(f"Failed to deserialize namespace: {e}")
        return {}

async def get_session_namespace(session_id: str) -> Dict[str, Any]:
    """Get the execution namespace for a session from the session manager"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{SESSION_MANAGER_URL}/sessions/{session_id}/environment")
            if response.status_code == 200:
                data = response.json()
                if data.get("environment") and data["environment"].get("serialized_data"):
                    return await deserialize_namespace(data["environment"]["serialized_data"])
            return {}
    except Exception as e:
        logger.warning(f"Failed to get session environment: {e}")
        return {}

async def save_session_namespace(session_id: str, namespace: Dict[str, Any]):
    """Save the execution namespace for a session to the session manager"""
    try:
        serialized_data = await serialize_namespace(namespace)
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.put(
                f"{SESSION_MANAGER_URL}/sessions/{session_id}/environment",
                json={
                    "language": "python",
                    "serialized_data": serialized_data
                }
            )
    except Exception as e:
        logger.warning(f"Failed to save session environment: {e}")

async def verify_session_language(session_id: str) -> bool:
    """Verify that the session is configured for Python"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{SESSION_MANAGER_URL}/sessions/{session_id}")
            if response.status_code == 200:
                session_data = response.json()
                return session_data.get("language") == "python"
            return False
    except Exception as e:
        logger.warning(f"Failed to verify session language: {e}")
        return False

async def notify_session_manager(session_id: str):
    """Notify the centralized session manager of activity"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.put(f"{SESSION_MANAGER_URL}/sessions/{session_id}/activity", params={"language": "python"})
    except Exception as e:
        logger.warning(f"Failed to notify session manager: {e}")

# CORS configuration - allow all origins in development
cors_origins = ["*"] if os.getenv("ENVIRONMENT", "development") == "development" else ["http://localhost:8080"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CodeRequest(BaseModel):
    code: str


class CodeResponse(BaseModel):
    output: str = ""
    error: str | None = None
    error_type: str | None = None
    session_info: Dict[str, Any] | None = None


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Python REPL API is running"}


# Remove old function as it's now handled by session_manager


@app.post("/execute/{session_id}", response_model=CodeResponse)
async def execute_code(
    request: CodeRequest, 
    session_id: str = Path(..., description="Session GUID")
) -> CodeResponse:
    logger.info(f"Executing code for session {session_id[:8]}...")
    
    # Verify session is configured for Python
    if not await verify_session_language(session_id):
        raise HTTPException(
            status_code=400,
            detail=f"Session {session_id} is not configured for Python"
        )
    
    # Validate input
    if not request.code.strip():
        error_response = ErrorHandler.handle_validation_error(
            "Code cannot be empty", session_id
        )
        raise HTTPException(
            status_code=get_http_status_for_error_type(error_response.error_type),
            detail=error_response.message
        )

    output_buffer = io.StringIO()
    execution_error = None

    old_stdout = sys.stdout
    old_stderr = sys.stderr

    try:
        sys.stdout = output_buffer
        sys.stderr = output_buffer

        try:
            # Get session namespace from session manager
            namespace = await get_session_namespace(session_id)
            
            code = request.code.strip()
            
            # Try to evaluate as expression first (for REPL-like behavior)
            try:
                result = eval(code, namespace)
                # If eval succeeds and returns a value (not None), display it
                if result is not None:
                    print(repr(result))
            except SyntaxError:
                # If eval fails, try exec (for statements like assignments, imports, etc.)
                exec(code, namespace)
            
            # Save updated namespace back to session manager
            await save_session_namespace(session_id, namespace)
            
        except Exception as e:
            execution_error = e
            logger.warning(f"Execution error in session {session_id[:8]}: {e}")

        output = output_buffer.getvalue()

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        output_buffer.close()

    # Session info will come from session manager - we don't track it locally anymore
    session_data = None

    # Notify session manager of activity
    await notify_session_manager(session_id)
    
    # Format result using error handler
    result = ErrorHandler.format_execution_result(
        output=output,
        error=execution_error,
        session_id=session_id,
        session_info=session_data
    )
    
    return CodeResponse(
        output=result.output,
        error=result.error,
        error_type=result.error_type.value if result.error_type else None,
        session_info=result.session_info
    )


@app.get("/health")
def health_check() -> Dict[str, Any]:
    """Enhanced health check endpoint"""
    return {
        "status": "ok",
        "language": "python",
        "version": "2.0.0",
        "stateless": True,  # Now stateless!
        "timestamp": datetime.now().isoformat()
    }


@app.post("/reset/{session_id}")
async def reset_namespace(session_id: str = Path(..., description="Session GUID")) -> Dict[str, str]:
    """Reset the session namespace, clearing all variables"""
    logger.info(f"Resetting session {session_id[:8]}...")
    
    try:
        # Clear environment in session manager
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(f"{SESSION_MANAGER_URL}/sessions/{session_id}/environment")
            if response.status_code == 200:
                return {"message": "Namespace reset successfully", "session_id": session_id}
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
            else:
                raise HTTPException(status_code=500, detail="Failed to reset session environment")
    except httpx.RequestError as e:
        logger.error(f"Failed to communicate with session manager: {e}")
        raise HTTPException(status_code=503, detail="Session manager unavailable")


# Session management is now handled by the central session manager service


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Python REPL API v2.0.0...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )
