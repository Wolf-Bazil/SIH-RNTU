import { useEffect, useRef, useState } from 'react'

/**
 * Eases a number toward `value` so readings visibly move when they update
 * instead of snapping. Returns null while there is no value, so callers can
 * render a placeholder rather than a misleading zero.
 */
export default function useCountUp(value, { duration = 700 } = {}) {
  const [display, setDisplay] = useState(value ?? null)
  const fromRef = useRef(value ?? 0)
  const frameRef = useRef(0)

  useEffect(() => {
    if (value === null || value === undefined || Number.isNaN(value)) {
      setDisplay(null)
      return undefined
    }

    // Respect the OS setting rather than animating regardless.
    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    const from = fromRef.current ?? 0
    const to = Number(value)

    if (reduced || from === to) {
      fromRef.current = to
      setDisplay(to)
      return undefined
    }

    const start = performance.now()
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration)
      // easeOutExpo: fast start, gentle settle.
      const eased = t === 1 ? 1 : 1 - Math.pow(2, -10 * t)
      const current = from + (to - from) * eased
      setDisplay(current)
      if (t < 1) {
        frameRef.current = requestAnimationFrame(tick)
      } else {
        fromRef.current = to
      }
    }

    frameRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frameRef.current)
  }, [value, duration])

  return display
}
