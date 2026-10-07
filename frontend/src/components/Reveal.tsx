/** Fades content in as it scrolls into view.
 *
 * The animation is decoration; the content is not. So this is built so that
 * every failure path ends with the content visible:
 *
 *   1. Anything already on screen at mount is shown immediately — no observer,
 *      no delay, no flash of invisible merchandise above the fold.
 *   2. If the tab is hidden, or IntersectionObserver is missing, content starts
 *      visible. Observer callbacks do not run in a backgrounded tab, so waiting
 *      on one there would hide the page from someone who switches back to it.
 *   3. Only genuinely below-the-fold content waits on the observer, and even
 *      that has a timeout backstop.
 */

import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'

/** True when we should not bother hiding this content in the first place. */
function shouldShowImmediately(): boolean {
  if (typeof IntersectionObserver === 'undefined') return true
  // A backgrounded tab never fires observer callbacks.
  if (typeof document !== 'undefined' && document.hidden) return true
  // Honour a reduced-motion preference by skipping the animation entirely.
  if (
    typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  ) {
    return true
  }
  return false
}

export default function Reveal({
  children,
  className = '',
}: {
  children: ReactNode
  className?: string
}) {
  const ref = useRef<HTMLDivElement>(null)
  const [shown, setShown] = useState(shouldShowImmediately)

  // Runs before paint, so content already in the viewport is never rendered
  // invisible for even one frame.
  useLayoutEffect(() => {
    if (shown || !ref.current) return
    const { top, bottom } = ref.current.getBoundingClientRect()
    const viewportHeight = window.innerHeight || 0
    if (top < viewportHeight && bottom > 0) setShown(true)
  }, [shown])

  useEffect(() => {
    if (shown || !ref.current) return

    const reveal = () => setShown(true)

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) reveal()
      },
      // Fire slightly before the element reaches the viewport, so the content
      // is already settled by the time a shopper is looking at it.
      { rootMargin: '0px 0px -60px 0px', threshold: 0.05 },
    )
    observer.observe(ref.current)

    // If the tab is backgrounded while this is still waiting, stop waiting —
    // the observer will not fire again and the shopper would come back to a
    // blank grid.
    document.addEventListener('visibilitychange', reveal)

    // Last-resort backstop for anything the two paths above miss.
    const fallback = window.setTimeout(reveal, 1500)

    return () => {
      observer.disconnect()
      document.removeEventListener('visibilitychange', reveal)
      window.clearTimeout(fallback)
    }
  }, [shown])

  return (
    <div ref={ref} className={`reveal ${shown ? 'in' : ''} ${className}`.trim()}>
      {children}
    </div>
  )
}
