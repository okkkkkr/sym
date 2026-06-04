<script setup>
import { computed, onMounted, shallowRef } from 'vue'

import AnnouncementBar from '../components/site/AnnouncementBar.vue'
import MainNav from '../components/site/MainNav.vue'
import SiteFooter from '../components/site/SiteFooter.vue'
import { fetchHomeLayout } from '../services/home-layout'

const loading = shallowRef(true)
const error = shallowRef('')
const layout = shallowRef({
  common_config: {
    show_banner: true,
    show_navigation: true,
    show_footer: true,
  },
  modules: [],
})

const commonConfig = computed(() => layout.value.common_config || {})

async function loadHomeLayout() {
  loading.value = true
  error.value = ''
  try {
    layout.value = await fetchHomeLayout()
  } catch (loadError) {
    error.value = loadError.message || '首页内容加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadHomeLayout()
})
</script>

<template>
  <div class="home-layout">
    <AnnouncementBar v-if="commonConfig.show_banner" />
    <MainNav v-if="commonConfig.show_navigation" :show-categories="false" />
    <main class="home-layout__main">
      <router-view v-slot="{ Component }">
        <component :is="Component" :layout="layout" :loading="loading" :error="error" />
      </router-view>
    </main>
    <SiteFooter v-if="commonConfig.show_footer" />
  </div>
</template>

<style scoped>
.home-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #f7f5ef;
}

:deep(.page-container) {
  width: min(100%, 1800px);
}

:deep(.main-nav__inner) {
  border-bottom: 0;
  grid-template-columns: auto 1fr;
}

.home-layout__main {
  flex: 1 0 auto;
  width: 100%;
}
</style>
