<script setup>
defineProps({
  title: {
    type: String,
    default: '',
  },
  action: {
    type: Object,
    default: () => ({}),
  },
})
</script>

<template>
  <header v-if="title || action.text" class="home-section-header">
    <h2 v-if="title">{{ title }}</h2>
    <a v-if="action.text && action.link" class="home-section-header__action" :href="action.link" :target="action.target === 'blank' ? '_blank' : undefined">
      {{ action.text }}
    </a>
  </header>
</template>

<style scoped>
.home-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.home-section-header h2 {
  font-size: clamp(30px, 3vw, 44px);
  line-height: 1.05;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.home-section-header__action {
  color: #3f3a34;
  font-size: 15px;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .home-section-header {
    margin-bottom: 18px;
  }

  .home-section-header h2 {
    font-size: 22px;
  }
}
</style>
