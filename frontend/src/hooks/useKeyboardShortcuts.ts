import { useCallback, useEffect } from 'react'
import type { SessionInfo } from '../types/session'

interface UseKeyboardShortcutsProps {
  sessions: SessionInfo[]
  currentSessionId: string | null
  setCurrentSessionId: (sessionId: string) => void
  focusInput: () => void
}

export const useKeyboardShortcuts = ({
  sessions,
  currentSessionId,
  setCurrentSessionId,
  focusInput
}: UseKeyboardShortcutsProps) => {
  const isMac = navigator.userAgent.includes('Mac')

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    const key = e.key
    const code = e.code
    const ctrlOrCmd = isMac ? e.metaKey : e.ctrlKey
    const altOrOption = e.altKey  // altKey works for both Option (Mac) and Alt (Windows/Linux)

    // Session switching hotkeys should work even when input is focused
    // The modifier keys (Cmd+Option or Ctrl+Alt) prevent interference with typing
    
    // Number keys for direct session access (Cmd+Option+1-9 on Mac, Ctrl+Alt+1-9 on Windows/Linux)
    // Use code property to detect physical keys (avoids issues with Option key producing special chars)
    if (ctrlOrCmd && altOrOption && !e.shiftKey && code.startsWith('Digit')) {
      e.preventDefault()
      // Extract number from code (e.g., 'Digit1' -> '1')
      const num = code.replace('Digit', '')
      const index = parseInt(num) - 1
      if (index >= 0 && index < sessions.length) {
        setCurrentSessionId(sessions[index].id)
        // Re-focus the input after switching sessions
        setTimeout(() => focusInput(), 50)
      }
    }
    // Previous/Next session with brackets (Cmd+Option+[/] on Mac, Ctrl+Alt+[/] on Windows/Linux)
    else if (ctrlOrCmd && altOrOption && (code === 'BracketLeft' || code === 'BracketRight' || key === '[' || key === ']')) {
      const currentIndex = sessions.findIndex(s => s.id === currentSessionId)
      
      if ((code === 'BracketLeft' || key === '[') && currentIndex > 0) {
        e.preventDefault()
        setCurrentSessionId(sessions[currentIndex - 1].id)
        // Re-focus the input after switching sessions
        setTimeout(() => focusInput(), 50)
      } else if ((code === 'BracketRight' || key === ']') && currentIndex < sessions.length - 1) {
        e.preventDefault()
        setCurrentSessionId(sessions[currentIndex + 1].id)
        // Re-focus the input after switching sessions
        setTimeout(() => focusInput(), 50)
      }
    }
  }, [sessions, currentSessionId, isMac, focusInput, setCurrentSessionId])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])
}