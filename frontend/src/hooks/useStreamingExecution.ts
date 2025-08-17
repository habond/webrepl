import { useState, useRef } from 'react'
import { v4 as uuidv4 } from 'uuid'
import type { TerminalEntry, Language } from '@/types'

export const useStreamingExecution = (sessionId: string) => {
  const [isLoading, setIsLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)

  const executeCodeWithStreaming = async (
    code: string,
    selectedLanguage: Language,
    onAddEntry: (entry: TerminalEntry) => void,
    onUpdateEntry?: (id: string, content: string) => void,
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

    // Don't set isLoading for streaming - we'll handle it differently
    setIsStreaming(true)

    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController()

    // Create placeholder entries for output and error
    const outputEntryId = uuidv4()
    const errorEntryId = uuidv4()
    let hasOutput = false
    let hasError = false
    let outputBuffer = ''
    let errorBuffer = ''

    try {
      // Use regular execution for languages that don't support streaming
      if (!selectedLanguage.supportsStreaming) {
        setIsLoading(true)
        setIsStreaming(false)
        const response = await fetch(`/api/${selectedLanguage.id}/execute/${sessionId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ code }),
          signal: abortControllerRef.current.signal,
        })

        const data = await response.json()

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
      } else {
        // Use SSE streaming
        const response = await fetch(`/api/${selectedLanguage.id}/execute-stream/${sessionId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ code }),
          signal: abortControllerRef.current.signal,
        })

        if (!response.ok) {
          throw new Error('Failed to execute code')
        }

        const reader = response.body?.getReader()
        const decoder = new TextDecoder()

        if (!reader) {
          throw new Error('No response body')
        }

        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6)
              if (dataStr.trim()) {
                try {
                  const data = JSON.parse(dataStr)
                  
                  if (data.type === 'output') {
                    if (!hasOutput) {
                      hasOutput = true
                      outputBuffer = data.content
                      const outputEntry: TerminalEntry = {
                        id: outputEntryId,
                        type: 'output',
                        content: outputBuffer,
                        timestamp: new Date(),
                      }
                      onAddEntry(outputEntry)
                    } else {
                      outputBuffer += data.content
                      // Always update the entry when we get new content
                      if (onUpdateEntry) {
                        onUpdateEntry(outputEntryId, outputBuffer)
                      }
                    }
                  } else if (data.type === 'error') {
                    if (!hasError) {
                      hasError = true
                      const errorEntry: TerminalEntry = {
                        id: errorEntryId,
                        type: 'error',
                        content: data.content,
                        timestamp: new Date(),
                      }
                      onAddEntry(errorEntry)
                      errorBuffer = data.content
                    } else {
                      errorBuffer += data.content
                      if (onUpdateEntry) {
                        onUpdateEntry(errorEntryId, errorBuffer)
                      }
                    }
                  } else if (data.type === 'complete') {
                    // Command completed
                    if (data.returnCode !== 0 && !hasError) {
                      const errorEntry: TerminalEntry = {
                        id: uuidv4(),
                        type: 'error',
                        content: `Command exited with code ${data.returnCode}`,
                        timestamp: new Date(),
                      }
                      onAddEntry(errorEntry)
                    }
                  }
                } catch {
                  // Skip malformed SSE data
                }
              }
            }
          }
        }
      }
    } catch (error: unknown) {
      if (error instanceof Error && error.name !== 'AbortError') {
        const errorEntry: TerminalEntry = {
          id: uuidv4(),
          type: 'error',
          content: error.message || 'Failed to connect to server',
          timestamp: new Date(),
        }
        onAddEntry(errorEntry)
      } else if (!(error instanceof Error)) {
        const errorEntry: TerminalEntry = {
          id: uuidv4(),
          type: 'error',
          content: 'Failed to connect to server',
          timestamp: new Date(),
        }
        onAddEntry(errorEntry)
      }
    } finally {
      setIsLoading(false)
      setIsStreaming(false)
      abortControllerRef.current = null
    }
  }

  const cancelExecution = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
  }

  return {
    isLoading,
    isStreaming,
    executeCodeWithStreaming,
    cancelExecution,
  }
}