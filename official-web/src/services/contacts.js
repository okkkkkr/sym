import { getOrCreateVisitorId } from './catalog'
import { apiUrl, sendApiBeacon } from './http'

const CONTACT_CLICK_TS_STORAGE_KEY_PREFIX = 'sym:last-contact-click-track-at:'
const CONTACT_CLICK_WINDOW_MS = 30 * 60 * 1000

export async function fetchActiveContacts(contactType = '') {
  const query = new URLSearchParams()
  if (contactType) {
    query.set('contact_type', contactType)
  }

  const suffix = query.toString() ? `?${query.toString()}` : ''
  const response = await fetch(apiUrl(`/base/contacts${suffix}`))
  const payload = await response.json()

  if (!response.ok) {
    throw new Error(payload.message || payload.msg || '加载联系方式失败')
  }

  return Array.isArray(payload.data) ? payload.data : []
}

function getStorage() {
  if (typeof window === 'undefined') {
    return null
  }

  return window.localStorage
}

async function postContactTracking(body) {
  const response = await fetch(apiUrl('/base/track/contact-click'), {
    method: 'POST',
    keepalive: true,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })

  const payload = await response.json()
  if (!response.ok) {
    throw new Error(payload.message || payload.msg || '联系方式点击上报失败')
  }

  return payload.data || {}
}

export async function reportContactClick(contactId, options = {}) {
  const normalizedContactId = Number.parseInt(String(contactId), 10)
  const visitorId = getOrCreateVisitorId()
  const storage = getStorage()
  if (!Number.isInteger(normalizedContactId) || normalizedContactId <= 0 || !visitorId || !storage) {
    return false
  }

  const storageKey = `${CONTACT_CLICK_TS_STORAGE_KEY_PREFIX}${normalizedContactId}`
  const lastTrackedAt = Number.parseInt(storage.getItem(storageKey) || '0', 10)
  if (Number.isFinite(lastTrackedAt) && lastTrackedAt > 0 && Date.now() - lastTrackedAt < CONTACT_CLICK_WINDOW_MS) {
    return false
  }

  const payload = {
    visitor_id: visitorId,
    contact_id: normalizedContactId,
  }

  if (options.transport !== 'fetch' && sendApiBeacon('/base/track/contact-click', payload)) {
    storage.setItem(storageKey, String(Date.now()))
    return true
  }

  try {
    await postContactTracking(payload)
    storage.setItem(storageKey, String(Date.now()))
    return true
  } catch (error) {
    console.warn('reportContactClick error', error)
    return false
  }
}
