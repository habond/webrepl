import { useTheme } from '@/contexts/ThemeContext'
import './ThemeToggle.css'

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()
  
  return (
    <button
      className="theme-toggle"
      onClick={toggleTheme}
      title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
    >
      <div className="theme-toggle-track">
        <div className="theme-toggle-thumb" />
        <div className="theme-icons">
          <span className="sun-icon" role="img" aria-label="Light theme">☀️</span>
          <span className="moon-icon" role="img" aria-label="Dark theme">🌙</span>
        </div>
      </div>
    </button>
  )
}