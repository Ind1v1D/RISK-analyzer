import { useEffect, useState } from 'react'
import Navbar from './components/Navbar.jsx'
import Hero from './components/Hero.jsx'
import Results from './components/Results.jsx'
import Disclaimer from './components/Disclaimer.jsx'
import Compare from './components/Compare.jsx'
import HowItWorksModal from './components/HowItWorksModal.jsx'
import SettingsModal from './components/SettingsModal.jsx'
import { analyzeContract, fetchSample } from './api.js'
import { useI18n } from './i18n/I18nContext.jsx'

/**
 * App shell + screen flow:  landing (upload)  ->  loading  ->  results
 * Errors bounce back to the landing screen and display inside the hero card.
 */
export default function App() {
  const { t, lang } = useI18n()
  const [screen, setScreen] = useState(() => window.location.pathname === '/compare' ? 'compare' : 'landing') // 'landing' | 'loading' | 'results' | 'compare'
  const [result, setResult] = useState(null)
  // Stored as an object (not a string) so the message is translated at render
  // time and follows the language if it is changed while the error is visible.
  const [error, setError] = useState(null)
  const [showHowTo, setShowHowTo] = useState(false)
  const [showSettings, setShowSettings] = useState(false)

  const loading = screen === 'loading'

  useEffect(() => {
    const onPopState = () => setScreen(window.location.pathname === '/compare' ? 'compare' : 'landing')
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  function openCompare() {
    window.history.pushState({}, '', '/compare')
    setScreen('compare')
  }

  const errorText = error
    ? error.code === 'network'
      ? t('errors.network')
      : error.message || t('errors.generic')
    : ''

  async function runAnalysis({ file = null, text = '' }) {
    setError(null)
    setScreen('loading')
    try {
      const data = await analyzeContract({ file, text, lang })
      setResult(data)
      setScreen('results')
      window.scrollTo({ top: 0 })
    } catch (err) {
      setError({ code: err.code, message: err.message })
      setScreen('landing')
    }
  }

  async function runExample() {
    if (loading) return
    setError(null)
    setScreen('loading')
    try {
      const { text } = await fetchSample(lang)
      const data = await analyzeContract({ text, lang })
      setResult(data)
      setScreen('results')
      window.scrollTo({ top: 0 })
    } catch (err) {
      setError({ code: err.code, message: err.message })
      setScreen('landing')
    }
  }

  function reset() {
    if (window.location.pathname !== '/') window.history.pushState({}, '', '/')
    setResult(null)
    setError(null)
    setScreen('landing')
    window.scrollTo({ top: 0 })
  }

  return (
    <div className="app">
      <Navbar
        loading={loading}
        onHome={reset}
        onExample={runExample}
        onCompare={openCompare}
        onHowItWorks={() => setShowHowTo(true)}
        onSettings={() => setShowSettings(true)}
      />

      <main className="app__main">
        {screen === 'compare' ? (
          <Compare onHome={reset} />
        ) : screen === 'results' && result ? (
          <Results result={result} onReset={reset} />
        ) : (
          <Hero
            loading={loading}
            error={errorText}
            onRun={runAnalysis}
            onExample={runExample}
            onCompare={openCompare}
            onHowItWorks={() => setShowHowTo(true)}
          />
        )}
      </main>

      <Disclaimer />

      {showHowTo && <HowItWorksModal onClose={() => setShowHowTo(false)} />}
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </div>
  )
}
