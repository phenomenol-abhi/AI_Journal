const STORAGE_KEY = 'inkwell_auth'

export function getAuth() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY))
  } catch {
    return null
  }
}

export function setAuth(auth) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(auth))
}

export function clearAuth() {
  localStorage.removeItem(STORAGE_KEY)
}

export async function api(path, { method = 'GET', body } = {}) {
  const auth = getAuth()
  const headers = {}
  if (body) headers['Content-Type'] = 'application/json'
  if (auth?.access) headers['Authorization'] = `Bearer ${auth.access}`
  const response = await fetch(`/api${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    const detail =
      typeof data.detail === 'string'
        ? data.detail
        : Object.values(data)[0] || `Request failed (${response.status})`
    const error = new Error(Array.isArray(detail) ? detail[0] : detail)
    error.status = response.status
    throw error
  }
  if (response.status === 204) return null
  return response.json()
}

export function wsUrl() {
  const token = getAuth()?.access
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/ws/chat/?token=${encodeURIComponent(token)}`
}
