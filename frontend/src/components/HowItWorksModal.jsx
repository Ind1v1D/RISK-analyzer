/** Non-blocking explainer opened from "Learn How It Works" / the navbar. */
export default function HowItWorksModal({ onClose }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label="How it works"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="modal__title">How it works</h2>
        <ol className="modal__steps">
          <li>
            <strong>Upload or paste.</strong> PDF, DOCX, or plain text. Your
            document is processed in memory for this session only — it is never
            stored.
          </li>
          <li>
            <strong>AI first pass.</strong> Gemini reviews the contract for
            clauses that are risky, unclear, or unusually unfavorable, and
            classifies each by risk level.
          </li>
          <li>
            <strong>Review the flags.</strong> See highlighted text plus
            plain-language explanations, then talk to a licensed attorney about
            what matters for your situation.
          </li>
        </ol>
        <p className="modal__note">
          ClauseCheck is a first-pass issue-spotting aid — not legal advice, and
          not a substitute for a lawyer.
        </p>
        <button className="pill-btn modal__close" onClick={onClose}>
          Got it
        </button>
      </div>
    </div>
  )
}
