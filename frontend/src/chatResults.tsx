/** Products the chat agent most recently matched.
 *
 * The chat panel writes here; the page reads. Lifting the results out of the
 * panel is what lets a chat search update the website itself rather than only
 * the inside of the widget.
 */

import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type { Product } from './types'

interface ChatResultsState {
  products: Product[]
  /** The shopper message that produced them, shown as the section subtitle. */
  query: string
  setResults: (products: Product[], query: string) => void
  clear: () => void
}

const ChatResultsContext = createContext<ChatResultsState | null>(null)

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [products, setProducts] = useState<Product[]>([])
  const [query, setQuery] = useState('')

  const setResults = useCallback((next: Product[], nextQuery: string) => {
    // An empty result set should not wipe the strip — a follow-up like "does it
    // come in pink?" returns no new products but the previous matches are still
    // what the shopper is looking at.
    if (next.length === 0) return
    setProducts(next)
    setQuery(nextQuery)
  }, [])

  const clear = useCallback(() => {
    setProducts([])
    setQuery('')
  }, [])

  const value = useMemo(
    () => ({ products, query, setResults, clear }),
    [products, query, setResults, clear],
  )

  return (
    <ChatResultsContext.Provider value={value}>{children}</ChatResultsContext.Provider>
  )
}

export function useChatResults(): ChatResultsState {
  const context = useContext(ChatResultsContext)
  if (!context) throw new Error('useChatResults must be used inside a ChatResultsProvider')
  return context
}
