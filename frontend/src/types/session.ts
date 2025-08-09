import type { APITerminalEntry } from './terminal'

export interface SessionInfo {
  id: string
  name: string
  language: string  // Single language per session
  created_at: string
  last_accessed: string
  execution_count: number
  history?: APITerminalEntry[]
}

export interface SessionsResponse {
  sessions: SessionInfo[]
  total: number
}

export interface CreateSessionRequest {
  name?: string
  language?: string
}

export interface SessionResponse {
  id: string
  name: string
  language: string  // Single language per session
  created_at: string
  last_accessed: string
  execution_count: number
  history?: APITerminalEntry[]
}