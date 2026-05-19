<script setup>
import AnnouncementBar from '../components/site/AnnouncementBar.vue'
import MainNav from '../components/site/MainNav.vue'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isProductRoute = computed(() => route.name === 'product')
</script>

<template>
  <div class="site-layout">
    <AnnouncementBar />
    <MainNav />
    <main
      class="site-layout__main pretty-scrollbar pretty-scrollbar--hover"
      :class="{ 'site-layout__main--locked': isProductRoute }"
    >
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.site-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: #f7f5ef;
}

.site-layout__main {
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}

.site-layout__main--locked {
  overflow: hidden;
}

@media (max-width: 900px) {
  .site-layout__main--locked {
    overflow-y: auto;
    overflow-x: hidden;
  }
}
</style>
