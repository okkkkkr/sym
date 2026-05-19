export async function fetchActiveContacts(contactType = '') {
  const query = new URLSearchParams()
  if (contactType) {
    query.set('contact_type', contactType)
  }

  const suffix = query.toString() ? `?${query.toString()}` : ''
  const response = await fetch(`/api/v1/base/contacts${suffix}`)
  const payload = await response.json()

  if (!response.ok) {
    throw new Error(payload.message || payload.msg || '加载联系方式失败')
  }

  return Array.isArray(payload.data) ? payload.data : []
}