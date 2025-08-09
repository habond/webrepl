import type { APIResponse, CodeRequest, TerminalEntry } from '@/types'
import { API_BASE_URL, API_TIMEOUT, ERROR_MESSAGES } from '@/config/constants'
import { log } from '@/utils/logger'

class REPLService {
  private async makeRequest(method: string, url: string, body?: any): Promise<Response> {
    const fullUrl = `${API_BASE_URL}${url}`
    log.apiRequest(method, fullUrl)
    
    const startTime = performance.now()
    
    try {
      const response = await fetch(fullUrl, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: AbortSignal.timeout(API_TIMEOUT),
      })
      
      const duration = performance.now() - startTime
      log.apiResponse(method, fullUrl, response.status, duration)
      
      return response
    } catch (error) {
      const duration = performance.now() - startTime
      log.error(`API request failed: ${method} ${fullUrl}`, error as Error, { duration })
      throw error
    }
  }

  async executeCode(language: string, code: string, sessionId: string): Promise<APIResponse> {
    log.session(sessionId, `Executing ${language} code`, { language, codeLength: code.length })
    
    try {
      const response = await this.makeRequest(
        'POST',
        `/${language}/execute/${sessionId}`,
        { code } as CodeRequest,
      )

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ 
          error: ERROR_MESSAGES.UNKNOWN_ERROR, 
        }))
        
        log.warn('Code execution failed', { 
          sessionId: sessionId.substring(0, 8),
          language,
          status: response.status,
          error: errorData.error,
        })
        
        throw new Error(errorData.error || ERROR_MESSAGES.UNKNOWN_ERROR)
      }

      const result = await response.json()
      
      log.session(sessionId, 'Code execution completed', {
        language,
        hasOutput: !!result.output,
        hasError: !!result.error,
        executionCount: result.sessionInfo?.execution_count,
      })
      
      return result
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        log.error('Request timeout', error, { sessionId: sessionId.substring(0, 8) })
        throw new Error('Request timed out')
      }
      
      log.error('Code execution error', error as Error, { 
        sessionId: sessionId.substring(0, 8),
        language, 
      })
      throw error
    }
  }

  async resetContext(language: string, sessionId: string): Promise<void> {
    log.session(sessionId, `Resetting ${language} context`, { language })
    
    try {
      const response = await this.makeRequest(
        'POST',
        `/${language}/reset/${sessionId}`,
      )
      
      if (!response.ok) {
        log.warn('Context reset failed', {
          sessionId: sessionId.substring(0, 8),
          language,
          status: response.status,
        })
      } else {
        log.session(sessionId, 'Context reset successful', { language })
      }
    } catch (error) {
      log.warn('Failed to reset backend state', {
        sessionId: sessionId.substring(0, 8),
        language,
        error: error instanceof Error ? error.message : 'Unknown error',
      })
      // Don't throw - reset failures shouldn't block the UI
    }
  }

  async getSessionInfo(sessionId: string): Promise<any> {
    try {
      // Try to get session info from any backend (they should be consistent)
      const response = await this.makeRequest('GET', '/python/sessions')
      
      if (response.ok) {
        const data = await response.json()
        return data.sessions?.[sessionId] || null
      }
    } catch (error) {
      log.debug('Failed to get session info', { 
        sessionId: sessionId.substring(0, 8),
        error: error instanceof Error ? error.message : 'Unknown error',
      })
    }
    
    return null
  }
}

export const replService = new REPLService()

class SessionHistoryService {
  private async makeRequest(method: string, url: string, body?: any): Promise<Response> {
    const fullUrl = `/api${url}` // Use session manager API
    
    try {
      const response = await fetch(fullUrl, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: AbortSignal.timeout(API_TIMEOUT),
      })
      
      return response
    } catch (error) {
      log.error(`Session API request failed: ${method} ${fullUrl}`, error as Error)
      throw error
    }
  }

  async addHistoryEntry(sessionId: string, entry: TerminalEntry): Promise<void> {
    const response = await this.makeRequest(
      'POST',
      `/sessions/${sessionId}/history`,
      { 
        entry: {
          ...entry,
          timestamp: entry.timestamp.toISOString(),
        }, 
      },
    )

    if (!response.ok) {
      throw new Error(`Failed to add history entry: ${response.statusText}`)
    }
  }

  async getSessionHistory(sessionId: string): Promise<TerminalEntry[]> {
    const response = await this.makeRequest('GET', `/sessions/${sessionId}/history`)
    
    if (!response.ok) {
      if (response.status === 404) {
        return [] // Session doesn't exist yet, return empty history
      }
      throw new Error(`Failed to get session history: ${response.statusText}`)
    }

    const data = await response.json()
    return data.history.map((entry: any) => ({
      ...entry,
      timestamp: new Date(entry.timestamp),
    }))
  }
}

export const sessionHistoryService = new SessionHistoryService()

// Export for testing
export { REPLService, SessionHistoryService }