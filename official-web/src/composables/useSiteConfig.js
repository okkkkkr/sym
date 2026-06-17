import { readonly, ref } from 'vue'
import { apiUrl } from '../services/http'

const emptySiteConfig = Object.freeze({
  logo_url: '',
  about_title: '',
  about_lines: [],
  footer_disclaimer: '',
  share_base_url: '',
})

const siteConfig = ref(emptySiteConfig)

let loaded = false
let pendingRequest = null

function normalizeSiteConfig(payload = {}) {
  return {
    logo_url: String(payload.logo_url || '').trim(),
    about_title: String(payload.about_title || '').trim(),
    about_lines: Array.isArray(payload.about_lines)
      ? payload.about_lines.map((item) => String(item).trim()).filter(Boolean)
      : [],
    footer_disclaimer: String(payload.footer_disclaimer || '').trim(),
    share_base_url: String(payload.share_base_url || '').trim(),
  }
}

async function fetchPublicSiteConfig() {
  const response = await fetch(apiUrl('/base/site-config'))
  const payload = await response.json()

  if (!response.ok) {
    throw new Error(payload.message || payload.msg || '加载站点配置失败')
  }

  return normalizeSiteConfig(payload.data || {})
}

export function useSiteConfig() {
  async function loadSiteConfig(force = false) {
    if (!force && loaded) {
      return siteConfig.value
    }

    if (!force && pendingRequest) {
      return pendingRequest
    }

    pendingRequest = fetchPublicSiteConfig()
      .then((data) => {
        siteConfig.value = data
        loaded = true
        return data
      })
      .catch((error) => {
        siteConfig.value = emptySiteConfig
        loaded = false
        throw error
      })
      .finally(() => {
        pendingRequest = null
      })

    return pendingRequest
  }

  return {
    siteConfig: readonly(siteConfig),
    loadSiteConfig,
  }
}
