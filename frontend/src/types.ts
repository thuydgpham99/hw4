/** Shapes returned by the Campus Customs API (see backend/db.py). */

export interface Product {
  product_id: string
  name: string
  garment_type: string
  /** Normalized category — the raw garment_type has 22 messy variants. */
  category: string
  description: string
  colors: string[]
  search_tags: string[]
  price: number
  image_url: string
}

export interface SizeStock {
  size: string
  quantity: number
  in_stock: boolean
}

/** A product plus its per-size inventory, from /api/products/{id}. */
export interface ProductDetail extends Product {
  sizes: SizeStock[]
  total_stock: number
  in_stock: boolean
}

export interface Category {
  name: string
  count: number
}

/** A signed-in shopper. Never includes password material. */
export interface User {
  id: number
  first_name: string | null
  last_name: string | null
  name: string
  email: string
  created_at: string
}

/** Chat response shape. `products` drives the matching items on the page. */
export interface ChatResponse {
  reply: string
  products: Product[]
  /** Issued by the backend; echo it back so follow-ups keep their context. */
  conversation_id?: string
  error?: string | null
}
