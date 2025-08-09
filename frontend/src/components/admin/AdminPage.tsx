import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { AVAILABLE_LANGUAGES } from '@/config/languages'
import { ThemeToggle } from '@/components/ui/ThemeToggle'

interface AdminSession {
  id: string
  name: string
  language: string
  created_at: string
  last_accessed: string
  execution_count: number
  history_count: number
  last_history_entry?: {
    type: string
    content: string
    timestamp: string
  }
  has_environment: boolean
  environment_language?: string
  environment_updated?: string
  full_history: Array<{
    id: string
    type: string
    content: string
    timestamp: string
  }>
  environment_details?: {
    language: string
    data: string
    last_updated: string
    data_size: number
  }
}

interface AdminResponse {
  sessions: AdminSession[]
  total: number
  summary: {
    total_sessions: number
    by_language: Record<string, number>
    active_sessions: number
    total_executions: number
  }
}

export const AdminPage = () => {
  const [data, setData] = useState<AdminResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())

  const fetchAdminData = async () => {
    try {
      const response = await fetch('/api/session-manager/admin/sessions')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const adminData = await response.json()
      setData(adminData)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch admin data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAdminData()
  }, [])

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchAdminData, 5000) // Refresh every 5 seconds
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

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

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
  }

  const getLanguageInfo = (languageId: string) => {
    return AVAILABLE_LANGUAGES.find(lang => lang.id === languageId) || AVAILABLE_LANGUAGES[0]
  }

  const toggleRowExpansion = (sessionId: string) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(sessionId)) {
      newExpanded.delete(sessionId)
    } else {
      newExpanded.add(sessionId)
    }
    setExpandedRows(newExpanded)
  }

  const decodeEnvironmentData = (base64Data: string): { decoded: string, formatted: string, type: string } => {
    try {
      // Decode base64
      const decoded = atob(base64Data)
      
      // Try to parse as JSON first (for JavaScript environments)
      try {
        const parsed = JSON.parse(decoded)
        return {
          decoded: decoded,
          formatted: JSON.stringify(parsed, null, 2),
          type: 'JSON'
        }
      } catch {
        // Not JSON, check if it's Python pickle format
        if (decoded.includes('pickle') || decoded.includes('\x80\x03') || decoded.startsWith('\x80')) {
          return {
            decoded: decoded,
            formatted: '# Python Pickle Data (binary format)\n# Cannot be displayed as text - contains serialized Python objects\n\n' +
                      `Raw bytes (first 100 chars): ${decoded.slice(0, 100).split('').map(c => c.charCodeAt(0) < 32 || c.charCodeAt(0) > 126 ? `\\x${c.charCodeAt(0).toString(16).padStart(2, '0')}` : c).join('')}${decoded.length > 100 ? '...' : ''}`,
            type: 'Python Pickle'
          }
        }
        
        // Check if it looks like serialized data but readable
        if (decoded.includes('__main__') || decoded.includes('globals') || decoded.includes('locals')) {
          return {
            decoded: decoded,
            formatted: '# Serialized Environment Data\n' + decoded,
            type: 'Serialized Data'
          }
        }
        
        // Plain text or unknown format
        return {
          decoded: decoded,
          formatted: decoded,
          type: 'Raw Text'
        }
      }
    } catch (error) {
      return {
        decoded: 'Failed to decode base64 data',
        formatted: `Error decoding: ${error instanceof Error ? error.message : 'Unknown error'}`,
        type: 'Error'
      }
    }
  }

  if (loading) {
    return (
      <div className="admin-page">
        <div className="admin-header">
          <h1>Session Admin</h1>
        </div>
        <div className="admin-loading">Loading admin data...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="admin-page">
        <div className="admin-header">
          <h1>Session Admin</h1>
        </div>
        <div className="admin-error">
          Error loading admin data: {error}
          <button className="retry-btn" onClick={fetchAdminData}>Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="admin-page">
      <div className="admin-header">
        <div className="admin-title-section">
          <Link to="/" className="back-link">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5m7 7-7-7 7-7"/>
            </svg>
            Back to Terminal
          </Link>
          <h1>Session Admin</h1>
        </div>
        <div className="admin-controls">
          <ThemeToggle />
          <label className="auto-refresh-toggle">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto refresh (5s)
          </label>
          <button className="refresh-btn" onClick={fetchAdminData}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
              <path d="M21 3v5h-5"/>
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
              <path d="M3 21v-5h5"/>
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {data && (
        <>
          <div className="admin-summary">
            <div className="summary-card">
              <h3>Total Sessions</h3>
              <div className="summary-value">{data.summary.total_sessions}</div>
            </div>
            <div className="summary-card">
              <h3>Active Sessions</h3>
              <div className="summary-value">{data.summary.active_sessions}</div>
            </div>
            <div className="summary-card">
              <h3>Total Executions</h3>
              <div className="summary-value">{data.summary.total_executions}</div>
            </div>
            <div className="summary-card">
              <h3>Languages</h3>
              <div className="language-breakdown">
                {Object.entries(data.summary.by_language).map(([lang, count]) => {
                  const langInfo = getLanguageInfo(lang)
                  return (
                    <div key={lang} className="language-stat">
                      <span className="language-icon">{langInfo.icon}</span>
                      <span className="language-name">{langInfo.name}</span>
                      <span className="language-count">{count}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          <div className="admin-table-container">
            <table className="admin-table">
              <thead>
                <tr>
                  <th></th>
                  <th>Name</th>
                  <th>Language</th>
                  <th>ID</th>
                  <th>Created</th>
                  <th>Last Active</th>
                  <th>Executions</th>
                  <th>History</th>
                  <th>Last Entry</th>
                  <th>Environment</th>
                </tr>
              </thead>
              <tbody>
                {data.sessions.map((session) => {
                  const langInfo = getLanguageInfo(session.language)
                  const isExpanded = expandedRows.has(session.id)
                  return (
                    <>
                      <tr key={session.id} className="admin-row">
                        <td className="expand-cell">
                          <button 
                            className="expand-btn" 
                            onClick={() => toggleRowExpansion(session.id)}
                            title={isExpanded ? "Collapse details" : "Expand details"}
                          >
                            <svg 
                              width="16" 
                              height="16" 
                              viewBox="0 0 24 24" 
                              fill="none" 
                              stroke="currentColor" 
                              strokeWidth="2"
                              style={{ transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }}
                            >
                              <path d="M9 18l6-6-6-6"/>
                            </svg>
                          </button>
                        </td>
                        <td className="session-name">
                          <div className="name-with-language">
                            <span className="language-badge">
                              <span className="language-icon">{langInfo.icon}</span>
                            </span>
                            <span className="name">{session.name}</span>
                          </div>
                        </td>
                        <td className="language-cell">
                          <span className="language-name">{langInfo.name}</span>
                        </td>
                        <td className="session-id">
                          <code>{session.id.slice(0, 8)}...</code>
                        </td>
                        <td className="date-cell" title={formatDateTime(session.created_at)}>
                          {formatTimeAgo(session.created_at)}
                        </td>
                        <td className="date-cell" title={formatDateTime(session.last_accessed)}>
                          <span className={session.execution_count > 0 ? 'active-session' : 'inactive-session'}>
                            {formatTimeAgo(session.last_accessed)}
                          </span>
                        </td>
                        <td className="execution-count">
                          <span className={`count ${session.execution_count > 0 ? 'has-executions' : 'no-executions'}`}>
                            {session.execution_count}
                          </span>
                        </td>
                        <td className="history-count">
                          {session.history_count}
                        </td>
                        <td className="last-entry">
                          {session.last_history_entry ? (
                            <div className="entry-preview">
                              <span className={`entry-type ${session.last_history_entry.type}`}>
                                {session.last_history_entry.type}
                              </span>
                              <span className="entry-content" title={session.last_history_entry.content}>
                                {session.last_history_entry.content}
                              </span>
                            </div>
                          ) : (
                            <span className="no-history">No history</span>
                          )}
                        </td>
                        <td className="environment-cell">
                          <span className={`environment-status ${session.has_environment ? 'has-env' : 'no-env'}`}>
                            {session.has_environment ? '✓ Saved' : '✗ None'}
                          </span>
                        </td>
                      </tr>
                      
                      {isExpanded && (
                        <tr key={`${session.id}-details`} className="admin-row-details">
                          <td colSpan={10}>
                            <div className="session-details-container">
                              <div className="details-section">
                                <h4>Session Information</h4>
                                <div className="details-grid">
                                  <div className="detail-item">
                                    <span className="detail-label">Full ID:</span>
                                    <code className="detail-value">{session.id}</code>
                                  </div>
                                  <div className="detail-item">
                                    <span className="detail-label">Created:</span>
                                    <span className="detail-value">{formatDateTime(session.created_at)}</span>
                                  </div>
                                  <div className="detail-item">
                                    <span className="detail-label">Last Accessed:</span>
                                    <span className="detail-value">{formatDateTime(session.last_accessed)}</span>
                                  </div>
                                </div>
                              </div>
                              
                              {session.environment_details && (
                                <div className="details-section">
                                  <h4>Environment Details</h4>
                                  <div className="details-grid">
                                    <div className="detail-item">
                                      <span className="detail-label">Language:</span>
                                      <span className="detail-value">{session.environment_details.language}</span>
                                    </div>
                                    <div className="detail-item">
                                      <span className="detail-label">Data Size:</span>
                                      <span className="detail-value">{session.environment_details.data_size} bytes</span>
                                    </div>
                                    <div className="detail-item">
                                      <span className="detail-label">Last Updated:</span>
                                      <span className="detail-value">{formatDateTime(session.environment_details.last_updated)}</span>
                                    </div>
                                  </div>
                                  {(() => {
                                    const environmentData = decodeEnvironmentData(session.environment_details.data)
                                    const badgeClass = `environment-type-badge ${
                                      environmentData.type === 'JSON' ? 'json' :
                                      environmentData.type === 'Python Pickle' ? 'pickle' :
                                      environmentData.type === 'Error' ? 'error' : ''
                                    }`
                                    return (
                                      <div className="environment-data">
                                        <div className="environment-header">
                                          <span className="detail-label">Environment Data:</span>
                                          <span className={badgeClass}>{environmentData.type}</span>
                                        </div>
                                        <pre className="environment-content">{environmentData.formatted}</pre>
                                      </div>
                                    )
                                  })()}
                                </div>
                              )}
                              
                              <div className="details-section">
                                <h4>Execution History ({session.full_history.length} entries)</h4>
                                {session.full_history.length > 0 ? (
                                  <div className="history-container">
                                    {session.full_history.map((entry, index) => (
                                      <div key={entry.id || index} className={`history-entry history-${entry.type}`}>
                                        <div className="history-header">
                                          <span className={`history-type history-type-${entry.type}`}>
                                            {entry.type.toUpperCase()}
                                          </span>
                                          <span className="history-timestamp">
                                            {formatDateTime(entry.timestamp)}
                                          </span>
                                        </div>
                                        <pre className="history-content">{entry.content}</pre>
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <div className="no-history-details">No execution history available</div>
                                )}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  )
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}