import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice } from '../api'
import type { ProductDetail as ProductDetailType } from '../types'

/** Rough CSS color for a swatch dot from the catalogue's color words. */
const SWATCH_COLORS: Record<string, string> = {
  'navy blue': '#00356b',
  navy: '#00356b',
  white: '#ffffff',
  'heather gray': '#b6b6b6',
  gray: '#8e8e8e',
  grey: '#8e8e8e',
  black: '#1a1a1a',
  red: '#c8102e',
  blue: '#2f6fb5',
  'light blue': '#8fc1e3',
  yellow: '#f4c430',
  gold: '#c9a227',
  green: '#2e6f44',
  cream: '#f3ead6',
  charcoal: '#36454f',
  maroon: '#6b2131',
  pink: '#e8a0b4',
  orange: '#e2671d',
  purple: '#5b4b8a',
  tan: '#d2b48c',
  brown: '#6b4a2f',
  silver: '#c9ccd1',
}

/** Single-item page: large image on one side, full product text on the other. */
export default function ProductDetail() {
  const { productId } = useParams<{ productId: string }>()
  const [product, setProduct] = useState<ProductDetailType | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!productId) return
    setProduct(null)
    setError(null)
    window.scrollTo(0, 0)
    fetchProduct(productId)
      .then(setProduct)
      .catch(() => setError('We could not find that product.'))
  }, [productId])

  if (error) {
    return (
      <div className="page">
        <div className="state state-error">{error}</div>
        <div style={{ textAlign: 'center' }}>
          <Link to="/products" className="btn btn-primary">
            Back to all products
          </Link>
        </div>
      </div>
    )
  }

  if (!product) {
    return (
      <div className="page">
        <div className="state">Loading…</div>
      </div>
    )
  }

  const availableSizes = product.sizes.filter((s) => s.in_stock)

  return (
    <div className="page">
      <Link to="/products" className="back-link">
        ← Back to all products
      </Link>

      <div className="detail-layout">
        <div className="detail-image">
          <img src={product.image_url} alt={product.name} />
        </div>

        <div>
          <div className="detail-type">{product.category}</div>
          <h1 className="detail-title">{product.name}</h1>
          <div className="detail-price">{formatPrice(product.price)}</div>

          <p className="detail-desc">{product.description}</p>

          <div className="detail-block">
            <h3>Availability</h3>
            {availableSizes.length === 0 ? (
              <span className="badge badge-out">Sold out in every size</span>
            ) : (
              <span className="badge badge-in">
                In stock in {availableSizes.length} of {product.sizes.length} sizes
              </span>
            )}
          </div>

          <div className="detail-block">
            <h3>Size &amp; Stock</h3>
            <div className="size-grid">
              {product.sizes.map((size) => (
                <div
                  key={size.size}
                  className={size.in_stock ? 'size-box' : 'size-box out'}
                >
                  <div className="size-box-label">{size.size}</div>
                  <div className="size-box-stock">
                    {size.in_stock ? `${size.quantity} left` : 'Out of stock'}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {product.colors.length > 0 && (
            <div className="detail-block">
              <h3>Colors</h3>
              <div className="swatch-row">
                {product.colors.map((color) => (
                  <span key={color} className="swatch">
                    <span
                      className="swatch-dot"
                      style={{
                        background: SWATCH_COLORS[color.toLowerCase()] ?? '#dfe6ef',
                      }}
                    />
                    {color}
                  </span>
                ))}
              </div>
            </div>
          )}

          {product.search_tags.length > 0 && (
            <div className="detail-block">
              <h3>Details</h3>
              <div className="tag-row">
                {product.search_tags.map((tag) => (
                  <span key={tag} className="tag">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          <button className="btn btn-primary btn-block" disabled={availableSizes.length === 0}>
            {availableSizes.length === 0 ? 'Sold Out' : 'Add to Bag'}
          </button>
        </div>
      </div>
    </div>
  )
}
