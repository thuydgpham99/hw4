import { useLocation } from 'react-router-dom'
import { useChatResults } from '../chatResults'
import ProductCard from './ProductCard'

/**
 * The band of product cards a chat search drops onto the page.
 *
 * Renders the same `ProductCard` the Products grid uses, so a card the chat put
 * on the page behaves identically to one the catalogue rendered — including
 * opening the single-item detail view when clicked.
 */
export default function ChatResultsStrip() {
  const { products, query, clear } = useChatResults()
  const { pathname } = useLocation()

  if (products.length === 0) return null

  // Hidden on a single-item page: the strip is tall, and leaving it in place
  // pushed the product detail a full screen below the fold — so clicking a card
  // appeared to do nothing. The results are kept in state and reappear on the
  // way back.
  if (/^\/products\/.+/.test(pathname)) return null

  return (
    <section className="chat-results">
      <div className="chat-results-inner">
        <div className="chat-results-head">
          <div>
            <h2>Picked out for you</h2>
            <p>
              {products.length} {products.length === 1 ? 'match' : 'matches'} for
              “{query}”
            </p>
          </div>
          <button className="chip" onClick={clear}>
            Clear
          </button>
        </div>
        <div className="product-grid">
          {products.map((product) => (
            <ProductCard key={product.product_id} product={product} />
          ))}
        </div>
      </div>
    </section>
  )
}
