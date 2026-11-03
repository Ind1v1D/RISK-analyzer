import { useEffect } from 'react'

/** Call `handler` when Escape is pressed (used to close modals). */
export function useEscape(handler) {
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') handler()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [handler])
}
