export function normalizeCategoryKey(category) {
  return String(category || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

export function resolveCategoryKey(categories = [], category = '') {
  const normalizedKey = normalizeCategoryKey(category)
  if (normalizedKey && categories.some((item) => item.key === normalizedKey)) {
    return normalizedKey
  }

  return categories[0]?.key || ''
}

export async function fetchCatalogCategories() {
  const response = await fetch('/api/v1/base/categories')
  const payload = await response.json()

  if (!response.ok) {
    throw new Error(payload.message || payload.msg || '加载分类导航失败')
  }

  return Array.isArray(payload.data) ? payload.data : []
}

export async function fetchCatalog(options = {}) {
  const currentCategory = normalizeCategoryKey(options.category)
  const query = new URLSearchParams()

  query.set('category', currentCategory)

  const keyword = String(options.keyword || '').trim()
  const brandIds = Array.isArray(options.brandIds) ? options.brandIds.filter(Boolean) : []
  const tagIds = Array.isArray(options.tagIds) ? options.tagIds.filter(Boolean) : []
  const page = Number.parseInt(options.page, 10)
  const pageSize = Number.parseInt(options.pageSize, 10)

  if (keyword) {
    query.set('keyword', keyword)
  }

  if (brandIds.length) {
    query.set('brand', brandIds.join(','))
  }

  if (tagIds.length) {
    query.set('tag', tagIds.join(','))
  }

  if (Number.isInteger(page) && page > 1) {
    query.set('page', String(page))
  }

  if (Number.isInteger(pageSize) && pageSize > 0) {
    query.set('page_size', String(pageSize))
  }

  const response = await fetch(`/api/v1/base/catalog?${query.toString()}`)
  const payload = await response.json()

  if (!response.ok) {
    throw new Error(payload.message || payload.msg || '加载好物列表失败')
  }

  return payload.data || { category: '', categoryLabel: '', brands: [], hotBrands: [], hotTags: [], products: [], total: 0, page: 1, pageSize: 24 }
}

export async function fetchCatalogProduct(productId) {
  const response = await fetch(`/api/v1/base/catalog/products/${encodeURIComponent(productId)}`)
  const payload = await response.json()

  if (!response.ok) {
    throw new Error(payload.message || payload.msg || '加载好物详情失败')
  }

  return payload.data || {}
}

const VISITOR_ID_STORAGE_KEY = 'sym-fast:visitor-id'
const VISIT_TS_STORAGE_KEY = 'sym-fast:last-visit-track-at'
const CHANNEL_VISIT_TS_STORAGE_KEY_PREFIX = 'sym-fast:last-channel-visit-track-at:'
const VISIT_THROTTLE_MS = 30 * 60 * 1000

function createVisitorId() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID().replace(/-/g, '')
  }

  return `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 12)}`
}

function getStorage() {
  if (typeof window === 'undefined') {
    return null
  }

  return window.localStorage
}

export function getOrCreateVisitorId() {
  const storage = getStorage()

  if (!storage) {
    return ''
  }

  const cachedVisitorId = String(storage.getItem(VISITOR_ID_STORAGE_KEY) || '').trim()
  if (cachedVisitorId) {
    return cachedVisitorId
  }

  const visitorId = createVisitorId()
  storage.setItem(VISITOR_ID_STORAGE_KEY, visitorId)
  return visitorId
}

function shouldTrackSiteVisit() {
  const storage = getStorage()
  if (!storage) {
    return false
  }

  const lastTrackedAt = Number.parseInt(storage.getItem(VISIT_TS_STORAGE_KEY) || '0', 10)
  if (!Number.isFinite(lastTrackedAt) || lastTrackedAt <= 0) {
    return true
  }

  return Date.now() - lastTrackedAt >= VISIT_THROTTLE_MS
}

function markSiteVisitTracked() {
  const storage = getStorage()
  if (!storage) {
    return
  }

  storage.setItem(VISIT_TS_STORAGE_KEY, String(Date.now()))
}

async function postTracking(url, body) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })

  const payload = await response.json()

  if (!response.ok) {
    throw new Error(payload.message || payload.msg || '统计上报失败')
  }

  return payload.data || {}
}

export async function reportProductClick(productId) {
  try {
    await postTracking('/api/v1/base/track/product-click', {
      product_id: Number.parseInt(String(productId), 10),
    })
    return true
  } catch (error) {
    console.warn('reportProductClick error', error)
    return false
  }
}

export async function reportBrandSearch(brandIds = []) {
  const normalizedBrandIds = brandIds
    .map((brandId) => Number.parseInt(String(brandId), 10))
    .filter((brandId) => Number.isInteger(brandId) && brandId > 0)

  if (!normalizedBrandIds.length) {
    return false
  }

  try {
    await postTracking('/api/v1/base/track/brand-search', {
      brand_ids: normalizedBrandIds,
    })
    return true
  } catch (error) {
    console.warn('reportBrandSearch error', error)
    return false
  }
}

export async function reportSiteVisit(path = '') {
  if (!shouldTrackSiteVisit()) {
    return false
  }

  const visitorId = getOrCreateVisitorId()
  if (!visitorId) {
    return false
  }

  try {
    await postTracking('/api/v1/base/track/site-visit', {
      visitor_id: visitorId,
      path: path || window.location.pathname || '/',
    })
    markSiteVisitTracked()
    return true
  } catch (error) {
    console.warn('reportSiteVisit error', error)
    return false
  }
}

export async function reportChannelVisit() {
  const visitorId = getOrCreateVisitorId()
  const storage = getStorage()
  if (!visitorId || !storage) {
    return false
  }

  const plat = new URLSearchParams(window.location.search).get('plat') || ''
  const storageKey = `${CHANNEL_VISIT_TS_STORAGE_KEY_PREFIX}${plat || 'nature'}`
  const lastTrackedAt = Number.parseInt(storage.getItem(storageKey) || '0', 10)
  if (Number.isFinite(lastTrackedAt) && lastTrackedAt > 0 && Date.now() - lastTrackedAt < VISIT_THROTTLE_MS) {
    return false
  }

  try {
    await postTracking('/api/v1/base/track/channel-visit', {
      visitor_id: visitorId,
      plat,
    })
    storage.setItem(storageKey, String(Date.now()))
    return true
  } catch (error) {
    console.warn('reportChannelVisit error', error)
    return false
  }
}
