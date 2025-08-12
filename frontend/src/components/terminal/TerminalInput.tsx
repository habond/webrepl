import type { Language } from '@/types'

interface TerminalInputProps {
  value: string
  onChange: (value: string) => void
  onExecute: () => void
  selectedLanguage: Language
  disabled?: boolean
  inputRef: React.RefObject<HTMLTextAreaElement | null>
  onNavigateHistory: (direction: 'up' | 'down') => void
}

export const TerminalInput = ({ 
  value, 
  onChange, 
  onExecute, 
  selectedLanguage, 
  disabled = false, 
  inputRef,
  onNavigateHistory, 
}: TerminalInputProps) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        // Shift+Enter: Allow new line (default behavior)
        return
      } else {
        // Enter: Execute code
        e.preventDefault()
        onExecute()
      }
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
      <textarea
        ref={inputRef}
        className="terminal-input"
        value={value}
        onChange={e => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        autoComplete="off"
        spellCheck={false}
        rows={1}
        style={{
          resize: 'none',
          overflow: 'hidden',
        }}
        onInput={(e) => {
          // Auto-resize textarea based on content
          const target = e.target as HTMLTextAreaElement
          target.style.height = 'auto'
          target.style.height = `${target.scrollHeight}px`
        }}
      />
    </div>
  )
}