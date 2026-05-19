<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const titleMap = {
  bag: 'BAG',
  shoes: 'SHOES',
  sunglasses: 'SUNGLASSES',
  watch: 'WATCH',
}

const pageTitle = computed(() => {
  const category = String(route.query.category ?? 'bag').toLowerCase()
  return titleMap[category] ?? titleMap.bag
})
</script>

<template>
  <section class="page-intro page-container">
    <h1>{{ pageTitle }}</h1>
    <p></p>
  </section>
</template>

<style scoped>
.page-intro {
  padding: 30px 24px 26px;
  border-bottom: 2px solid #1f1f1f;
}

.page-intro h1 {
  margin: 0;
  color: #0e0e0e;
  font-size: clamp(58px, 8vw, 72px);
  font-weight: 900;
  line-height: 0.92;
  letter-spacing: 0.01em;
}

.page-intro p {
  max-width: 520px;
  color: #1f1f1f;
  font-size: 13px;
  line-height: 1.9;
}

@media (max-width: 767px) {
  .page-intro {
    padding: 32px 16px 28px;
  }
}
</style>
