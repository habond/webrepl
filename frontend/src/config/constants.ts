/**
 * Shared constants and configuration for the WebREPL frontend
 */

// API Configuration
export const API_BASE_URL = '/api'
export const API_TIMEOUT = 10000 // 10 seconds

// Session Configuration
export const SESSION_STORAGE_KEY = 'webrepl_session'
export const SESSION_TIMEOUT = 2 * 60 * 60 * 1000 // 2 hours in milliseconds

// UI Constants
export const MAX_TERMINAL_HISTORY = 1000
export const AUTO_SCROLL_THRESHOLD = 100

// Error Messages
export const ERROR_MESSAGES = {
  CONNECTION_FAILED: 'Failed to connect to server',
  INVALID_CODE: 'Code cannot be empty',
  SESSION_EXPIRED: 'Session has expired',
  NETWORK_ERROR: 'Network error occurred',
  UNKNOWN_ERROR: 'An unexpected error occurred',
} as const

// Success Messages
export const SUCCESS_MESSAGES = {
  CODE_EXECUTED: 'Code executed successfully',
  SESSION_RESET: 'Session reset successfully',
  LANGUAGE_SWITCHED: 'Language switched successfully',
} as const

// Theme Configuration
export const THEME = {
  colors: {
    background: '#000000',
    text: '#00ff00',
    error: '#ff0040',
    warning: '#ffaa00',
    info: '#00aaff',
    success: '#00ff00',
  },
  fonts: {
    monospace: '"Fira Code", "Monaco", "Consolas", monospace',
  },
} as const

// Development Configuration
export const DEV_CONFIG = {
  enableDebugLogs: process.env.NODE_ENV === 'development',
  showSessionInfo: process.env.NODE_ENV === 'development',
  enablePerformanceMetrics: process.env.NODE_ENV === 'development',
} as const

// Export types for type safety
export type ErrorMessage = keyof typeof ERROR_MESSAGES
export type SuccessMessage = keyof typeof SUCCESS_MESSAGES