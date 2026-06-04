function normalizeCommonConfig(commonConfig = {}) {
  return {
    show_banner: commonConfig.show_banner !== false,
    show_navigation: commonConfig.show_navigation !== false,
    show_footer: commonConfig.show_footer !== false,
  }
}

export async function fetchHomeLayout() {
  const response = await fetch('/api/v1/base/home-layout')
  const payload = await response.json()

  if (!response.ok || payload?.code !== 200) {
    throw new Error(payload.message || payload.msg || '加载首页装修失败')
  }

  const data = payload.data || { page_code: 'home', version: 0, modules: [] }
  return {
    ...data,
    common_config: normalizeCommonConfig(data.common_config),
    modules: Array.isArray(data.modules) ? data.modules : [],
  }
}
