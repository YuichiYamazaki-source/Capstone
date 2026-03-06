import { useState } from 'react'
import { recommend } from '../api'

export default function SearchPage({ onCartUpdate }) {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setError('')
    setLoading(true)
    setResult(null)
    try {
      const data = await recommend(query)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <h2>AI Product Search</h2>
      <p className="hint">
        Try: &quot;summer casual outfit under 8000 yen&quot; or &quot;red dress&quot;
      </p>

      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          placeholder="Describe what you're looking for..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="search-input"
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="search-results">
          <div className="result-meta">
            <span>Model: {result.model_version}</span>
            <span>Query: &quot;{result.query}&quot;</span>
          </div>

          {result.products && result.products.length > 0 ? (
            <div className="product-grid">
              {result.products.map((p, idx) => (
                <div key={p.product_id || idx} className="product-card search-card">
                  <div className="product-info">
                    <h3>{p.name}</h3>
                    <span className="category">{p.category}</span>
                    <p className="description">{p.description}</p>
                    <div className="product-meta">
                      <span className="price">&yen;{p.price.toLocaleString()}</span>
                      <span className="score">
                        Score: {(p.similarity_score * 100).toFixed(1)}%
                      </span>
                      <span className="stock">Stock: {p.available_stock}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p>No products found.</p>
          )}

          {result.recommendations && (
            <div className="ai-summary">
              <h3>AI Summary</h3>
              <div className="summary-text">{result.recommendations}</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
