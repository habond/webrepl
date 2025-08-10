import type { Language } from '@/types'

// Default backend port (used for display purposes only, actual routing via nginx proxy)
const DEFAULT_BACKEND_PORT = parseInt(import.meta.env.VITE_BACKEND_PORT || '8000')

export const AVAILABLE_LANGUAGES: Language[] = [
  { 
    id: 'python', 
    name: 'Python',
    icon: '🐍',
    prompt: '>>> ', 
    port: DEFAULT_BACKEND_PORT,
  },
  { 
    id: 'javascript', 
    name: 'JavaScript',
    icon: '📜',
    prompt: '> ', 
    port: DEFAULT_BACKEND_PORT,
  },
  { 
    id: 'ruby', 
    name: 'Ruby',
    icon: '💎',
    prompt: '>> ', 
    port: DEFAULT_BACKEND_PORT,
  },
  { 
    id: 'php', 
    name: 'PHP',
    icon: '🐘',
    prompt: 'php > ', 
    port: DEFAULT_BACKEND_PORT,
  },
  { 
    id: 'kotlin', 
    name: 'Kotlin',
    icon: '🟣',
    prompt: 'kt > ', 
    port: DEFAULT_BACKEND_PORT,
  },
  { 
    id: 'haskell', 
    name: 'Haskell',
    icon: 'λ',
    prompt: 'λ> ', 
    port: DEFAULT_BACKEND_PORT,
  },
]