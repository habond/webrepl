import { Link } from 'react-router-dom'
import { ThemeToggle } from '@/components/ui/ThemeToggle'

export const TerminalHeader = () => {
  return (
    <div className="terminal-header">
      <span className="terminal-title">REPL Terminal</span>
      <div className="terminal-header-controls">
        <ThemeToggle />
        <Link to="/admin" className="admin-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2a10 10 0 1 0 10 10 4 4 0 0 1-5-5 4 4 0 0 1-5-5"/>
            <path d="M9 9a3 3 0 1 1 6 0"/>
          </svg>
          Admin
        </Link>
      </div>
    </div>
  )
}