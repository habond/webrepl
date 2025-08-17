import { useState, useRef, useCallback, useEffect } from 'react'
import type { SessionInfo } from '@/types'
import { AVAILABLE_LANGUAGES } from '@/config/languages'

interface SessionSwitcherProps {
  sessions: SessionInfo[]
  currentSessionId: string | undefined
  onCreateSession: (name?: string, language?: string) => Promise<void>
  onDeleteSession: (sessionId: string) => Promise<void>
  onRenameSession: (sessionId: string, newName: string) => Promise<void>
  onSelectSession: (sessionId: string) => void
  isLoading: boolean
}

export const SessionSwitcher = ({ 
  sessions, 
  currentSessionId, 
  onCreateSession, 
  onDeleteSession,
  onRenameSession,
  onSelectSession,
  isLoading, 
}: SessionSwitcherProps) => {
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0
  const [expandedSessions, setExpandedSessions] = useState<Set<string>>(new Set())
  const [isCreating, setIsCreating] = useState(false)
  const [showLanguageMenu, setShowLanguageMenu] = useState(false)
  const [renamingSessionId, setRenamingSessionId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [isResizing, setIsResizing] = useState(false)
  const [width, setWidth] = useState(350)
  
  const sessionSwitcherRef = useRef<HTMLDivElement>(null)
  const resizeHandleRef = useRef<HTMLDivElement>(null)
  const languageMenuRef = useRef<HTMLDivElement>(null)

  const toggleSessionExpanded = (sessionId: string) => {
    const newExpanded = new Set(expandedSessions)
    if (newExpanded.has(sessionId)) {
      newExpanded.delete(sessionId)
    } else {
      newExpanded.add(sessionId)
    }
    setExpandedSessions(newExpanded)
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  }

  const getLanguageInfo = (languageId: string) => {
    return AVAILABLE_LANGUAGES.find(lang => lang.id === languageId) || AVAILABLE_LANGUAGES[0]
  }

  const switchToSession = (sessionId: string) => {
    onSelectSession(sessionId)
  }

  const handleCreateSession = async (language?: string) => {
    if (isCreating || isLoading) return
    
    setIsCreating(true)
    try {
      await onCreateSession(undefined, language)
    } catch (error) {
      console.error('Failed to create session:', error)
    } finally {
      setIsCreating(false)
    }
  }

  const handleLanguageSelect = async (language: string) => {
    setShowLanguageMenu(false)
    await handleCreateSession(language)
  }

  const startRename = (sessionId: string, currentName: string) => {
    setRenamingSessionId(sessionId)
    setRenameValue(currentName)
  }

  const cancelRename = () => {
    setRenamingSessionId(null)
    setRenameValue('')
  }

  const handleRename = async () => {
    if (renamingSessionId && renameValue.trim()) {
      try {
        await onRenameSession(renamingSessionId, renameValue.trim())
        cancelRename()
      } catch (error) {
        console.error('Failed to rename session:', error)
      }
    }
  }

  const handleRenameKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleRename()
    } else if (e.key === 'Escape') {
      cancelRename()
    }
  }

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
  }, [])

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing || !sessionSwitcherRef.current) return
    
    const rect = sessionSwitcherRef.current.getBoundingClientRect()
    const newWidth = e.clientX - rect.left
    
    // Apply constraints
    const minWidth = 250
    const maxWidth = 600
    const constrainedWidth = Math.min(Math.max(newWidth, minWidth), maxWidth)
    
    setWidth(constrainedWidth)
  }, [isResizing])

  const handleMouseUp = useCallback(() => {
    setIsResizing(false)
  }, [])

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
      }
    }
  }, [isResizing, handleMouseMove, handleMouseUp])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showLanguageMenu) {
        const isClickInside = languageMenuRef.current && languageMenuRef.current.contains(event.target as Node)
        
        if (!isClickInside) {
          setShowLanguageMenu(false)
        }
      }
    }

    if (showLanguageMenu) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
      }
    }
  }, [showLanguageMenu])

  return (
    <div 
      ref={sessionSwitcherRef}
      className="session-switcher" 
      style={{ width: `${width}px` }}
    >
      <div className="session-header">
        <h3 className="session-title">Sessions</h3>
        <div className="create-session-dropdown" ref={languageMenuRef}>
          <button 
            className="create-session-btn"
            onClick={() => setShowLanguageMenu(!showLanguageMenu)}
            disabled={isLoading || isCreating}
            title="Create new session"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14m-7-7h14" />
            </svg>
          </button>
          
          {showLanguageMenu && (
            <div className="language-menu">
              <div className="language-menu-header">Choose Language</div>
              {AVAILABLE_LANGUAGES.map((lang) => (
                <button
                  key={lang.id}
                  className="language-option"
                  onClick={() => handleLanguageSelect(lang.id)}
                  disabled={isCreating}
                >
                  <span className="language-icon">{lang.icon}</span>
                  <span className="language-name">{lang.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="session-list">
        {sessions.length === 0 ? (
          <div className="no-sessions">
            <p>No active sessions</p>
            <button 
              className="create-first-session"
              onClick={() => setShowLanguageMenu(!showLanguageMenu)}
              disabled={isLoading || isCreating}
            >
              Create your first session
            </button>
          </div>
        ) : (
          sessions.map((session, index) => {
            const isActive = session.id === currentSessionId
            const isExpanded = expandedSessions.has(session.id)
            const languageInfo = getLanguageInfo(session.language)
            const hotkeyHint = index < 9 ? `${isMac ? '⌘⌥' : 'Ctrl+Alt+'}${index + 1}` : ''
            
            return (
              <div key={session.id} className={`session-item ${isActive ? 'active' : ''}`} title={hotkeyHint}>
                <div className="session-main" onClick={() => switchToSession(session.id)}>
                  <div className="session-language-badge">
                    <span className="language-icon">{languageInfo.icon}</span>
                  </div>
                  <div className="session-info">
                    {renamingSessionId === session.id ? (
                      <input
                        type="text"
                        className="session-name-input"
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onKeyPress={handleRenameKeyPress}
                        onBlur={handleRename}
                        autoFocus
                        onClick={(e) => e.stopPropagation()}
                      />
                    ) : (
                      <span className="session-name">
                        {session.name}
                        {hotkeyHint && index < 9 && (
                          <span className="hotkey-hint">{hotkeyHint}</span>
                        )}
                      </span>
                    )}
                    <span className="session-meta">
                      {languageInfo.name} • {session.execution_count} executions • {formatTimeAgo(session.last_accessed)}
                    </span>
                  </div>
                  
                  <div className="session-actions">
                    <button
                      className="expand-btn"
                      onClick={(e) => {
                        e.stopPropagation()
                        toggleSessionExpanded(session.id)
                      }}
                      title={isExpanded ? 'Show less' : 'Show more'}
                    >
                      <svg 
                        width="12" 
                        height="12" 
                        viewBox="0 0 24 24" 
                        fill="none" 
                        stroke="currentColor" 
                        strokeWidth="2"
                        className={`chevron ${isExpanded ? 'expanded' : ''}`}
                      >
                        <path d="M6 9l6 6 6-6" />
                      </svg>
                    </button>
                    
                    <button
                      className="rename-btn"
                      onClick={(e) => {
                        e.stopPropagation()
                        startRename(session.id, session.name)
                      }}
                      disabled={isLoading}
                      title="Rename session"
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
                      </svg>
                    </button>
                    
                    <button
                      className="delete-btn"
                      onClick={(e) => {
                        e.stopPropagation()
                        if (window.confirm(`Delete session "${session.name}"?`)) {
                          onDeleteSession(session.id)
                        }
                      }}
                      disabled={isLoading}
                      title="Delete session"
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M3 6h18m-2 0v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6m3 0V4c0-1 1-2 2-2h4c0-1 1-2 2-2v2" />
                      </svg>
                    </button>
                  </div>
                </div>

                {isExpanded && (
                  <div className="session-details">
                    <div className="detail-row">
                      <span className="label">Language:</span>
                      <span className="value">{session.language}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Created:</span>
                      <span className="value">{new Date(session.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">ID:</span>
                      <span className="value session-id">{session.id.slice(0, 8)}...</span>
                    </div>
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>

      <div className="keyboard-shortcuts">
        <div className="shortcuts-title">Keyboard Shortcuts</div>
        <div className="shortcut-item">
          <kbd>{isMac ? '⌘⌥' : 'Ctrl+Alt+'}1-9</kbd>
          <span>Switch to session</span>
        </div>
        <div className="shortcut-item">
          <kbd>{isMac ? '⌘⌥[' : 'Ctrl+Alt+['}</kbd>
          <span>Previous session</span>
        </div>
        <div className="shortcut-item">
          <kbd>{isMac ? '⌘⌥]' : 'Ctrl+Alt+]'}</kbd>
          <span>Next session</span>
        </div>
      </div>

      {(isLoading || isCreating) && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
        </div>
      )}
      
      <div 
        ref={resizeHandleRef}
        className="session-switcher-resize-handle"
        onMouseDown={handleMouseDown}
      />
    </div>
  )
}