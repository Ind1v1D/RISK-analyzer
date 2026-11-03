import { useState } from 'react'
import Navbar from './components/Navbar.jsx'
import Hero from './components/Hero.jsx'
import Results from './components/Results.jsx'
import Disclaimer from './components/Disclaimer.jsx'
import HowItWorksModal from './components/HowItWorksModal.jsx'
import { analyzeContract, fetchSample } from './api.js'

/**
 * App shell + screen flow:  landing (upload)  ->  loading  ->  results
 * Errors bounce back to the landing screen and display inside the hero card.
 */
export default function App() {
  const [screen, setScreen] = useState('landing') // 'landing' | 'loading' | 'results'
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [showHowTo, setShowHowTo] = useState(false)

  const loading = screen === 'loading'

  async function runAnalysis({ file = null, text = '' }) {
    setError('')
    setScreen('loading')
    try {
      const data = await analyzeContract({ file, text })
      setResult(data)
      setScreen('results')
      window.scrollTo({ top: 0 })
    } catch (err) {
      setError(err.message)
      setScreen('landing')
    }
  }

  async function runExample() {
    if (loading) return
    setError('')
    setScreen('loading')
    try {
      const { text } = await fetchSample()
      const data = await analyzeContract({ text })
      setResult(data)
      setScreen('results')
      window.scrollTo({ top: 0 })
    } catch (err) {
      setError(err.message)
      setScreen('landing')
    }
  }

  function reset() {
    setResult(null)
    setError('')
    setScreen('landing')
    window.scrollTo({ top: 0 })
  }

  return (
    <div className="app">
      <Navbar
        loading={loading}
        onHome={reset}
        onExample={runExample}
        onHowItWorks={() => setShowHowTo(true)}
      />

      <main className="app__main">
        {screen === 'results' && result ? (
          <Results result={result} onReset={reset} />
        ) : (
          <Hero
            loading={loading}
            error={error}
            onRun={runAnalysis}
            onExample={runExample}
            onHowItWorks={() => setShowHowTo(true)}
          />
        )}
      </main>

      <Disclaimer />

      {showHowTo && <HowItWorksModal onClose={() => setShowHowTo(false)} />}
    </div>
  )
}
