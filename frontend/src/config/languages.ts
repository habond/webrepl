import type { Language } from '@/types'

export const AVAILABLE_LANGUAGES: Language[] = [
  { 
    id: 'python', 
    name: 'Python',
    icon: '🐍',
    prompt: '>>> ', 
    port: 8000,
  },
  { 
    id: 'javascript', 
    name: 'JavaScript',
    icon: '📜',
    prompt: '> ', 
    port: 8001,
  },
  { 
    id: 'ruby', 
    name: 'Ruby',
    icon: '💎',
    prompt: '>> ', 
    port: 8002,
  },
  { 
    id: 'php', 
    name: 'PHP',
    icon: '🐘',
    prompt: 'php > ', 
    port: 8003,
  },
  { 
    id: 'kotlin', 
    name: 'Kotlin',
    icon: '🟣',
    prompt: 'kt > ', 
    port: 8004,
  },
  { 
    id: 'haskell', 
    name: 'Haskell',
    icon: 'λ',
    prompt: 'λ> ', 
    port: 8005,
  },
]