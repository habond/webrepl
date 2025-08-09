import './styles/index.css'
import './styles/terminal.css'
import './styles/session-switcher.css'
import './styles/admin.css'
import './styles/responsive.css'
import { useEffect, useState } from 'react'
import { TerminalHeader } from '@/components/terminal/TerminalHeader'
import { Terminal } from '@/components/terminal/Terminal'
import { SessionSwitcher } from '@/components/navigation/SessionSwitcher'
import { useTerminal } from '@/hooks/useTerminal'
import { useCodeExecution } from '@/hooks/useCodeExecution'
import { useSessionManager } from '@/hooks/useSessionManager'

function App() {
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(undefined)
  
  const {
    sessions,
    isLoading: isSessionLoading,
    hasInitialized,
    createSession,
    deleteSession,
    renameSession
  } = useSessionManager()
  
  // Handle session management - create default session or select most recent session
  useEffect(() => {
    const handleSessionManagement = async () => {
      // Only act after initial session fetch is complete
      if (!hasInitialized || isSessionLoading) return
      
      if (sessions.length === 0) {
        // No sessions exist at all - create a default session
        try {
          const newSession = await createSession('Default Session')
          if (newSession) {
            setCurrentSessionId(newSession.id)
          }
        } catch (error) {
          console.error('Failed to create default session:', error)
        }
      } else if (!currentSessionId) {
        // No current session selected - select most recent session
        const mostRecent = sessions.sort(
          (a, b) => new Date(b.last_accessed).getTime() - new Date(a.last_accessed).getTime()
        )[0]
        setCurrentSessionId(mostRecent.id)
      } else {
        // Verify current session still exists
        const sessionExists = sessions.some(s => s.id === currentSessionId)
        if (!sessionExists) {
          // Current session was deleted - select most recent session
          const mostRecent = sessions.sort(
            (a, b) => new Date(b.last_accessed).getTime() - new Date(a.last_accessed).getTime()
          )[0]
          setCurrentSessionId(mostRecent?.id || undefined)
        }
      }
    }

    handleSessionManagement()
  }, [sessions, hasInitialized, isSessionLoading, currentSessionId, createSession])
  
  const {
    currentInput,
    setCurrentInput,
    history,
    selectedLanguage,
    inputRef,
    terminalRef,
    addEntry,
    clearInput,
    focusInput,
    handleTerminalClick,
    navigateHistory
  } = useTerminal(
    currentSessionId || '', 
    sessions.find(s => s.id === currentSessionId)?.language,
    sessions.find(s => s.id === currentSessionId)?.history?.map(entry => ({
      ...entry,
      timestamp: new Date(entry.timestamp)
    }))
  )

  const { isLoading, executeCode } = useCodeExecution(currentSessionId || '')

  const handleExecute = async () => {
    const codeToExecute = currentInput
    clearInput() // Clear input immediately to prevent interference
    await executeCode(codeToExecute, selectedLanguage, addEntry)
    // Ensure input is focused after execution completes
    focusInput()
  }

  return (
    <div className="app-container">
      <SessionSwitcher
        sessions={sessions}
        currentSessionId={currentSessionId}
        onCreateSession={async (name, language) => {
          const newSession = await createSession(name, language)
          if (newSession) {
            setCurrentSessionId(newSession.id)
          }
          return newSession
        }}
        onDeleteSession={async (sessionId) => {
          await deleteSession(sessionId)
          // If we deleted the current session, clear the selection
          if (sessionId === currentSessionId) {
            setCurrentSessionId(undefined)
          }
        }}
        onRenameSession={renameSession}
        onSelectSession={setCurrentSessionId}
        isLoading={isSessionLoading}
      />
      
      <div className="terminal-container">
        <TerminalHeader />
        
        <Terminal
          history={history}
          currentInput={currentInput}
          onInputChange={setCurrentInput}
          onExecute={handleExecute}
          selectedLanguage={selectedLanguage}
          isLoading={isLoading}
          inputRef={inputRef}
          terminalRef={terminalRef}
          onTerminalClick={handleTerminalClick}
          onNavigateHistory={navigateHistory}
        />
      </div>
    </div>
  )
}

export default App