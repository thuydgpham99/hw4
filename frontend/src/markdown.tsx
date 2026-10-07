/** Minimal Markdown renderer for agent replies.
 *
 * The agent emits a narrow, known subset — bold for prices and sizes, hyphen
 * bullets for product lists, blank lines between paragraphs. Rendering those
 * three constructs by hand avoids taking on a full Markdown dependency (and its
 * supply chain) to format what amounts to three characters of syntax.
 *
 * Anything that is not one of those constructs falls through as plain text, so
 * unexpected input can never break the panel.
 */

import type { ReactNode } from 'react'

/** Splits a line on **bold** spans. Unmatched asterisks stay as literal text. */
function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const parts: ReactNode[] = []
  const pattern = /\*\*(.+?)\*\*/g
  let lastIndex = 0
  let match: RegExpExecArray | null
  let i = 0

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index))
    }
    parts.push(<strong key={`${keyPrefix}-b${i++}`}>{match[1]}</strong>)
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < text.length) parts.push(text.slice(lastIndex))
  return parts.length > 0 ? parts : [text]
}

export function renderMarkdown(source: string): ReactNode {
  const lines = source.split('\n')
  const blocks: ReactNode[] = []

  let paragraph: string[] = []
  let bullets: string[] = []

  const flushParagraph = () => {
    if (paragraph.length === 0) return
    const text = paragraph.join(' ')
    blocks.push(
      <p key={`p${blocks.length}`} className="md-p">
        {renderInline(text, `p${blocks.length}`)}
      </p>,
    )
    paragraph = []
  }

  const flushBullets = () => {
    if (bullets.length === 0) return
    blocks.push(
      <ul key={`u${blocks.length}`} className="md-ul">
        {bullets.map((item, i) => (
          <li key={i}>{renderInline(item, `u${blocks.length}-${i}`)}</li>
        ))}
      </ul>,
    )
    bullets = []
  }

  for (const line of lines) {
    const trimmed = line.trim()

    if (trimmed === '') {
      flushBullets()
      flushParagraph()
      continue
    }

    const bullet = trimmed.match(/^[-*]\s+(.*)$/)
    if (bullet) {
      flushParagraph()
      bullets.push(bullet[1])
      continue
    }

    flushBullets()
    paragraph.push(trimmed)
  }

  flushBullets()
  flushParagraph()

  return <>{blocks}</>
}
