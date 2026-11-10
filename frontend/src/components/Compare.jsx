import { useState } from 'react'
import { compareContracts } from '../api.js'
import { useI18n } from '../i18n/I18nContext.jsx'
import '../styles/Compare.css'

function VersionInput({ label, value, onChange, file, onFile, placeholder }) {
  const { t } = useI18n()
  return (
    <section className="compare-input">
      <label className="compare-input__label">{label}</label>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        disabled={Boolean(file)}
      />
      <div className="compare-input__file-row">
        <label className="compare-input__file-button">
          {file ? file.name : t('compare.chooseFile')}
          <input
            type="file"
            accept=".pdf,.docx,.txt,.md"
            onChange={(event) => onFile(event.target.files?.[0] || null)}
          />
        </label>
        {file && <button className="compare-input__clear" onClick={() => onFile(null)}>{t('compare.clearFile')}</button>}
      </div>
    </section>
  )
}

export default function Compare({ onHome }) {
  const { t } = useI18n()
  const [versions, setVersions] = useState(['', ''])
  const [files, setFiles] = useState([null, null])
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const canCompare = (files[0] && files[1]) ||
    (!files[0] && !files[1] && versions[0].trim() && versions[1].trim())

  function updateVersion(index, value) {
    setVersions((current) => current.map((item, i) => i === index ? value : item))
    setFiles((current) => current.map((item, i) => i === index ? null : item))
  }

  function updateFile(index, file) {
    setFiles((current) => current.map((item, i) => i === index ? file : item))
    if (file) setVersions((current) => current.map((item, i) => i === index ? '' : item))
  }

  async function runCompare() {
    if (!canCompare || loading) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = files[0] && files[1]
        ? await compareContracts({ files })
        : await compareContracts({ v1: versions[0], v2: versions[1] })
      setResult(data)
    } catch (err) {
      setError(err.message || t('compare.failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="compare-page">
      <header className="compare-page__heading">
        <div>
          <h1>{t('compare.title')}</h1>
          <p>{t('compare.subtitle')}</p>
        </div>
        <button className="btn-primary" onClick={onHome}>{t('compare.back')}</button>
      </header>

      <div className="compare-inputs">
        <VersionInput label={t('compare.version1')} value={versions[0]} file={files[0]}
          onChange={(value) => updateVersion(0, value)} onFile={(file) => updateFile(0, file)}
          placeholder={t('compare.placeholder1')} />
        <VersionInput label={t('compare.version2')} value={versions[1]} file={files[1]}
          onChange={(value) => updateVersion(1, value)} onFile={(file) => updateFile(1, file)}
          placeholder={t('compare.placeholder2')} />
      </div>
      <div className="compare-actions">
        <span className="compare-privacy">{t('compare.privacy')}</span>
        <button className="btn-primary" disabled={!canCompare || loading} onClick={runCompare}>
          {loading ? t('compare.loading') : t('compare.run')}
        </button>
      </div>
      {error && <p className="compare-error" role="alert">{error}</p>}

      {result && (
        <section className="compare-results" aria-live="polite">
          <div className="compare-results__summary">
            <div>
              <span className={`compare-verdict compare-verdict--${result.verdict.toLowerCase().replaceAll(' ', '-')}`}>
                {t(`compare.verdict.${result.verdict.toLowerCase().replaceAll(' ', '-')}`)}
              </span>
              <p>{t('compare.score', { before: result.risk_score_before, after: result.risk_score_after })}</p>
            </div>
            <div className="compare-counts">
              {['added', 'removed', 'modified', 'moved', 'unchanged'].map((key) => (
                <span key={key}>{t(`compare.status.${key}`)} <b>{result.summary[key]}</b></span>
              ))}
            </div>
          </div>
          <div className="compare-cards">
            {result.changes.filter((item) => item.status !== 'unchanged').map((item, index) => (
              <article className={`compare-change compare-change--${item.status}`} key={`${item.status}-${index}`}>
                <div className="compare-change__head">
                  <span className={`compare-status compare-status--${item.status}`}>{t(`compare.status.${item.status}`)}</span>
                  <span className="compare-risk-change">{t(`compare.risk.${item.risk_change.toLowerCase().replaceAll(' ', '-')}`)}</span>
                </div>
                {item.before_text && <p className="compare-change__text"><b>{t('compare.before')}:</b> {item.before_text}</p>}
                {item.after_text && <p className="compare-change__text"><b>{t('compare.after')}:</b> {item.after_text}</p>}
                {item.status === 'modified' && (
                  <p className="compare-diff" aria-label={t('compare.wordDiff')}>
                    {item.word_diff.map((part, i) => part.kind === 'removed'
                      ? <del key={i}>{part.text}</del>
                      : part.kind === 'added'
                        ? <ins key={i}>{part.text}</ins>
                        : <span key={i}>{part.text}</span>)}
                  </p>
                )}
                {item.key_terms.length > 0 && (
                  <div className="compare-terms">{item.key_terms.map((term, i) => <span key={i}>{term.before} → {term.after}</span>)}</div>
                )}
              </article>
            ))}
          </div>
          <p className="compare-disclaimer">{result.disclaimer}</p>
        </section>
      )}
    </main>
  )
}
