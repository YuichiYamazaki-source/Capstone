/**
 * api.js
 * Centralized API client for all backend calls.
 * Base URL is empty string (same-origin via nginx proxy on port 80).
 */

const API_BASE = ''

// ── Token Management ──

export function getToken() {
  return localStorage.getItem('token')
}

export function setToken(token) {
  localStorage.setItem('token', token)
}

export function clearToken() {
  localStorage.removeItem('token')
}

// ── Helper ──

async function authFetch(url, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }
  const res = await fetch(url, { ...options, headers })
  if (res.status === 401) {
    clearToken()
    throw new Error('Session expired. Please log in again.')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

// ── Auth ──

export async function login(email, password) {
  const data = await authFetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  // Backend returns { access_token, token_type }
  setToken(data.access_token)
  return data
}

// ── Products ──

export async function getProducts() {
  return authFetch(`${API_BASE}/products/`)
}

// ── AI Recommend ──

export async function recommend(query) {
  return authFetch(`${API_BASE}/products/recommend`, {
    method: 'POST',
    body: JSON.stringify({ query }),
  })
}

// ── Cart ──

export async function getCart() {
  return authFetch(`${API_BASE}/cart/`)
}

export async function addToCart(productId, quantity = 1) {
  return authFetch(`${API_BASE}/cart/items`, {
    method: 'POST',
    body: JSON.stringify({ product_id: productId, quantity }),
  })
}

export async function removeFromCart(productId) {
  return authFetch(`${API_BASE}/cart/items/${productId}`, {
    method: 'DELETE',
  })
}
