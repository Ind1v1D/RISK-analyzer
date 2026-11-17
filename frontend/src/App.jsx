import { useRef, useState } from 'react'
import Navbar from './components/Navbar.jsx'
import Hero from './components/Hero.jsx'
import Results from './components/Results.jsx'
import Disclaimer from './components/Disclaimer.jsx'
import HowItWorksModal from './components/HowItWorksModal.jsx'
import SettingsModal from './components/SettingsModal.jsx'
import PrintReport from './components/PrintReport.jsx'
import { analyzeContract, fetchSample } from './api.js'
import { useI18n } from './i18n/I18nContext.jsx'

const EMPTY_INPUT = { mode: 'paste', text: '', file: null }

/**
 * App shell + screen flow:  landing (upload)  ->  loading  ->  results
 * Errors bounce back to the landing screen and display inside the hero card.
 */
export default function App() {
  const { t, lang } = useI18n()
  const [screen, setScreen] = useState('landing') // 'landing' | 'loading' | 'results'
  const [result, setResult] = useState(null)
  const [docName, setDocName] = useState(null) // uploaded file name, null for pasted text / example
  // Input state lives here (not in InputCard) so it survives loading + errors.
  const [input, setInput] = useState(EMPTY_INPUT)
  // Stored as an object (not a string) so the message is translated at render
  // time and follows the language if it is changed while the error is visible.
  const [error, setError] = useState(null)
  const [showHowTo, setShowHowTo] = useState(false)
  const [showSettings, setShowSettings] = useState(false)

  // Identifies the latest request; responses from older/cancelled ones are ignored.
  const pending = useRef({ id: 0, controller: null })

  const loading = screen === 'loading'

  let errorText = ''
  if (error) {
    if (error.code === 'network') errorText = t('errors.network')
    else if (error.code === 'timeout') errorText = t('errors.timeout')
    else {
      errorText = error.message || t('errors.generic')
      if ((error.status === 429 || error.status === 503) && error.retryAfter) {
        errorText += ` ${t('errors.retryAfter', { count: error.retryAfter })}`
      }
    }
  }

  function cancelPending() {
    pending.current.controller?.abort()
    pending.current = { id: pending.current.id + 1, controller: null }
  }

  /** Runs `job(signal)`; shows the result unless this request was superseded or cancelled. */
  async function run(job, name) {
    cancelPending()
    const controller = new AbortController()
    const id = pending.current.id
    pending.current.controller = controller
    setError(null)
    setScreen('loading')
    try {
      const data = await job(controller.signal)
      if (pending.current.id !== id) return
      setResult(data)
      setDocName(name)
      setScreen('results')
      window.scrollTo({ top: 0 })
    } catch (err) {
      if (pending.current.id !== id || err.code === 'aborted') return
      setError({ code: err.code, message: err.message, status: err.status, retryAfter: err.retryAfter })
      setScreen('landing')
    }
  }

  function runAnalysis({ file = null, text = '' }) {
    return run((signal) => analyzeContract({ file, text, lang, signal }), file ? file.name : null)
  }

  function runExample() {
    if (loading) return
    return run(async (signal) => {
      const { text } = await fetchSample(lang, signal)
      return analyzeContract({ text, lang, signal })
    }, null)
  }

  /** Back to the landing screen; cancels any in-flight request. Input is kept. */
  function goHome() {
    cancelPending()
    setResult(null)
    setError(null)
    setScreen('landing')
    window.scrollTo({ top: 0 })
  }

  /** "Analyze another contract": same, but start with an empty input. */
  function startOver() {
    setInput(EMPTY_INPUT)
    goHome()
  }

  return (
    <>
      <div className="app">
        <Navbar
          loading={loading}
          onHome={goHome}
          onExample={runExample}
          onHowItWorks={() => setShowHowTo(true)}
          onSettings={() => setShowSettings(true)}
        />

        <main className="app__main">
          {screen === 'results' && result ? (
            <Results result={result} onReset={startOver} />
          ) : (
            <Hero
              loading={loading}
              error={errorText}
              input={input}
              onInputChange={setInput}
              onRun={runAnalysis}
              onExample={runExample}
              onHowItWorks={() => setShowHowTo(true)}
            />
          )}
        </main>

        <Disclaimer />

        {showHowTo && <HowItWorksModal onClose={() => setShowHowTo(false)} />}
        {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
      </div>

      {/* Hidden on screen; the only thing visible when printing / saving as PDF. */}
      {screen === 'results' && result && <PrintReport result={result} docName={docName} />}
    </>
  )
}
