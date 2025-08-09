import { useState, useEffect, useCallback } from 'react'
import { cleanupSessionState } from './useTerminal'
import type { SessionInfo, SessionsResponse, CreateSessionRequest, SessionResponse } from '@/types'

const API_BASE = '/api'

export const useSessionManager = () => {
  const [sessions, setSessions] = useState<SessionInfo[]>([])
  const [isLoading, setIsLoading] = useState(true) // Start as loading
  const [error, setError] = useState<string | null>(null)
  const [isCreatingSession, setIsCreatingSession] = useState(false)
  const [hasInitialized, setHasInitialized] = useState(false)

  // Fetch all sessions
  const fetchSessions = useCallback(async (isInitialLoad = false) => {
    try {
      if (isInitialLoad) setIsLoading(true)
      setError(null)
      const response = await fetch(`${API_BASE}/sessions`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch sessions: ${response.statusText}`)
      }
      
      const data: SessionsResponse = await response.json()
      setSessions(data.sessions)
      
      if (isInitialLoad) {
        setHasInitialized(true)
        setIsLoading(false)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sessions')
      console.error('Error fetching sessions:', err)
      if (isInitialLoad) {
        setHasInitialized(true)
        setIsLoading(false)
      }
    }
  }, [])

  // Create new session
  const createSession = useCallback(async (name?: string, language?: string) => {
    // Prevent concurrent session creation
    if (isCreatingSession) {
      return
    }
    
    try {
      setIsCreatingSession(true)
      setIsLoading(true)
      setError(null)
      
      const requestBody: CreateSessionRequest = {
        ...(name && { name }),
        ...(language && { language })
      }
      
      const response = await fetch(`${API_BASE}/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })
      
      if (!response.ok) {
        throw new Error(`Failed to create session: ${response.statusText}`)
      }
      
      const newSession: SessionResponse = await response.json()
      
      // Refresh sessions list
      await fetchSessions()
      
      return newSession
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create session'
      setError(errorMessage)
      console.error('Error creating session:', err)
      throw err
    } finally {
      setIsLoading(false)
      setIsCreatingSession(false)
    }
  }, [fetchSessions, isCreatingSession])

  // Delete session
  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      setIsLoading(true)
      setError(null)
      
      const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) {
        throw new Error(`Failed to delete session: ${response.statusText}`)
      }
      
      // Clean up terminal state for this session
      cleanupSessionState(sessionId)
      
      // Remove from local state immediately
      setSessions(prev => prev.filter(session => session.id !== sessionId))
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete session'
      setError(errorMessage)
      console.error('Error deleting session:', err)
      // Refresh sessions to ensure consistency
      await fetchSessions()
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [sessions, fetchSessions])

  // Get session by ID
  const getSession = useCallback(async (sessionId: string): Promise<SessionInfo | null> => {
    try {
      const response = await fetch(`${API_BASE}/sessions/${sessionId}`)
      
      if (!response.ok) {
        if (response.status === 404) {
          return null
        }
        throw new Error(`Failed to fetch session: ${response.statusText}`)
      }
      
      return await response.json()
    } catch (err) {
      console.error('Error fetching session:', err)
      return null
    }
  }, [])

  // Rename session
  const renameSession = useCallback(async (sessionId: string, newName: string) => {
    try {
      setIsLoading(true)
      setError(null)
      
      const response = await fetch(`${API_BASE}/sessions/${sessionId}/rename`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: newName })
      })
      
      if (!response.ok) {
        throw new Error(`Failed to rename session: ${response.statusText}`)
      }
      
      // Refresh sessions list to reflect the rename
      await fetchSessions()
      
      return await response.json()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to rename session'
      setError(errorMessage)
      console.error('Error renaming session:', err)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [fetchSessions])

  // Auto-refresh sessions periodically
  useEffect(() => {
    // Initial load
    fetchSessions(true)
    
    // Refresh sessions every 30 seconds
    const interval = setInterval(() => fetchSessions(false), 30000)
    return () => clearInterval(interval)
  }, [fetchSessions])

  return {
    sessions,
    isLoading: isLoading || isCreatingSession,
    hasInitialized,
    error,
    fetchSessions,
    createSession,
    deleteSession,
    getSession,
    renameSession,
    clearError: () => setError(null)
  }
}