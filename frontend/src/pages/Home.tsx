import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchCategories, fetchProducts } from '../api'
import ProductCard from '../components/ProductCard'
import Reveal from '../components/Reveal'
import type { Category, Product } from '../types'

/** Landing page: hero, why-shop-here strip, category tiles, featured grid. */
export default function Home() {
  const [featured, setFeatured] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([fetchProducts(), fetchCategories()])
      .then(([productsResult, cats]) => {
        const products = productsResult.products
        // A spread of categories reads better on the landing page than the
        // first eight alphabetically, which would be all crewnecks.
        const picks: Product[] = []
        const seen = new Map<string, number>()
        for (const product of products) {
          const count = seen.get(product.category) ?? 0
          if (count < 2) {
            picks.push(product)
            seen.set(product.category, count + 1)
          }
          if (picks.length === 8) break
        }
        setFeatured(picks)
        setCategories(cats)
      })
      .catch(() => setError('We could not load the catalogue. Is the backend running?'))
  }, [])

  return (
    <>
      <section className="hero">
        <div className="hero-kicker">New Haven · Since Game Day</div>
        <h1>
          Wear It Like <em>You Mean It</em>
        </h1>
        <p>
          Yale gear made for walking to class in February, for the stands at The
          Game, and for the parents who want to show up looking like they belong
          here too.
        </p>
        <div className="hero-actions">
          <Link to="/products" className="btn btn-accent">
            Shop the Collection
          </Link>
          <Link to="/about" className="btn btn-outline">
            Our Story
          </Link>
        </div>
      </section>

      <div className="page">
        <Reveal>
        <div className="feature-row">
          <div className="feature">
            <h3>Built for New Haven weather</h3>
            <p>
              Heavyweight fleece, real cotton, and quarter-zips that hold their
              shape past midterms.
            </p>
          </div>
          <div className="feature">
            <h3>Straight answers on stock</h3>
            <p>
              Every size shown on this site comes from our shelf count. If it's
              gone, we say it's gone.
            </p>
          </div>
          <div className="feature">
            <h3>Officially licensed</h3>
            <p>
              Every piece is approved Yale merchandise, printed and stitched to
              the university's standards.
            </p>
          </div>
        </div>
        </Reveal>

        {categories.length > 0 && (
          <>
            <div className="section-head">
              <h2>Shop by Category</h2>
              <p>Six ways into a closet full of blue.</p>
            </div>
            <div className="category-strip">
              {categories.map((category) => (
                <Link
                  key={category.name}
                  to={`/products?category=${encodeURIComponent(category.name)}`}
                  className="category-tile"
                >
                  <div className="category-tile-name">{category.name}</div>
                  <div className="category-tile-count">{category.count} items</div>
                </Link>
              ))}
            </div>
          </>
        )}

        <div className="section-head">
          <h2>Fresh Off the Rack</h2>
          <p>A few favorites from every corner of the store.</p>
        </div>

        {error ? (
          <div className="state state-error">{error}</div>
        ) : featured.length === 0 ? (
          <div className="state">Loading the good stuff…</div>
        ) : (
          <>
            <div className="product-grid">
              {featured.map((product) => (
                <Reveal key={product.product_id}>
                  <ProductCard product={product} />
                </Reveal>
              ))}
            </div>
            <div style={{ textAlign: 'center', marginTop: '2.5rem' }}>
              <Link to="/products" className="btn btn-primary">
                See all products
              </Link>
            </div>
          </>
        )}
      </div>
    </>
  )
}
