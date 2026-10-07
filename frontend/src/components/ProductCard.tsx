import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import type { Product } from '../types'

/** Catalogue tile. The whole card is the link through to the single-item page. */
export default function ProductCard({ product }: { product: Product }) {
  return (
    <Link to={`/products/${product.product_id}`} className="product-card">
      <div className="product-card-image">
        <img src={product.image_url} alt={product.name} loading="lazy" />
      </div>
      <div className="product-card-body">
        <div className="product-card-type">{product.category}</div>
        <div className="product-card-name">{product.name}</div>
        <p className="product-card-desc">{product.description}</p>
        <div className="product-card-price">{formatPrice(product.price)}</div>
      </div>
    </Link>
  )
}
