const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? 'https://api.symluxlib.com/api/v1' : '/api/v1')
).replace(/\/$/, '')

export function apiUrl(path) {
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}

export function sendApiBeacon(path, body) {
  if (typeof navigator === 'undefined' || typeof navigator.sendBeacon !== 'function') {
    return false
  }

  return navigator.sendBeacon(
    apiUrl(path),
    new Blob([JSON.stringify(body)], {
      type: 'application/json',
    }),
  )
}
