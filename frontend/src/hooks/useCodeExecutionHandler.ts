import { useCallback } from 'react'
import type { Language, TerminalEntry } from '../types/terminal'

interface UseCodeExecutionHandlerProps {
  currentInput: string
  clearInput: () => void
  focusInput: () => void
  executeCode: (code: string, selectedLanguage: Language, onAddEntry: (entry: TerminalEntry) => void) => Promise<void>
  executeCodeWithStreaming: (code: string, selectedLanguage: Language, onAddEntry: (entry: TerminalEntry) => void, onUpdateEntry?: (id: string, content: string) => void) => Promise<void>
  selectedLanguage: Language
  addEntry: (entry: TerminalEntry) => void
  updateEntry: (id: string, content: string) => void
}

export const useCodeExecutionHandler = ({
  currentInput,
  clearInput,
  focusInput,
  executeCode,
  executeCodeWithStreaming,
  selectedLanguage,
  addEntry,
  updateEntry
}: UseCodeExecutionHandlerProps) => {
  const handleExecute = useCallback(async () => {
    const codeToExecute = currentInput
    clearInput() // Clear input immediately to prevent interference
    
    if (selectedLanguage.supportsStreaming) {
      // Use streaming execution
      await executeCodeWithStreaming(codeToExecute, selectedLanguage, addEntry, updateEntry)
    } else {
      // Use regular execution
      await executeCode(codeToExecute, selectedLanguage, addEntry)
    }
    
    // Ensure input is focused after execution completes
    focusInput()
  }, [
    currentInput,
    clearInput,
    focusInput,
    executeCode,
    executeCodeWithStreaming,
    selectedLanguage,
    addEntry,
    updateEntry
  ])

  return { handleExecute }
}