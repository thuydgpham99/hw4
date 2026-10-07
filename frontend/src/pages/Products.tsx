import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchCategories, fetchProducts } from '../api'
import ProductCard from '../components/ProductCard'
import Reveal from '../components/Reveal'
import type { Category, Product } from '../types'

const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']

/** Catalogue page: category chips, text search, and the product grid. */
export default function Products() {
  const [searchParams, setSearchParams] = useSearchParams()
  const activeCategory = searchParams.get('category') ?? 'All'

  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [search, setSearch] = useState('')
  // Stock-aware filters: 145 of 612 size rows are at zero, so browsing without
  // these means clicking into products that cannot be sold to you.
  const [sizeFilter, setSizeFilter] = useState<string>('')
  const [inStockOnly, setInStockOnly] = useState(false)
  const [resultTotal, setResultTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => setCategories([]))
  }, [])

  useEffect(() => {
    setLoading(true)
    // Debounced so typing in the search box does not fire a request per keypress.
    const timer = setTimeout(() => {
      fetchProducts({
        category: activeCategory,
        search,
        size: sizeFilter || undefined,
        inStock: inStockOnly,
      })
        .then((result) => {
          setProducts(result.products)
          setResultTotal(result.total)
          setError(null)
        })
        .catch(() => setError('We could not load the catalogue. Is the backend running?'))
        .finally(() => setLoading(false))
    }, 220)
    return () => clearTimeout(timer)
  }, [activeCategory, search, sizeFilter, inStockOnly])

  function selectCategory(name: string) {
    if (name === 'All') {
      searchParams.delete('category')
    } else {
      searchParams.set('category', name)
    }
    setSearchParams(searchParams, { replace: true })
  }

  const total = categories.reduce((sum, c) => sum + c.count, 0)

  return (
    <div className="page">
      <div className="section-head">
        <h2>The Collection</h2>
        <p>Everything on our shelves, straight from the stockroom.</p>
      </div>

      <div className="toolbar">
        <div className="chip-row">
          <button
            className={activeCategory === 'All' ? 'chip active' : 'chip'}
            onClick={() => selectCategory('All')}
          >
            All
            {total > 0 && <span className="chip-count">{total}</span>}
          </button>
          {categories.map((category) => (
            <button
              key={category.name}
              className={activeCategory === category.name ? 'chip active' : 'chip'}
              onClick={() => selectCategory(category.name)}
            >
              {category.name}
              <span className="chip-count">{category.count}</span>
            </button>
          ))}
        </div>

        <input
          className="search-input"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search for navy, bulldog, The Game…"
          aria-label="Search products"
        />
      </div>

      <div className="filter-bar">
        <div className="filter-group">
          <span className="filter-label">My size</span>
          <div className="chip-row">
            <button
              className={sizeFilter === '' ? 'chip chip-sm active' : 'chip chip-sm'}
              onClick={() => setSizeFilter('')}
            >
              Any
            </button>
            {SIZES.map((size) => (
              <button
                key={size}
                className={sizeFilter === size ? 'chip chip-sm active' : 'chip chip-sm'}
                onClick={() => setSizeFilter(sizeFilter === size ? '' : size)}
              >
                {size}
              </button>
            ))}
          </div>
        </div>

        <label className="toggle">
          <input
            type="checkbox"
            checked={inStockOnly}
            onChange={(e) => setInStockOnly(e.target.checked)}
          />
          <span>In stock only</span>
        </label>
      </div>

      {error ? (
        <div className="state state-error">{error}</div>
      ) : loading ? (
        <div className="state">Loading products…</div>
      ) : products.length === 0 ? (
        <div className="state">
          {sizeFilter
            ? `Nothing here is in stock in ${sizeFilter} right now. Try another size, or clear the filter.`
            : 'Nothing matched that search. Try a color, a sport, or a garment type.'}
        </div>
      ) : (
        <>
          <p className="result-count">
            Showing {products.length} of {resultTotal}{' '}
            {resultTotal === 1 ? 'item' : 'items'}
            {sizeFilter && <> · in stock in <strong>{sizeFilter}</strong></>}
            {inStockOnly && !sizeFilter && <> · in stock</>}
          </p>
          <div className="product-grid">
            {products.map((product) => (
              <Reveal key={product.product_id}>
                <ProductCard product={product} />
              </Reveal>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
