import type { TerminalEntry, Language } from '@/types'

interface TerminalLineProps {
  entry: TerminalEntry
  selectedLanguage: Language
}

export const TerminalLine = ({ entry, selectedLanguage }: TerminalLineProps) => {
  return (
    <div key={entry.id} className={`terminal-line ${entry.type}`}>
      {entry.type === 'input' && <span className="prompt">{selectedLanguage.prompt}</span>}
      <pre className="terminal-text">{entry.content}</pre>
    </div>
  )
}