import { useState } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { replService } from '@/services/api'
import type { TerminalEntry, Language } from '@/types'

export const useCodeExecution = (sessionId: string) => {
  const [isLoading, setIsLoading] = useState(false)

  const executeCode = async (
    code: string, 
    selectedLanguage: Language,
    onAddEntry: (entry: TerminalEntry) => void,
  ) => {
    if (!code.trim() || isLoading) return

    // Add input entry
    const inputEntry: TerminalEntry = {
      id: uuidv4(),
      type: 'input',
      content: code,
      timestamp: new Date(),
    }
    onAddEntry(inputEntry)

    setIsLoading(true)

    try {
      const data = await replService.executeCode(selectedLanguage.id, code, sessionId)

      if (data.output) {
        const outputEntry: TerminalEntry = {
          id: uuidv4(),
          type: 'output',
          content: data.output,
          timestamp: new Date(),
        }
        onAddEntry(outputEntry)
      }

      if (data.error) {
        const errorEntry: TerminalEntry = {
          id: uuidv4(),
          type: 'error',
          content: data.error,
          timestamp: new Date(),
        }
        onAddEntry(errorEntry)
      }
    } catch {
      const errorEntry: TerminalEntry = {
        id: uuidv4(),
        type: 'error',
        content: 'Failed to connect to server',
        timestamp: new Date(),
      }
      onAddEntry(errorEntry)
    } finally {
      setIsLoading(false)
    }
  }

  return {
    isLoading,
    executeCode,
  }
}