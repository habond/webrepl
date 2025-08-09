import { AVAILABLE_LANGUAGES } from '@/config/languages'
import type { Language } from '@/types'

interface LanguageSelectorProps {
  selectedLanguage: Language
  onLanguageChange: (language: Language) => void
  disabled?: boolean
}

export const LanguageSelector = ({ 
  selectedLanguage, 
  onLanguageChange, 
  disabled = false 
}: LanguageSelectorProps) => {
  return (
    <div className="language-selector">
      <label htmlFor="language-select">Language:</label>
      <select
        id="language-select"
        value={selectedLanguage.id}
        onChange={e => {
          const language = AVAILABLE_LANGUAGES.find(lang => lang.id === e.target.value)
          if (language) onLanguageChange(language)
        }}
        disabled={disabled}
      >
        {AVAILABLE_LANGUAGES.map(lang => (
          <option key={lang.id} value={lang.id}>
            {lang.name}
          </option>
        ))}
      </select>
    </div>
  )
}