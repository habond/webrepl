import type { Language } from '@/types'

interface TerminalInputProps {
  value: string
  onChange: (value: string) => void
  onExecute: () => void
  selectedLanguage: Language
  disabled?: boolean
  inputRef: React.RefObject<HTMLInputElement | null>
  onNavigateHistory: (direction: 'up' | 'down') => void
}

export const TerminalInput = ({ 
  value, 
  onChange, 
  onExecute, 
  selectedLanguage, 
  disabled = false, 
  inputRef,
  onNavigateHistory 
}: TerminalInputProps) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      onExecute()
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      onNavigateHistory('up')
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      onNavigateHistory('down')
    }
  }

  return (
    <div className="terminal-line input-line">
      <span className="prompt">{selectedLanguage.prompt}</span>
      <input
        ref={inputRef}
        type="text"
        className="terminal-input"
        value={value}
        onChange={e => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        autoComplete="off"
        spellCheck={false}
      />
    </div>
  )
}