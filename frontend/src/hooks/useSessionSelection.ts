import { useEffect } from 'react'
import type { SessionInfo } from '../types/session'

interface UseSessionSelectionProps {
  sessions: SessionInfo[]
  currentSessionId: string | undefined
  setCurrentSessionId: (sessionId: string | undefined) => void
  hasInitialized: boolean
  isSessionLoading: boolean
}

export const useSessionSelection = ({
  sessions,
  currentSessionId,
  setCurrentSessionId,
  hasInitialized,
  isSessionLoading
}: UseSessionSelectionProps) => {
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
  }, [sessions, hasInitialized, isSessionLoading, currentSessionId, setCurrentSessionId])
}