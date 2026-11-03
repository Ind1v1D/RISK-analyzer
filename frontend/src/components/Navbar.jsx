/** Minimal transparent navbar: logo left, simple text links right. */
export default function Navbar({ loading, onHome, onExample, onHowItWorks }) {
  return (
    <header className="navbar">
      <button className="navbar__logo" onClick={onHome} title="Back to home">
        <span className="navbar__mark" aria-hidden="true" />
        ClauseCheck
      </button>

      <nav className="navbar__links">
        <button className="navbar__link" onClick={onHowItWorks}>
          How it works
        </button>
        <button className="navbar__link" onClick={onExample} disabled={loading}>
          Example
        </button>
      </nav>
    </header>
  )
}
