import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { DEFAULT_LANG, LANGUAGES, translations } from './translations.js'

const STORAGE_KEY = 'clausecheck.lang'
const I18nContext = createContext(null)

/** Saved choice first, then the browser language, then English. */
function detectInitialLang() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved && translations[saved]) return saved
  } catch {
    // localStorage can be unavailable (private mode) — fall through.
  }
  const browser = (navigator.language || '').toLowerCase()
  const match = LANGUAGES.find(({ code }) => browser.startsWith(code))
  return match ? match.code : DEFAULT_LANG
}

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(detectInitialLang)

  const setLang = useCallback((next) => {
    if (!translations[next]) return
    setLangState(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // Not fatal: the choice just won't survive a reload.
    }
  }, [])

  // Keep <html lang> (screen readers, hyphenation) and the tab title in sync.
  useEffect(() => {
    document.documentElement.lang = lang
    document.title = translations[lang]['meta.title']
  }, [lang])

  /** t('key', { count: 3 }) -> translated string with {placeholders} and plurals resolved. */
  const t = useCallback(
    (key, vars = {}) => {
      let value = translations[lang][key] ?? translations[DEFAULT_LANG][key] ?? key
      if (value && typeof value === 'object') {
        const category = new Intl.PluralRules(lang).select(Number(vars.count ?? 0))
        value = value[category] ?? value.other
      }
      return String(value).replace(/\{(\w+)\}/g, (whole, name) =>
        name in vars ? String(vars[name]) : whole,
      )
    },
    [lang],
  )

  const value = useMemo(() => ({ lang, setLang, t, languages: LANGUAGES }), [lang, setLang, t])
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n() {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error('useI18n must be used inside <I18nProvider>')
  return ctx
}
