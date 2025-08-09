import { TerminalLine } from '@/components/terminal/TerminalLine'
import { TerminalInput } from '@/components/terminal/TerminalInput'
import type { TerminalEntry, Language } from '@/types'

interface TerminalProps {
  history: TerminalEntry[]
  currentInput: string
  onInputChange: (value: string) => void
  onExecute: () => void
  selectedLanguage: Language
  isLoading: boolean
  inputRef: React.RefObject<HTMLInputElement | null>
  terminalRef: React.RefObject<HTMLDivElement | null>
  onTerminalClick: (e: React.MouseEvent, isLoading: boolean) => void
  onNavigateHistory: (direction: 'up' | 'down') => void
}

export const Terminal = ({ 
  history, 
  currentInput, 
  onInputChange, 
  onExecute, 
  selectedLanguage, 
  isLoading, 
  inputRef, 
  terminalRef, 
  onTerminalClick,
  onNavigateHistory 
}: TerminalProps) => {
  return (
    <div className="terminal" ref={terminalRef} onClick={(e) => onTerminalClick(e, isLoading)}>
      <div className="terminal-content">
        {history.length === 0 && (
          <div className="welcome-message">
            {selectedLanguage.name} Interactive Terminal
            <br />
            Type {selectedLanguage.name} commands and press Enter to execute.
          </div>
        )}
        
        {history.map(entry => (
          <TerminalLine 
            key={entry.id} 
            entry={entry} 
            selectedLanguage={selectedLanguage} 
          />
        ))}
        
        {isLoading && (
          <div className="terminal-line loading">
            <span className="loading-indicator">...</span>
          </div>
        )}
        
        <TerminalInput
          value={currentInput}
          onChange={onInputChange}
          onExecute={onExecute}
          selectedLanguage={selectedLanguage}
          disabled={isLoading}
          inputRef={inputRef}
          onNavigateHistory={onNavigateHistory}
        />
      </div>
    </div>
  )
}