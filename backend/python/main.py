import io
import os
import sys
import logging
import base64
import pickle
import asyncio
import json
import threading
import time
from typing import Any, Dict, AsyncGenerator, Optional
from datetime import datetime
import httpx

from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
SESSION_MANAGER_URL = os.getenv("SESSION_MANAGER_URL", "http://session-manager:8000")

async def serialize_namespace(namespace: Dict[str, Any]) -> str:
    """Serialize a Python namespace to base64-encoded string"""
    logger.error(f"ENTERING serialize_namespace with {len(namespace)} items")
    try:
        # Filter out non-serializable objects like modules, functions, etc.
        serializable_namespace = {}
        logger.error(f"About to iterate through namespace items")
        
        for key, value in namespace.items():
            if key.startswith('__'):
                continue  # Skip dunder variables
            
            logger.info(f"Processing {key}: {type(value)}")
            try:
                # Test if the object can be pickled
                test_result = pickle.dumps(value)
                serializable_namespace[key] = value
                logger.info(f"  ✓ Added {key} to serializable namespace")
            except Exception as pickle_error:
                logger.info(f"  ✗ Cannot pickle {key}: {pickle_error}")
                # Handle modules specially - store module name for re-import
                if hasattr(value, '__name__') and str(type(value)) == "<class 'module'>":
                    module_key = f"__module__{key}"
                    serializable_namespace[module_key] = value.__name__
                    logger.info(f"  ✓ Stored module {key} as {module_key} = {value.__name__}")
                else:
                    logger.info(f"  ✗ Skipping non-serializable object {key}")
                # Skip other non-serializable objects
                continue
        
        logger.info(f"Final serializable namespace: {list(serializable_namespace.keys())}")
        try:
            serialized_bytes = pickle.dumps(serializable_namespace)
            result = base64.b64encode(serialized_bytes).decode('utf-8')
            logger.info(f"Serialization successful, result length: {len(result)}")
            return result
        except Exception as pickle_err:
            logger.warning(f"Failed to pickle final namespace: {pickle_err}")
            logger.warning(f"Namespace contents: {serializable_namespace}")
            return ""
    except Exception as e:
        logger.warning(f"Failed to serialize namespace (outer): {e}")
        import traceback
        logger.warning(f"Traceback: {traceback.format_exc()}")
        return ""

async def deserialize_namespace(serialized_data: str) -> Dict[str, Any]:
    """Deserialize a base64-encoded string back to Python namespace"""
    try:
        if not serialized_data:
            return {}
        serialized_bytes = base64.b64decode(serialized_data.encode('utf-8'))
        namespace = pickle.loads(serialized_bytes)
        
        # Re-import modules that were stored as module names
        modules_to_import = {}
        keys_to_remove = []
        
        for key, value in namespace.items():
            if key.startswith('__module__'):
                original_key = key[10:]  # Remove '__module__' prefix
                module_name = value
                try:
                    # Re-import the module
                    imported_module = __import__(module_name)
                    modules_to_import[original_key] = imported_module
                    keys_to_remove.append(key)
                except ImportError:
                    logger.warning(f"Failed to re-import module {module_name}")
                    keys_to_remove.append(key)
        
        # Remove module name entries and add the actual modules
        for key in keys_to_remove:
            del namespace[key]
        namespace.update(modules_to_import)
        
        return namespace
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
    logger.error(f"ENTERING save_session_namespace with namespace keys: {list(namespace.keys())}")
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
environment = os.getenv("ENVIRONMENT", "development")
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:8080")
cors_origins = ["*"] if environment == "development" else cors_origins_env.split(",")

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
                    print(result)
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




class ThreadSafeStreamingStdout:
    """Thread-safe stdout that can stream output in real-time"""
    def __init__(self):
        self.buffer = []
        self.lock = threading.Lock()
        
    def write(self, text: str) -> int:
        if text:
            with self.lock:
                self.buffer.append(text)
        return len(text)
    
    def flush(self):
        pass
    
    def get_and_clear(self) -> str:
        """Get all output since last call and clear buffer"""
        with self.lock:
            if self.buffer:
                output = ''.join(self.buffer)
                self.buffer.clear()
                return output
            return ""


async def stream_python_execution(session_id: str, code: str) -> AsyncGenerator[str, None]:
    """Stream Python code execution with real-time output using threading"""
    logger.info(f"Starting streaming execution for session {session_id[:8]}...")
    
    # Verify session is configured for Python
    if not await verify_session_language(session_id):
        yield f"data: {json.dumps({'type': 'error', 'content': f'Session {session_id} is not configured for Python'})}\n\n"
        return
    
    # Validate input
    if not code.strip():
        yield f"data: {json.dumps({'type': 'error', 'content': 'Code cannot be empty'})}\n\n"
        return

    # Create thread-safe stdout capture
    streaming_stdout = ThreadSafeStreamingStdout()
    streaming_stderr = ThreadSafeStreamingStdout()
    execution_complete = threading.Event()
    execution_error = None

    # Get session namespace from session manager
    namespace = await get_session_namespace(session_id)

    def execute_python_code(namespace_dict):
        """Execute Python code in a separate thread"""
        nonlocal execution_error
        
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        try:
            sys.stdout = streaming_stdout
            sys.stderr = streaming_stderr
            
            code_stripped = code.strip()
            
            try:
                # Try to evaluate as expression first (for REPL-like behavior)
                try:
                    result = eval(code_stripped, namespace_dict)
                    # If eval succeeds and returns a value (not None), display it
                    if result is not None:
                        print(result)
                except SyntaxError:
                    # If eval fails, try exec (for statements like assignments, imports, etc.)
                    exec(code_stripped, namespace_dict)
                    
            except Exception as e:
                execution_error = e
                error_msg = str(e)
                # For tracebacks, format them nicely
                if hasattr(e, '__traceback__'):
                    import traceback
                    error_msg = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                
                print(error_msg, file=sys.stderr)
                
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            execution_complete.set()

    try:
        # Start execution in a separate thread
        execution_thread = threading.Thread(target=execute_python_code, args=(namespace,))
        execution_thread.start()
        
        # Stream output while execution is running
        while not execution_complete.is_set():
            # Check for new output
            new_output = streaming_stdout.get_and_clear()
            if new_output:
                yield f"data: {json.dumps({'type': 'output', 'content': new_output})}\n\n"
            
            new_error = streaming_stderr.get_and_clear()
            if new_error:
                yield f"data: {json.dumps({'type': 'error', 'content': new_error})}\n\n"
            
            # Small delay to allow streaming effect
            await asyncio.sleep(0.1)
        
        # Wait for thread to complete
        execution_thread.join(timeout=30)  # 30 second timeout
        
        # Get any final output
        final_output = streaming_stdout.get_and_clear()
        if final_output:
            yield f"data: {json.dumps({'type': 'output', 'content': final_output})}\n\n"
            
        final_error = streaming_stderr.get_and_clear()
        if final_error:
            yield f"data: {json.dumps({'type': 'error', 'content': final_error})}\n\n"
        
        # Save updated namespace back to session manager
        await save_session_namespace(session_id, namespace)
        
        # Send completion event
        return_code = 0 if execution_error is None else 1
        yield f"data: {json.dumps({'type': 'complete', 'returnCode': return_code})}\n\n"

    except Exception as e:
        logger.error(f"Streaming execution error in session {session_id[:8]}: {e}")
        yield f"data: {json.dumps({'type': 'error', 'content': f'Execution error: {str(e)}'})}\n\n"
        yield f"data: {json.dumps({'type': 'complete', 'returnCode': 1})}\n\n"

    # Notify session manager of activity
    await notify_session_manager(session_id)
    
    logger.info(f"Streaming execution completed for session {session_id[:8]}")


@app.post("/execute-stream/{session_id}")
async def execute_code_stream(
    request: CodeRequest, 
    session_id: str = Path(..., description="Session GUID")
):
    """Execute Python code with streaming output using Server-Sent Events"""
    logger.info(f"Starting streaming execution for session {session_id[:8]}...")
    
    return StreamingResponse(
        stream_python_execution(session_id, request.code),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
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
    backend_port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=backend_port,
        log_level="info"
    )
