import { useState, useCallback } from 'react'
import { getToken, clearToken, getCart } from './api'
import LoginForm from './components/LoginForm'
import Navbar from './components/Navbar'
import ProductList from './components/ProductList'
import SearchPage from './components/SearchPage'
import Cart from './components/Cart'

export default function App() {
  const [token, setToken] = useState(getToken())
  const [page, setPage] = useState('products')
  const [cartCount, setCartCount] = useState(0)
  const [cartRefresh, setCartRefresh] = useState(0)

  const handleLogout = () => {
    clearToken()
    setToken(null)
  }

  const refreshCartCount = useCallback(async () => {
    try {
      const cart = await getCart()
      const count = (cart.items || []).reduce((s, i) => s + i.quantity, 0)
      setCartCount(count)
      setCartRefresh((prev) => prev + 1)
    } catch {
      // ignore — user may have logged out
    }
  }, [])

  if (!token) {
    return <LoginForm onLoginSuccess={(t) => { setToken(t); refreshCartCount() }} />
  }

  return (
    <div className="app">
      <Navbar
        currentPage={page}
        onNavigate={setPage}
        onLogout={handleLogout}
        cartCount={cartCount}
      />
      <main className="main-content">
        {page === 'products' && (
          <ProductList onCartUpdate={refreshCartCount} />
        )}
        {page === 'search' && (
          <SearchPage onCartUpdate={refreshCartCount} />
        )}
        {page === 'cart' && (
          <Cart refreshTrigger={cartRefresh} onCartUpdate={refreshCartCount} />
        )}
      </main>
    </div>
  )
}
