/**
 * Side panel listing every flag: risk badge, the flagged excerpt (truncated),
 * and the plain-language explanation a non-lawyer can understand.
 * Entries are scroll-linked with the highlights in the document.
 */
export default function FlagPanel({ flags, activeIndex, onSelect, unmatchedCount }) {
  if (flags.length === 0) {
    return (
      <aside className="flag-panel">
        <div className="empty-state">
          <strong>No obvious red flags found.</strong>
          <p>
            The AI didn&rsquo;t flag anything that clearly needs attention — but
            it can miss things. Consider having a licensed attorney review the
            document before you sign.
          </p>
        </div>
      </aside>
    )
  }

  return (
    <aside className="flag-panel">
      <div className="flag-panel__header">
        <h2 className="flag-panel__title">{flags.length} clause{flags.length === 1 ? '' : 's'} flagged</h2>
        <p className="flag-panel__notice">
          AI-generated starting points — not legal advice.
        </p>
      </div>

      {flags.map((flag, i) => (
        <div
          key={i}
          id={`panel-${i}`}
          className={`flag-item${activeIndex === i ? ' flag-item--active' : ''}`}
          onClick={() => onSelect(i, 'panel')}
        >
          <div className="flag-item__head">
            <span className={`risk-badge risk-badge--${flag.risk_level.toLowerCase()}`}>
              {flag.risk_level} risk
            </span>
            <span className="flag-item__num">#{i + 1}</span>
          </div>
          <p className="flag-item__quote">“{flag.clause_text}”</p>
          <p className="flag-item__why">{flag.explanation}</p>
        </div>
      ))}

      {unmatchedCount > 0 && (
        <p className="flag-panel__footnote">
          {unmatchedCount} flag{unmatchedCount === 1 ? '' : 's'} couldn&rsquo;t be
          located in the text but {unmatchedCount === 1 ? 'is' : 'are'} listed above.
        </p>
      )}
    </aside>
  )
}
