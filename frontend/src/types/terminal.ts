export interface TerminalEntry {
  id: string
  type: 'input' | 'output' | 'error'
  content: string
  timestamp: Date
}

export interface APITerminalEntry {
  id: string
  type: 'input' | 'output' | 'error'
  content: string
  timestamp: string
}

export interface Language {
  id: string
  name: string
  icon: string
  prompt: string
  port: number
}

export interface APIResponse {
  output: string
  error: string | null
}

export interface CodeRequest {
  code: string
}