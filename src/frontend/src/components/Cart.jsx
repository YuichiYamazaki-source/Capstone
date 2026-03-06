import { useState, useEffect } from 'react'
import { getCart, removeFromCart } from '../api'

export default function Cart({ refreshTrigger, onCartUpdate }) {
  const [cart, setCart] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadCart()
  }, [refreshTrigger])

  const loadCart = async () => {
    setLoading(true)
    try {
      const data = await getCart()
      setCart(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRemove = async (productId) => {
    try {
      await removeFromCart(productId)
      await loadCart()
      if (onCartUpdate) onCartUpdate()
    } catch (err) {
      alert(err.message)
    }
  }

  if (loading) return <div className="loading">Loading cart...</div>
  if (error) return <div className="error">{error}</div>

  const items = cart?.items || []
  const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0)

  return (
    <div className="page">
      <h2>Shopping Cart</h2>
      {items.length === 0 ? (
        <p className="empty-cart">Your cart is empty.</p>
      ) : (
        <>
          <div className="cart-items">
            {items.map((item) => (
              <div key={item.product_id} className="cart-item">
                <div className="cart-item-info">
                  <h3>{item.name}</h3>
                  <span className="price">
                    &yen;{item.price.toLocaleString()} x {item.quantity}
                  </span>
                </div>
                <button
                  className="remove-btn"
                  onClick={() => handleRemove(item.product_id)}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
          <div className="cart-total">
            <strong>Total: &yen;{total.toLocaleString()}</strong>
          </div>
        </>
      )}
    </div>
  )
}
