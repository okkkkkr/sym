<script setup>
import SiteFooter from '../components/site/SiteFooter.vue'
</script>

<template>
  <div class="home-layout">
    <main class="home-layout__main">
      <router-view />
    </main>
    <SiteFooter />
  </div>
</template>

<style scoped>
.home-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #f7f5ef;
}

.home-layout__main {
  flex: 1 0 auto;
  width: 100%;
}
</style>