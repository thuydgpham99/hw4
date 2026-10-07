/** Thin fetch wrapper around the Campus Customs API.
 *
 * Paths are origin-relative; Vite proxies /api to FastAPI on :8000 in dev.
 */

import type { Category, ChatResponse, Product, ProductDetail } from './types'

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) {
    throw new Error(`Request failed (${res.status}) for ${path}`)
  }
  return res.json() as Promise<T>
}

export async function fetchProducts(
  params: {
    category?: string
    search?: string
    size?: string
    inStock?: boolean
  } = {},
): Promise<{ products: Product[]; count: number; total: number }> {
  const query = new URLSearchParams()
  if (params.category && params.category !== 'All') query.set('category', params.category)
  if (params.search) query.set('search', params.search)
  if (params.size) query.set('size', params.size)
  if (params.inStock) query.set('in_stock', 'true')
  const suffix = query.toString() ? `?${query}` : ''
  const data = await getJSON<{ count: number; total: number; products: Product[] }>(
    `/api/products${suffix}`,
  )
  return { products: data.products, count: data.count, total: data.total ?? data.count }
}

export async function fetchProduct(productId: string): Promise<ProductDetail> {
  return getJSON<ProductDetail>(`/api/products/${productId}`)
}

export async function fetchCategories(): Promise<Category[]> {
  const data = await getJSON<{ categories: Category[] }>('/api/categories')
  return data.categories
}

export async function sendChatMessage(
  message: string,
  conversationId?: string | null,
  currentProductId?: string | null,
  token?: string | null,
): Promise<ChatResponse> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  // Sent when signed in: the backend uses it to greet by name and save history.
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch('/api/chat', {
    method: 'POST',
    headers,
    body: JSON.stringify({
      message,
      // Echoing the conversation id back is what lets the agent resolve
      // follow-ups like "do you have that in pink?".
      conversation_id: conversationId ?? null,
      // The product page they are on, so "this" has a referent.
      current_product_id: currentProductId ?? null,
    }),
  })
  if (!res.ok) throw new Error(`Chat request failed (${res.status})`)
  return res.json() as Promise<ChatResponse>
}

/** A signed-in shopper's saved conversation, replayed when they return. */
export async function fetchChatHistory(token: string): Promise<
  { role: 'user' | 'assistant'; content: string; products: Product[] }[]
> {
  const res = await fetch('/api/chat/history', {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) return []
  const data = await res.json()
  return data.messages ?? []
}

/** Formats cents-free catalogue prices as $68 rather than $68.00. */
export function formatPrice(price: number): string {
  return `$${Number.isInteger(price) ? price : price.toFixed(2)}`
}
