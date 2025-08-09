const express = require('express')
const cors = require('cors')
const vm = require('vm')
const axios = require('axios')
const { ErrorHandler, ErrorType } = require('./errorHandler')

const app = express()
const port = 8000

// Session Manager URL
const SESSION_MANAGER_URL = 'http://session-manager:8000'

// Configure logging
console.log('Starting JavaScript REPL API v2.0.0...')

// CORS configuration - allow all origins in development
const corsOrigins = process.env.ENVIRONMENT === 'production' 
  ? ['http://localhost:8080'] 
  : ['*']

app.use(cors({
  origin: corsOrigins
}))

app.use(express.json())

// VM Context serialization functions
function serializeContext(vmContext) {
  try {
    // Extract serializable properties from the VM context
    const serializable = {}
    
    for (const key in vmContext) {
      if (key === 'console' || key.startsWith('_')) continue // Skip console and internal props
      
      const value = vmContext[key]
      if (typeof value === 'function') {
        serializable[key] = { __type: 'function', __source: value.toString() }
      } else if (typeof value === 'object' && value !== null) {
        try {
          JSON.stringify(value) // Test if serializable
          serializable[key] = value
        } catch (e) {
          // Skip non-serializable objects
        }
      } else {
        serializable[key] = value
      }
    }
    
    const serializedData = JSON.stringify(serializable)
    return Buffer.from(serializedData).toString('base64')
  } catch (error) {
    console.warn('Failed to serialize context:', error)
    return ''
  }
}

function deserializeContext(serializedData) {
  try {
    if (!serializedData) return createFreshContext()
    
    const jsonData = Buffer.from(serializedData, 'base64').toString('utf-8')
    const serializable = JSON.parse(jsonData)
    
    const context = createFreshContext()
    
    // Restore serialized properties
    for (const [key, value] of Object.entries(serializable)) {
      if (typeof value === 'object' && value !== null && value.__type === 'function') {
        try {
          // Restore function from source
          context[key] = vm.runInContext(`(${value.__source})`, context)
        } catch (e) {
          console.warn(`Failed to restore function ${key}:`, e)
        }
      } else {
        context[key] = value
      }
    }
    
    return context
  } catch (error) {
    console.warn('Failed to deserialize context:', error)
    return createFreshContext()
  }
}

function createFreshContext() {
  const context = {
    console: {
      log: (...args) => {
        context._output += args.map(arg => 
          typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
        ).join(' ') + '\n'
      },
      error: (...args) => {
        context._error += args.map(arg => 
          typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
        ).join(' ') + '\n'
      }
    },
    _output: '',
    _error: ''
  }
  return vm.createContext(context)
}

// Session management functions
async function getSessionContext(sessionId) {
  try {
    const response = await axios.get(`${SESSION_MANAGER_URL}/sessions/${sessionId}/environment`)
    if (response.status === 200 && response.data.environment?.serialized_data) {
      return deserializeContext(response.data.environment.serialized_data)
    }
    return createFreshContext()
  } catch (error) {
    console.warn('Failed to get session environment:', error)
    return createFreshContext()
  }
}

async function saveSessionContext(sessionId, vmContext) {
  try {
    const serializedData = serializeContext(vmContext)
    await axios.put(`${SESSION_MANAGER_URL}/sessions/${sessionId}/environment`, {
      language: 'javascript',
      serialized_data: serializedData
    })
  } catch (error) {
    console.warn('Failed to save session environment:', error)
  }
}

async function verifySessionLanguage(sessionId) {
  try {
    const response = await axios.get(`${SESSION_MANAGER_URL}/sessions/${sessionId}`)
    return response.status === 200 && response.data.language === 'javascript'
  } catch (error) {
    console.warn('Failed to verify session language:', error)
    return false
  }
}

async function notifySessionManager(sessionId) {
  try {
    await axios.put(`${SESSION_MANAGER_URL}/sessions/${sessionId}/activity?language=javascript`)
  } catch (error) {
    console.warn('Failed to notify session manager:', error)
  }
}

// Enhanced health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    language: 'javascript',
    version: '2.0.0',
    stateless: true,  // Now stateless!
    timestamp: new Date().toISOString()
  })
})

// Remove old function as it's now handled by sessionManager

// Execute JavaScript code endpoint
app.post('/execute/:sessionId', async (req, res) => {
  const { sessionId } = req.params
  console.log(`Executing code for session ${sessionId.substring(0, 8)}...`)
  
  try {
    // Verify session is configured for JavaScript
    if (!await verifySessionLanguage(sessionId)) {
      return res.status(400).json({
        output: '',
        error: `Session ${sessionId} is not configured for JavaScript`,
        errorType: 'session_error'
      })
    }

    const { code } = req.body
    
    // Validate input
    if (!code || typeof code !== 'string') {
      const errorResponse = ErrorHandler.handleValidationError(
        'Code parameter is required and must be a string',
        sessionId
      )
      return res.status(ErrorHandler.getHttpStatusForErrorType(errorResponse.errorType))
        .json({
          output: '',
          error: errorResponse.message,
          errorType: errorResponse.errorType
        })
    }

    // Get session-specific context from session manager
    const vmContext = await getSessionContext(sessionId)

    // Reset output collectors
    vmContext._output = ''
    vmContext._error = ''

    let result = undefined
    let executionError = null

    try {
      // Execute code in persistent VM context
      result = vm.runInContext(code, vmContext, {
        timeout: 5000, // 5 second timeout
        displayErrors: true
      })

      // If there's a result and no console output, show the result
      let output = vmContext._output
      if (result !== undefined && !output.trim()) {
        output = String(result) + '\n'
      }

      // Save updated context back to session manager
      await saveSessionContext(sessionId, vmContext)
      
      // Notify session manager of activity
      await notifySessionManager(sessionId)
      
      // Session info will come from session manager - we don't track it locally anymore
      const sessionData = null

      // Format result using error handler
      const formattedResult = ErrorHandler.formatExecutionResult(
        output || '',
        vmContext._error ? new Error(vmContext._error) : null,
        sessionId,
        sessionData
      )

      res.json({
        output: formattedResult.output,
        error: formattedResult.error,
        errorType: formattedResult.errorType,
        sessionInfo: formattedResult.sessionInfo
      })

    } catch (err) {
      executionError = err
      console.warn(`Execution error in session ${sessionId.substring(0, 8)}: ${err.message}`)
      
      // Save context even on error to preserve partial state
      await saveSessionContext(sessionId, vmContext)
      await notifySessionManager(sessionId)
      
      // Session info will come from session manager - we don't track it locally anymore
      const sessionData = null

      const formattedResult = ErrorHandler.formatExecutionResult(
        vmContext._output || '',
        executionError,
        sessionId,
        sessionData
      )

      res.json({
        output: formattedResult.output,
        error: formattedResult.error,
        errorType: formattedResult.errorType,
        sessionInfo: formattedResult.sessionInfo
      })
    }

  } catch (err) {
    console.error('Server error:', err)
    const errorResponse = ErrorHandler.handleInternalError(err, sessionId)
    res.status(ErrorHandler.getHttpStatusForErrorType(errorResponse.errorType))
      .json({
        output: '',
        error: errorResponse.message,
        errorType: errorResponse.errorType
      })
  }
})

// Reset execution context endpoint
app.post('/reset/:sessionId', async (req, res) => {
  const { sessionId } = req.params
  console.log(`Resetting session ${sessionId.substring(0, 8)}...`)
  
  try {
    // Clear environment in session manager
    const response = await axios.delete(`${SESSION_MANAGER_URL}/sessions/${sessionId}/environment`)
    if (response.status === 200) {
      res.json({ 
        message: 'Context reset successfully',
        sessionId: sessionId
      })
    } else if (response.status === 404) {
      const errorResponse = ErrorHandler.handleSessionError(
        `Session ${sessionId} not found`,
        sessionId
      )
      res.status(ErrorHandler.getHttpStatusForErrorType(errorResponse.errorType))
        .json({
          error: errorResponse.message,
          errorType: errorResponse.errorType
        })
    }
  } catch (err) {
    console.error('Reset error:', err)
    if (err.response?.status === 404) {
      const errorResponse = ErrorHandler.handleSessionError(
        `Session ${sessionId} not found`,
        sessionId
      )
      res.status(ErrorHandler.getHttpStatusForErrorType(errorResponse.errorType))
        .json({
          error: errorResponse.message,
          errorType: errorResponse.errorType
        })
    } else {
      const errorResponse = ErrorHandler.handleInternalError(err, sessionId)
      res.status(ErrorHandler.getHttpStatusForErrorType(errorResponse.errorType))
        .json({
          error: errorResponse.message,
          errorType: errorResponse.errorType
        })
    }
  }
})

// Session management is now handled by the central session manager service

// Start server
app.listen(port, '0.0.0.0', () => {
  console.log(`JavaScript REPL backend v2.0.0 running on port ${port}`)
})

// Graceful shutdown
function shutdown() {
  console.log('Shutting down JavaScript REPL backend...')
  process.exit(0)
}

process.on('SIGTERM', shutdown)
process.on('SIGINT', shutdown)