import { apiUrl, sendApiBeacon } from './http'

export async function fetchActiveBanners() {
  const response = await fetch(apiUrl('/base/banners'))
  const payload = await response.json()

  if (!response.ok) {
    throw new Error(payload.message || payload.msg || '加载横幅失败')
  }

  return Array.isArray(payload.data) ? payload.data : []
}

async function postBannerTracking(body) {
  const response = await fetch(apiUrl('/base/track/banner-click'), {
    method: 'POST',
    keepalive: true,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })

  const payload = await response.json()
  if (!response.ok) {
    throw new Error(payload.message || payload.msg || '横幅点击上报失败')
  }

  return payload.data || {}
}

export async function reportBannerClick(bannerId, options = {}) {
  const normalizedBannerId = Number.parseInt(String(bannerId), 10)
  if (!Number.isInteger(normalizedBannerId) || normalizedBannerId <= 0) {
    return false
  }

  const payload = {
    banner_id: normalizedBannerId,
  }

  if (options.transport !== 'fetch' && sendApiBeacon('/base/track/banner-click', payload)) {
    return true
  }

  try {
    await postBannerTracking(payload)
    return true
  } catch (error) {
    console.warn('reportBannerClick error', error)
    return false
  }
}
