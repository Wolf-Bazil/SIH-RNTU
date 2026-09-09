import React from 'react'

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'bn', label: 'বাংলা' },
  { code: 'ta', label: 'தமிழ்' },
  { code: 'te', label: 'తెలుగు' },
  { code: 'mr', label: 'मराठी' },
  { code: 'gu', label: 'ગુજરાતી' },
  { code: 'ml', label: 'മലയാളം' },
  { code: 'kn', label: 'ಕನ್ನಡ' }
]

function LanguageToggle({ language, setLanguage, onLanguageChange }) {
  const handleChange = (e) => {
    const val = e.target.value
    if (setLanguage) setLanguage(val)
    if (onLanguageChange) onLanguageChange(val)
  }

  return (
    <div className="bg-maritime-700 rounded-lg p-4">
      <h2 className="text-lg font-bold mb-2 text-maritime-200">Language / भाषा</h2>
      <select
        className="w-full p-2 rounded bg-maritime-600 text-white border border-maritime-500 focus:outline-none"
        value={language}
        onChange={handleChange}
      >
        {LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code}>{lang.label}</option>
        ))}
      </select>
    </div>
  )
}

export default LanguageToggle
