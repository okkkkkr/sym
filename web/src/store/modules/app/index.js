import { defineStore } from 'pinia'
import { lStorage } from '@/utils'
import i18n from '~/i18n'

const currentLocale = lStorage.get('locale')
const { locale } = i18n.global

if (typeof document !== 'undefined') {
  document.documentElement.classList.remove('dark')
}

export const useAppStore = defineStore('app', {
  state() {
    return {
      reloadFlag: true,
      collapsed: false,
      fullScreen: true,
      /** keepAlive路由的key，重新赋值可重置keepAlive */
      aliveKeys: {},
      isDark: false,
      locale: currentLocale || 'en',
    }
  },
  actions: {
    async reloadPage() {
      $loadingBar.start()
      this.reloadFlag = false
      await nextTick()
      this.reloadFlag = true

      setTimeout(() => {
        document.documentElement.scrollTo({ left: 0, top: 0 })
        $loadingBar.finish()
      }, 100)
    },
    switchCollapsed() {
      this.collapsed = !this.collapsed
    },
    setCollapsed(collapsed) {
      this.collapsed = collapsed
    },
    setFullScreen(fullScreen) {
      this.fullScreen = fullScreen
    },
    setAliveKeys(key, val) {
      this.aliveKeys[key] = val
    },
    /** 设置暗黑模式 */
    setDark(isDark) {
      this.isDark = false
      if (typeof document !== 'undefined') {
        document.documentElement.classList.remove('dark')
      }
    },
    /** 切换/关闭 暗黑模式 */
    toggleDark() {
      this.isDark = false
      if (typeof document !== 'undefined') {
        document.documentElement.classList.remove('dark')
      }
    },
    setLocale(newLocale) {
      this.locale = newLocale
      locale.value = newLocale
      lStorage.set('locale', newLocale)
    },
  },
})
