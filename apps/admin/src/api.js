// API helper — all fetch calls go through here

import { getToken, clearToken } from './auth.js'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

/**
 * Make an API request. Automatically attaches Authorization header if token exists.
 * Returns parsed JSON on success; throws on HTTP error.
 */
export async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path}`
  const token = getToken()

  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(url, { ...options, headers })

  // If 401, clear token so the auth guard redirects to login
  if (res.status === 401) {
    clearToken()
    window.location.hash = '#/login'
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`API ${res.status}: ${text}`)
  }

  // DELETE may return 204 or a JSON body
  if (res.status === 204) return null
  return res.json()
}

// ── Auth ────────────────────────────────────────────────

export function login(username, password) {
  return apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

// ── Admin Posts ─────────────────────────────────────────

export function listPosts({ search, status, seo, limit, offset } = {}) {
  const params = new URLSearchParams()
  if (search && search.trim()) params.append('search', search.trim())
  if (status && status !== 'all') params.append('status', status)
  if (seo && seo !== 'all') params.append('seo', seo)
  if (limit !== undefined) params.append('limit', limit)
  if (offset !== undefined) params.append('offset', offset)
  
  const qs = params.toString()
  const path = qs ? `/admin/posts?${qs}` : '/admin/posts'
  return apiFetch(path)
}

export function getPost(id) {
  return apiFetch(`/admin/posts/${id}`)
}

export function createPost(data) {
  return apiFetch('/admin/posts', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updatePost(id, data) {
  return apiFetch(`/admin/posts/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function deletePost(id) {
  return apiFetch(`/admin/posts/${id}`, {
    method: 'DELETE',
  })
}

// ── Uploads ─────────────────────────────────────────────

/**
 * Upload a cover image. Uses FormData (not JSON) so we must
 * NOT set Content-Type — the browser sets the multipart boundary.
 */
export async function uploadCover(file) {
  const url = `${API_BASE}/admin/uploads/cover`
  const token = getToken()

  const body = new FormData()
  body.append('file', file)

  const headers = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(url, { method: 'POST', headers, body })

  if (res.status === 401) {
    clearToken()
    window.location.hash = '#/login'
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`Upload failed (${res.status}): ${text}`)
  }

  return res.json()
}

// ── Cover upload management ─────────────────────────────

export function listCoverUploads() {
  return apiFetch('/admin/uploads/covers')
}

export function deleteCoverUpload(filename) {
  return apiFetch(`/admin/uploads/covers/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  })
}
