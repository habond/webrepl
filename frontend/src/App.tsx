import './styles/index.css'
import './styles/terminal.css'
import './styles/session-switcher.css'
import './styles/admin.css'
import './styles/responsive.css'
import { useState } from 'react'
import { TerminalHeader } from '@/components/terminal/TerminalHeader'
import { Terminal } from '@/components/terminal/Terminal'
import { SessionSwitcher } from '@/components/navigation/SessionSwitcher'
import { useTerminal } from '@/hooks/useTerminal'
import { useCodeExecution } from '@/hooks/useCodeExecution'
import { useStreamingExecution } from '@/hooks/useStreamingExecution'
import { useSessionManager } from '@/hooks/useSessionManager'
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts'
import { useSessionSelection } from '@/hooks/useSessionSelection'
import { useCodeExecutionHandler } from '@/hooks/useCodeExecutionHandler'
import { NoActiveSession } from '@/components/ui/NoActiveSession'

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
  useSessionSelection({
    sessions,
    currentSessionId,
    setCurrentSessionId,
    hasInitialized,
    isSessionLoading
  })
  
  const {
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
  } = useTerminal(
    currentSessionId || '', 
    sessions.find(s => s.id === currentSessionId)?.language,
    sessions.find(s => s.id === currentSessionId)?.history?.map(entry => ({
      ...entry,
      timestamp: new Date(entry.timestamp),
    })),
  )

  const { isLoading: isRegularLoading, executeCode } = useCodeExecution(currentSessionId || '')
  const { isStreaming, executeCodeWithStreaming } = useStreamingExecution(currentSessionId || '')

  const isLoading = isRegularLoading

  const { handleExecute } = useCodeExecutionHandler({
    currentInput,
    clearInput,
    focusInput,
    executeCode,
    executeCodeWithStreaming,
    selectedLanguage,
    addEntry,
    updateEntry
  })

  // Session switching hotkeys
  useKeyboardShortcuts({
    sessions,
    currentSessionId: currentSessionId || '',
    setCurrentSessionId,
    focusInput
  })

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
              isStreaming={isStreaming}
              inputRef={inputRef}
              terminalRef={terminalRef}
              onTerminalClick={handleTerminalClick}
              onNavigateHistory={navigateHistory}
            />
          </>
        ) : (
          <NoActiveSession />
        )}
      </div>
    </div>
  )
}

export default App