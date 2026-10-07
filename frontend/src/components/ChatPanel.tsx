import { useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { fetchChatHistory, formatPrice, sendChatMessage } from '../api'
import { getToken, useAuth } from '../auth'
import { useChatResults } from '../chatResults'
import { renderMarkdown } from '../markdown'
import type { Product } from '../types'

interface Message {
  role: 'user' | 'assistant'
  content: string
  /** Matching items the agent surfaced — rendered as cards under the reply. */
  products?: Product[]
}

/** Shown in an empty chat — the hardest part of a chat box is the blank one. */
const STARTERS = [
  'What hoodies do you have?',
  'Something warm for The Game',
  'Do you have XL in stock?',
]

const GREETING: Message = {
  role: 'assistant',
  content:
    "Hi! I'm the Campus Customs shop assistant. Ask me about any of our Yale " +
    'gear — sizes, colors, prices, what we have in stock — and I\'ll pull up ' +
    'what matches.',
}

/**
 * Floating chat panel, bottom right.
 *
 * Sends three things with every message: the text, the conversation id, and the
 * product page the shopper is on. When signed in it also sends the session
 * token, which is what gets the conversation saved and replayed on return.
 */
export default function ChatPanel() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([GREETING])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  // Issued by the backend on the first reply; echoed back on every turn after.
  const [conversationId, setConversationId] = useState<string | null>(null)
  const logRef = useRef<HTMLDivElement>(null)
  // Matches are pushed up to the page, not just rendered inside the panel.
  const { setResults } = useChatResults()
  const { user } = useAuth()
  // The page context the agent needs to resolve "do you have this in pink?".
  // Read from the path rather than useParams: this panel renders outside
  // <Routes>, so it has no route match of its own and useParams is always empty.
  const { pathname } = useLocation()
  const productId = pathname.match(/^\/products\/(.+)$/)?.[1]

  // Replay a signed-in shopper's saved conversation when they return.
  useEffect(() => {
    const token = getToken()
    if (!user || !token) {
      setMessages([GREETING])
      return
    }
    fetchChatHistory(token).then((saved) => {
      if (saved.length === 0) return
      setMessages([
        GREETING,
        ...saved.map((m) => ({
          role: m.role,
          content: m.content,
          products: m.products,
        })),
      ])
    })
  }, [user])

  // Keep the newest message in view as the conversation grows.
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [messages, open])

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    await send(draft)
  }

  async function send(raw: string) {
    const text = raw.trim()
    if (!text || sending) return

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setDraft('')
    setSending(true)

    try {
      const response = await sendChatMessage(text, conversationId, productId, getToken())
      if (response.conversation_id) setConversationId(response.conversation_id)
      setResults(response.products ?? [], text)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.reply,
          products: response.products,
        },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            "Sorry — I couldn't reach the shop assistant. Make sure the backend " +
            'is running and try again.',
        },
      ])
    } finally {
      setSending(false)
    }
  }

  if (!open) {
    return (
      <button className="chat-launcher" onClick={() => setOpen(true)}>
        <span>Chat with us</span>
      </button>
    )
  }

  return (
    <div className="chat-panel">
      <div className="chat-head">
        <div>
          <div className="chat-head-title">Campus Customs Assistant</div>
          <div className="chat-head-sub">Here to help you find your fit</div>
        </div>
        <button
          className="chat-close"
          onClick={() => setOpen(false)}
          aria-label="Close chat"
        >
          &times;
        </button>
      </div>

      <div className="chat-log" ref={logRef}>
        {messages.map((message, index) => (
          <Fragment key={index} message={message} />
        ))}
        {sending && (
          <div className="typing" aria-label="Assistant is typing">
            <span />
            <span />
            <span />
          </div>
        )}
      </div>

      {messages.length === 1 && !sending && (
        <div className="chat-suggestions">
          {STARTERS.map((starter) => (
            <button
              key={starter}
              className="chat-suggestion"
              onClick={() => send(starter)}
            >
              {starter}
            </button>
          ))}
        </div>
      )}

      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask about sizes, colors, prices…"
          aria-label="Message"
        />
        <button className="chat-send" type="submit" disabled={sending || !draft.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}

/** One turn: the text bubble plus any product cards that came with it. */
function Fragment({ message }: { message: Message }) {
  return (
    <>
      <div
        className={message.role === 'user' ? 'bubble bubble-user' : 'bubble bubble-bot'}
      >
        {message.role === 'assistant' ? renderMarkdown(message.content) : message.content}
      </div>
      {message.products && message.products.length > 0 && (
        <div className="chat-products">
          {message.products.map((product) => (
            <Link
              key={product.product_id}
              to={`/products/${product.product_id}`}
              className="chat-product"
            >
              <img src={product.image_url} alt={product.name} />
              <div>
                <div className="chat-product-name">{product.name}</div>
                <div className="chat-product-price">{formatPrice(product.price)}</div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </>
  )
}
