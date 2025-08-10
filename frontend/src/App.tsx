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
    renameSession,
  } = useSessionManager()
  
  // Handle session management - select most recent session when available
  useEffect(() => {
    const handleSessionManagement = async () => {
      // Only act after initial session fetch is complete
      if (!hasInitialized || isSessionLoading) return
      
      if (sessions.length === 0) {
        // No sessions exist - clear current session and let user create one
        setCurrentSessionId(undefined)
      } else if (!currentSessionId) {
        // No current session selected - select most recent session
        const mostRecent = sessions.sort(
          (a, b) => new Date(b.last_accessed).getTime() - new Date(a.last_accessed).getTime(),
        )[0]
        setCurrentSessionId(mostRecent.id)
      } else {
        // Verify current session still exists
        const sessionExists = sessions.some(s => s.id === currentSessionId)
        if (!sessionExists) {
          // Current session was deleted - select most recent session or clear if none exist
          const mostRecent = sessions.sort(
            (a, b) => new Date(b.last_accessed).getTime() - new Date(a.last_accessed).getTime(),
          )[0]
          setCurrentSessionId(mostRecent?.id || undefined)
        }
      }
    }

    handleSessionManagement()
  }, [sessions, hasInitialized, isSessionLoading, currentSessionId])
  
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
    navigateHistory,
  } = useTerminal(
    currentSessionId || '', 
    sessions.find(s => s.id === currentSessionId)?.language,
    sessions.find(s => s.id === currentSessionId)?.history?.map(entry => ({
      ...entry,
      timestamp: new Date(entry.timestamp),
    })),
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
        {currentSessionId ? (
          <>
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
          </>
        ) : (
          <div className="no-session-message">
            <div className="message-content">
              <h2>No Active Session</h2>
              <p>Create a session from the sidebar to start coding</p>
              <div className="arrow-indicator">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M7 17l5-5-5-5M12 19h7" />
                </svg>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App