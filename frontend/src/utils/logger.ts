/**
 * Structured logging utility for development and debugging
 */

import { DEV_CONFIG } from '@/config/constants'

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3
}

interface LogContext {
  sessionId?: string
  component?: string
  action?: string
  duration?: number
  [key: string]: any
}

class Logger {
  private level: LogLevel = DEV_CONFIG.enableDebugLogs ? LogLevel.DEBUG : LogLevel.INFO

  private formatMessage(level: LogLevel, message: string, context?: LogContext): string {
    const timestamp = new Date().toISOString()
    const levelName = LogLevel[level]
    const contextStr = context ? JSON.stringify(context) : ''
    
    return `[${timestamp}] [${levelName}] ${message} ${contextStr}`.trim()
  }

  private shouldLog(level: LogLevel): boolean {
    return level >= this.level
  }

  debug(message: string, context?: LogContext): void {
    if (this.shouldLog(LogLevel.DEBUG)) {
      console.debug(this.formatMessage(LogLevel.DEBUG, message, context))
    }
  }

  info(message: string, context?: LogContext): void {
    if (this.shouldLog(LogLevel.INFO)) {
      console.info(this.formatMessage(LogLevel.INFO, message, context))
    }
  }

  warn(message: string, context?: LogContext): void {
    if (this.shouldLog(LogLevel.WARN)) {
      console.warn(this.formatMessage(LogLevel.WARN, message, context))
    }
  }

  error(message: string, error?: Error, context?: LogContext): void {
    if (this.shouldLog(LogLevel.ERROR)) {
      const errorContext = error ? { ...context, error: error.message, stack: error.stack } : context
      console.error(this.formatMessage(LogLevel.ERROR, message, errorContext))
    }
  }

  // Performance logging
  time(label: string): void {
    if (DEV_CONFIG.enablePerformanceMetrics) {
      console.time(label)
    }
  }

  timeEnd(label: string): void {
    if (DEV_CONFIG.enablePerformanceMetrics) {
      console.timeEnd(label)
    }
  }

  // Session-specific logging
  session(sessionId: string, message: string, context?: LogContext): void {
    this.info(message, { ...context, sessionId: sessionId.substring(0, 8) })
  }

  // API request logging
  apiRequest(method: string, url: string, sessionId?: string): void {
    this.debug(`API Request: ${method} ${url}`, { 
      method, 
      url, 
      sessionId: sessionId?.substring(0, 8), 
    })
  }

  apiResponse(method: string, url: string, status: number, duration: number, sessionId?: string): void {
    const level = status >= 400 ? LogLevel.WARN : LogLevel.DEBUG
    const message = `API Response: ${method} ${url} - ${status}`
    
    if (level === LogLevel.WARN) {
      this.warn(message, { method, url, status, duration, sessionId: sessionId?.substring(0, 8) })
    } else {
      this.debug(message, { method, url, status, duration, sessionId: sessionId?.substring(0, 8) })
    }
  }

  // Component lifecycle logging
  componentMount(componentName: string, props?: any): void {
    this.debug(`Component mounted: ${componentName}`, { component: componentName, props })
  }

  componentUnmount(componentName: string): void {
    this.debug(`Component unmounted: ${componentName}`, { component: componentName })
  }

  // User action logging
  userAction(action: string, context?: LogContext): void {
    this.info(`User action: ${action}`, { ...context, action })
  }
}

// Export singleton instance
export const logger = new Logger()

// Export convenience functions
export const log = {
  debug: logger.debug.bind(logger),
  info: logger.info.bind(logger),
  warn: logger.warn.bind(logger),
  error: logger.error.bind(logger),
  session: logger.session.bind(logger),
  apiRequest: logger.apiRequest.bind(logger),
  apiResponse: logger.apiResponse.bind(logger),
  componentMount: logger.componentMount.bind(logger),
  componentUnmount: logger.componentUnmount.bind(logger),
  userAction: logger.userAction.bind(logger),
  time: logger.time.bind(logger),
  timeEnd: logger.timeEnd.bind(logger),
}