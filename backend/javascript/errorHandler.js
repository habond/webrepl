/**
 * Standardized Error Handling for JavaScript REPL Backend
 * 
 * Provides consistent error responses and proper HTTP status codes.
 */

const ErrorType = {
  VALIDATION_ERROR: 'validation_error',
  EXECUTION_ERROR: 'execution_error',
  SESSION_ERROR: 'session_error',
  INTERNAL_ERROR: 'internal_error',
  TIMEOUT_ERROR: 'timeout_error'
}

class ErrorHandler {
  static handleValidationError(message, sessionId = null) {
    return {
      errorType: ErrorType.VALIDATION_ERROR,
      message,
      sessionId,
      timestamp: new Date().toISOString()
    }
  }

  static handleExecutionError(error, sessionId = null) {
    return {
      errorType: ErrorType.EXECUTION_ERROR,
      message: error.message || String(error),
      details: error.stack,
      sessionId,
      timestamp: new Date().toISOString()
    }
  }

  static handleSessionError(message, sessionId) {
    return {
      errorType: ErrorType.SESSION_ERROR,
      message,
      sessionId,
      timestamp: new Date().toISOString()
    }
  }

  static handleInternalError(error, sessionId = null) {
    return {
      errorType: ErrorType.INTERNAL_ERROR,
      message: 'Internal server error occurred',
      details: error.message || String(error),
      sessionId,
      timestamp: new Date().toISOString()
    }
  }

  static formatExecutionResult(output = '', error = null, sessionId = null, sessionInfo = null) {
    const result = {
      output,
      error: null,
      errorType: null,
      sessionInfo
    }

    if (error) {
      const errorResponse = this.handleExecutionError(error, sessionId)
      result.error = errorResponse.message
      result.errorType = errorResponse.errorType
    }

    return result
  }

  static getHttpStatusForErrorType(errorType) {
    const statusMap = {
      [ErrorType.VALIDATION_ERROR]: 400,
      [ErrorType.EXECUTION_ERROR]: 200, // Execution errors are expected, return 200
      [ErrorType.SESSION_ERROR]: 404,
      [ErrorType.INTERNAL_ERROR]: 500,
      [ErrorType.TIMEOUT_ERROR]: 408
    }
    return statusMap[errorType] || 500
  }
}

module.exports = {
  ErrorHandler,
  ErrorType
}