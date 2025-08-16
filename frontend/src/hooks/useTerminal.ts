import { useState, useRef, useEffect, useCallback } from 'react'
import { AVAILABLE_LANGUAGES } from '@/config/languages'
import { sessionHistoryService } from '@/services/api'
import type { TerminalEntry, Language } from '@/types'

// Per-session terminal state
interface SessionState {
  history: TerminalEntry[]
  selectedLanguage: Language
  currentInput: string
  commandHistory: string[]
  historyIndex: number
}

// Global session state storage (persisted across session switches)
const sessionStates = new Map<string, SessionState>()

// Global cleanup function for session deletion
export const cleanupSessionState = (sessionId: string) => {
  sessionStates.delete(sessionId)
}

const getDefaultSessionState = (language?: string): SessionState => ({
  history: [],
  selectedLanguage: AVAILABLE_LANGUAGES.find(lang => lang.id === language) || AVAILABLE_LANGUAGES[0],
  currentInput: '',
  commandHistory: [],
  historyIndex: -1,
})

export const useTerminal = (sessionId: string, sessionLanguage?: string, sessionHistory?: TerminalEntry[]) => {
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const terminalRef = useRef<HTMLDivElement>(null)
  const previousSessionId = useRef<string | null>(null)

  // Initialize session state
  const initializeSessionState = useCallback(() => {
    if (!sessionId) return getDefaultSessionState(sessionLanguage)
    
    if (!sessionStates.has(sessionId)) {
      sessionStates.set(sessionId, getDefaultSessionState(sessionLanguage))
    }
    return sessionStates.get(sessionId)!
  }, [sessionId, sessionLanguage])

  // Get current session state
  const getCurrentState = useCallback(() => {
    if (!sessionId) return getDefaultSessionState(sessionLanguage)
    return sessionStates.get(sessionId) || getDefaultSessionState(sessionLanguage)
  }, [sessionId, sessionLanguage])

  // Update session state
  const updateSessionState = useCallback((updates: Partial<SessionState>) => {
    if (!sessionId) return
    
    const currentState = getCurrentState()
    const newState = { ...currentState, ...updates }
    sessionStates.set(sessionId, newState)
  }, [sessionId, getCurrentState])

  const [sessionState, setSessionState] = useState<SessionState>(() => initializeSessionState())

  // Sync local state when sessionId changes
  useEffect(() => {
    const loadSessionHistory = () => {
      if (sessionId && previousSessionId.current !== sessionId) {
        // Use session history from database if available, otherwise create new
        if (!sessionStates.has(sessionId)) {
          const defaultState = getDefaultSessionState(sessionLanguage)
          // If we have session history from database, use it
          if (sessionHistory && sessionHistory.length > 0) {
            defaultState.history = sessionHistory
            
            // Extract command history from persisted terminal entries
            const commandHistory: string[] = []
            sessionHistory.forEach(entry => {
              if (entry.type === 'input' && entry.content.trim()) {
                // Don't add duplicate consecutive commands
                const lastCommand = commandHistory[commandHistory.length - 1]
                if (lastCommand !== entry.content.trim()) {
                  commandHistory.push(entry.content.trim())
                }
              }
            })
            defaultState.commandHistory = commandHistory
          }
          sessionStates.set(sessionId, defaultState)
          setSessionState(defaultState)
        } else {
          setSessionState(sessionStates.get(sessionId)!)
        }
        previousSessionId.current = sessionId
      }
    }

    loadSessionHistory()
  }, [sessionId, sessionLanguage, sessionHistory])

  // Getters for current session data
  const currentInput = sessionState.currentInput
  const history = sessionState.history
  const selectedLanguage = sessionState.selectedLanguage


  useEffect(() => {
    // Auto-focus input and scroll to bottom
    // Use setTimeout to ensure DOM has updated
    const timer = setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus()
      }
      if (terminalRef.current) {
        terminalRef.current.scrollTop = terminalRef.current.scrollHeight
      }
    }, 0)
    
    return () => clearTimeout(timer)
  }, [history])

  // Focus input after operations complete (for external control)
  const focusInput = useCallback(() => {
    const timer = setTimeout(() => {
      if (inputRef.current && !inputRef.current.disabled) {
        inputRef.current.focus()
      }
    }, 0)
    return () => clearTimeout(timer)
  }, [])


  // Session-aware state updaters
  const setCurrentInput = useCallback((input: string | ((prev: string) => string)) => {
    const newInput = typeof input === 'function' ? input(currentInput) : input
    updateSessionState({ currentInput: newInput })
    setSessionState(prev => ({ ...prev, currentInput: newInput }))
  }, [currentInput, sessionId, updateSessionState])

  const addEntry = useCallback((entry: TerminalEntry) => {
    // Get the current history dynamically to avoid stale closure issues
    const currentState = getCurrentState()
    const newHistory = [...currentState.history, entry]
    
    // If this is an input entry, add to command history (only non-empty commands)
    let newCommandHistory = currentState.commandHistory
    if (entry.type === 'input' && entry.content.trim()) {
      // Don't add duplicate consecutive commands
      const lastCommand = newCommandHistory[newCommandHistory.length - 1]
      if (lastCommand !== entry.content.trim()) {
        newCommandHistory = [...newCommandHistory, entry.content.trim()]
      }
    }
    
    updateSessionState({ 
      history: newHistory, 
      commandHistory: newCommandHistory,
      historyIndex: -1, // Reset history index when new command is added
    })
    setSessionState(prev => ({ 
      ...prev, 
      history: newHistory, 
      commandHistory: newCommandHistory,
      historyIndex: -1, 
    }))

    // Save to session manager (with fixed JSON column handling)
    if (sessionId) {
      sessionHistoryService.addHistoryEntry(sessionId, entry).catch(error => {
        console.error('Failed to save history entry to session manager:', error)
        // Continue with local state even if server save fails
      })
    }
  }, [sessionId, getCurrentState, updateSessionState])

  const updateEntry = useCallback((entryId: string, newContent: string) => {
    const currentState = getCurrentState()
    const newHistory = currentState.history.map(entry => 
      entry.id === entryId ? { ...entry, content: newContent } : entry
    )
    
    updateSessionState({ history: newHistory })
    setSessionState(prev => ({ ...prev, history: newHistory }))

    // Save updated entry to session manager
    if (sessionId) {
      sessionHistoryService.updateHistoryEntry(sessionId, entryId, newContent).catch(error => {
        console.error('Failed to update history entry in session manager:', error)
        // Continue with local state even if server save fails
      })
    }
  }, [sessionId, getCurrentState, updateSessionState])

  const clearInput = useCallback(() => {
    setCurrentInput('')
  }, [setCurrentInput])

  // Command history navigation functions
  const navigateHistory = useCallback((direction: 'up' | 'down') => {
    const currentState = getCurrentState()
    const { commandHistory, historyIndex } = currentState

    if (commandHistory.length === 0) return

    let newIndex: number
    
    if (direction === 'up') {
      // Move backwards in history (older commands)
      if (historyIndex === -1) {
        // First time pressing up - go to most recent command
        newIndex = commandHistory.length - 1
      } else if (historyIndex > 0) {
        // Go to previous command
        newIndex = historyIndex - 1
      } else {
        // Already at oldest command, stay there
        newIndex = historyIndex
      }
    } else {
      // Move forwards in history (newer commands)
      if (historyIndex === -1 || historyIndex >= commandHistory.length - 1) {
        // Already at newest or not in history mode, clear input
        updateSessionState({ currentInput: '', historyIndex: -1 })
        setSessionState(prev => ({ ...prev, currentInput: '', historyIndex: -1 }))
        return
      } else {
        // Go to next command
        newIndex = historyIndex + 1
      }
    }

    const command = commandHistory[newIndex]
    updateSessionState({ currentInput: command, historyIndex: newIndex })
    setSessionState(prev => ({ ...prev, currentInput: command, historyIndex: newIndex }))
  }, [getCurrentState, updateSessionState])


  const handleTerminalClick = useCallback((e: React.MouseEvent, isLoading: boolean) => {
    // Don't focus if user is trying to select text or clicking on interactive elements
    const target = e.target as HTMLElement
    const isSelectableText = target.tagName === 'PRE' || target.classList.contains('terminal-text')
    const isInteractiveElement = target.tagName === 'SELECT' || target.tagName === 'OPTION' || target.tagName === 'LABEL'
    
    if (!isSelectableText && !isInteractiveElement && inputRef.current && !isLoading) {
      inputRef.current.focus()
    }
  }, [])

  return {
    currentInput,
    setCurrentInput,
    history,
    selectedLanguage,
    inputRef,
    terminalRef,
    addEntry,
    updateEntry,
    clearInput,
    focusInput,
    handleTerminalClick,
    navigateHistory,
  }
}