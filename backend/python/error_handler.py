"""
Standardized Error Handling for Python REPL Backend

Provides consistent error responses and proper HTTP status codes.
"""

import traceback
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel


class ErrorType(str, Enum):
    """Standardized error types"""
    VALIDATION_ERROR = "validation_error"
    EXECUTION_ERROR = "execution_error"
    SESSION_ERROR = "session_error"
    INTERNAL_ERROR = "internal_error"
    TIMEOUT_ERROR = "timeout_error"


class ErrorResponse(BaseModel):
    """Standardized error response format"""
    error_type: ErrorType
    message: str
    details: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[str] = None


class ExecutionResult(BaseModel):
    """Standardized execution result"""
    output: str = ""
    error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    session_info: Optional[Dict[str, Any]] = None


class ErrorHandler:
    """Centralized error handling with consistent responses"""
    
    @staticmethod
    def handle_validation_error(message: str, session_id: Optional[str] = None) -> ErrorResponse:
        """Handle validation errors (400)"""
        return ErrorResponse(
            error_type=ErrorType.VALIDATION_ERROR,
            message=message,
            session_id=session_id
        )
    
    @staticmethod
    def handle_execution_error(
        exception: Exception, 
        session_id: Optional[str] = None,
        include_traceback: bool = True
    ) -> ErrorResponse:
        """Handle code execution errors"""
        details = None
        if include_traceback:
            details = traceback.format_exc()
        
        return ErrorResponse(
            error_type=ErrorType.EXECUTION_ERROR,
            message=f"{type(exception).__name__}: {str(exception)}",
            details=details,
            session_id=session_id
        )
    
    @staticmethod
    def handle_session_error(message: str, session_id: str) -> ErrorResponse:
        """Handle session-related errors"""
        return ErrorResponse(
            error_type=ErrorType.SESSION_ERROR,
            message=message,
            session_id=session_id
        )
    
    @staticmethod
    def handle_internal_error(
        exception: Exception, 
        session_id: Optional[str] = None
    ) -> ErrorResponse:
        """Handle internal server errors (500)"""
        return ErrorResponse(
            error_type=ErrorType.INTERNAL_ERROR,
            message="Internal server error occurred",
            details=str(exception),
            session_id=session_id
        )
    
    @staticmethod
    def format_execution_result(
        output: str = "",
        error: Optional[Exception] = None,
        session_id: Optional[str] = None,
        session_info: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Format execution result with proper error handling"""
        result = ExecutionResult(output=output, session_info=session_info)
        
        if error:
            error_response = ErrorHandler.handle_execution_error(error, session_id)
            result.error = error_response.message
            result.error_type = error_response.error_type
        
        return result


def get_http_status_for_error_type(error_type: ErrorType) -> int:
    """Get appropriate HTTP status code for error type"""
    status_map = {
        ErrorType.VALIDATION_ERROR: 400,
        ErrorType.EXECUTION_ERROR: 200,  # Execution errors are expected, return 200
        ErrorType.SESSION_ERROR: 404,
        ErrorType.INTERNAL_ERROR: 500,
        ErrorType.TIMEOUT_ERROR: 408,
    }
    return status_map.get(error_type, 500)