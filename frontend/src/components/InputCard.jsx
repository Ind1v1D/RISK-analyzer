import { useRef, useState } from 'react'

const ACCEPTED = ['.pdf', '.docx', '.txt', '.md']
const MAX_BYTES = 10 * 1024 * 1024 // matches the backend limit

/**
 * The pill/card-shaped input — the primary call to action on the landing page.
 * Two modes toggled by the chip buttons underneath:
 *   paste  -> textarea with placeholder text
 *   upload -> drag-and-drop zone + file picker
 * A circular accent submit button is docked to the card's bottom-right corner.
 */
export default function InputCard({ onSubmit }) {
  const [mode, setMode] = useState('paste') // 'paste' | 'upload'
  const [text, setText] = useState('')
  const [file, setFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [localError, setLocalError] = useState('')
  const fileInput = useRef(null)

  const canSubmit =
    (mode === 'paste' && text.trim().length > 0) || (mode === 'upload' && file)

  function pickFile(candidate) {
    setLocalError('')
    if (!candidate) return
    const ext = `.${candidate.name.split('.').pop()}`.toLowerCase()
    if (!ACCEPTED.includes(ext)) {
      setLocalError('Unsupported file — please use a PDF, DOCX, or TXT file.')
      return
    }
    if (candidate.size > MAX_BYTES) {
      setLocalError('That file is over 10 MB — please upload a smaller one.')
      return
    }
    setFile(candidate)
  }

  function submit() {
    if (!canSubmit) return
    onSubmit(mode === 'upload' ? { file } : { text })
  }

  return (
    <div className="input-card">
      {mode === 'paste' ? (
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste your contract or upload a file…"
          spellCheck={false}
        />
      ) : (
        <div
          className={`dropzone${dragOver ? ' dropzone--over' : ''}`}
          onClick={() => fileInput.current?.click()}
          onDragOver={(e) => {
            e.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragOver(false)
            pickFile(e.dataTransfer.files?.[0])
          }}
        >
          <input
            ref={fileInput}
            type="file"
            accept=".pdf,.docx,.txt,.md"
            hidden
            onChange={(e) => pickFile(e.target.files?.[0])}
          />
          {file ? (
            <span className="file-chip">
              {file.name}
              <button
                className="file-chip__x"
                title="Remove file"
                onClick={(e) => {
                  e.stopPropagation()
                  setFile(null)
                }}
              >
                ✕
              </button>
            </span>
          ) : (
            <>
              <strong>Drag &amp; drop your contract here</strong>
              <span>or click to browse — PDF, DOCX, or TXT</span>
            </>
          )}
        </div>
      )}

      <div className="input-card__footer">
        <div className="input-card__chips">
          <button
            className={`chip${mode === 'upload' ? ' chip--active' : ''}`}
            onClick={() => setMode('upload')}
          >
            📎 Upload File
          </button>
          <button
            className={`chip${mode === 'paste' ? ' chip--active' : ''}`}
            onClick={() => setMode('paste')}
          >
            ✎ Paste Text
          </button>
        </div>

        <button
          className="submit-btn"
          onClick={submit}
          disabled={!canSubmit}
          title="Analyze contract"
          aria-label="Analyze contract"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M5 12h13M13 6l6 6-6 6"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>

      {localError && <p className="input-card__error">{localError}</p>}
    </div>
  )
}
