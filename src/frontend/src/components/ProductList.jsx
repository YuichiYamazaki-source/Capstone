import { useState, useEffect } from 'react'
import { getProducts, addToCart } from '../api'

export default function ProductList({ onCartUpdate }) {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [addingId, setAddingId] = useState(null)

  useEffect(() => {
    loadProducts()
  }, [])

  const loadProducts = async () => {
    try {
      const data = await getProducts()
      setProducts(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAddToCart = async (productId) => {
    setAddingId(productId)
    try {
      await addToCart(productId, 1)
      if (onCartUpdate) onCartUpdate()
    } catch (err) {
      alert(err.message)
    } finally {
      setAddingId(null)
    }
  }

  if (loading) return <div className="loading">Loading products...</div>
  if (error) return <div className="error">{error}</div>

  return (
    <div className="page">
      <h2>Products ({products.length})</h2>
      <div className="product-grid">
        {products.map((p) => (
          <div key={p.product_id} className="product-card">
            <div className="product-info">
              <h3>{p.name}</h3>
              <span className="category">{p.category}</span>
              <p className="description">{p.description}</p>
              <div className="product-meta">
                <span className="price">&yen;{p.price.toLocaleString()}</span>
                <span className="stock">Stock: {p.available_stock}</span>
              </div>
            </div>
            <button
              className="add-cart-btn"
              onClick={() => handleAddToCart(p.product_id)}
              disabled={addingId === p.product_id}
            >
              {addingId === p.product_id ? 'Adding...' : 'Add to Cart'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
