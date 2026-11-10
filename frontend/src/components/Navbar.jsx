import { useI18n } from '../i18n/I18nContext.jsx'
import { useTheme } from '../theme/ThemeContext.jsx'

const SunIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="2" />
    <path
      d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    />
  </svg>
)

const MoonIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path
      d="M21 12.8A8.5 8.5 0 1 1 11.2 3a6.6 6.6 0 0 0 9.8 9.8z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinejoin="round"
    />
  </svg>
)

const GearIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" />
    <path
      d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3h0a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5h0a1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9v0a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinejoin="round"
    />
  </svg>
)

/** Minimal transparent navbar: logo left, text links + theme toggle + settings right. */
export default function Navbar({ loading, onHome, onExample, onCompare, onHowItWorks, onSettings }) {
  const { t } = useI18n()
  const { theme, toggleTheme } = useTheme()
  const themeLabel = theme === 'dark' ? t('nav.themeToLight') : t('nav.themeToDark')

  return (
    <header className="navbar">
      <button className="navbar__logo" onClick={onHome} title={t('nav.home')}>
        <span className="navbar__mark" aria-hidden="true" />
        ClauseCheck
      </button>

      <nav className="navbar__links">
        <button className="navbar__link" onClick={onHowItWorks}>
          {t('nav.howItWorks')}
        </button>
        <button className="navbar__link" onClick={onExample} disabled={loading}>
          {t('nav.example')}
        </button>
        <button className="navbar__link" onClick={onCompare}>
          {t('nav.compare')}
        </button>

        <div className="navbar__actions">
          <button
            className="icon-btn"
            onClick={toggleTheme}
            title={themeLabel}
            aria-label={themeLabel}
          >
            {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
          </button>
          <button
            className="icon-btn"
            onClick={onSettings}
            title={t('nav.settings')}
            aria-label={t('nav.settings')}
          >
            <GearIcon />
          </button>
        </div>
      </nav>
    </header>
  )
}
