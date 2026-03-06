export default function Navbar({ currentPage, onNavigate, onLogout, cartCount }) {
  return (
    <nav className="navbar">
      <div className="nav-brand">AI Commerce</div>
      <div className="nav-links">
        <button
          className={currentPage === 'products' ? 'active' : ''}
          onClick={() => onNavigate('products')}
        >
          Products
        </button>
        <button
          className={currentPage === 'search' ? 'active' : ''}
          onClick={() => onNavigate('search')}
        >
          AI Search
        </button>
        <button
          className={currentPage === 'cart' ? 'active' : ''}
          onClick={() => onNavigate('cart')}
        >
          Cart{cartCount > 0 ? ` (${cartCount})` : ''}
        </button>
      </div>
      <button className="logout-btn" onClick={onLogout}>
        Logout
      </button>
    </nav>
  )
}
