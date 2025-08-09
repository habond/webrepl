/**
 * Session Management Module for JavaScript REPL Backend
 * 
 * Provides centralized session handling with metadata, cleanup, and monitoring.
 */

const vm = require('vm')

class SessionMetadata {
  constructor(sessionId) {
    this.sessionId = sessionId
    this.createdAt = new Date()
    this.lastAccessed = new Date()
    this.executionCount = 0
    this.contextSize = 0
  }

  updateAccess() {
    this.lastAccessed = new Date()
  }

  incrementExecution() {
    this.executionCount++
    this.updateAccess()
  }

  toJSON() {
    return {
      sessionId: this.sessionId,
      createdAt: this.createdAt.toISOString(),
      lastAccessed: this.lastAccessed.toISOString(),
      executionCount: this.executionCount,
      contextSize: this.contextSize
    }
  }
}

class SessionManager {
  constructor(cleanupInterval = 3600000, sessionTimeout = 7200000) { // milliseconds
    this.sessions = new Map()
    this.metadata = new Map()
    this.cleanupInterval = cleanupInterval
    this.sessionTimeout = sessionTimeout
    this.cleanupTimer = null
    
    // Start cleanup timer
    this.startCleanupTimer()
  }

  createFreshContext() {
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

  getSessionContext(sessionId) {
    if (!this.sessions.has(sessionId)) {
      this.sessions.set(sessionId, this.createFreshContext())
      this.metadata.set(sessionId, new SessionMetadata(sessionId))
    }

    // Update metadata
    const metadata = this.metadata.get(sessionId)
    metadata.updateAccess()
    metadata.contextSize = Object.keys(this.sessions.get(sessionId)).length

    return this.sessions.get(sessionId)
  }

  resetSession(sessionId) {
    if (this.sessions.has(sessionId)) {
      this.sessions.set(sessionId, this.createFreshContext())
      const metadata = this.metadata.get(sessionId)
      metadata.updateAccess()
      metadata.contextSize = 0
      return true
    }
    return false
  }

  deleteSession(sessionId) {
    const deleted = this.sessions.delete(sessionId) && this.metadata.delete(sessionId)
    return deleted
  }

  recordExecution(sessionId) {
    const metadata = this.metadata.get(sessionId)
    if (metadata) {
      metadata.incrementExecution()
    }
  }

  getSessionInfo(sessionId) {
    return this.metadata.get(sessionId)
  }

  getAllSessions() {
    return Object.fromEntries(this.metadata)
  }

  getSessionCount() {
    return this.sessions.size
  }

  cleanupExpiredSessions() {
    const now = Date.now()
    const expiredSessions = []

    for (const [sessionId, metadata] of this.metadata) {
      if (now - metadata.lastAccessed.getTime() > this.sessionTimeout) {
        expiredSessions.push(sessionId)
      }
    }

    for (const sessionId of expiredSessions) {
      this.deleteSession(sessionId)
    }

    return expiredSessions.length
  }

  startCleanupTimer() {
    this.cleanupTimer = setInterval(() => {
      try {
        const removed = this.cleanupExpiredSessions()
        if (removed > 0) {
          console.log(`Cleaned up ${removed} expired sessions`)
        }
      } catch (error) {
        console.error('Error during session cleanup:', error)
      }
    }, this.cleanupInterval)
  }

  shutdown() {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer)
      this.cleanupTimer = null
    }
  }
}

// Export singleton instance
module.exports = new SessionManager()