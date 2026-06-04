<script setup>
import HomeSectionHeader from './HomeSectionHeader.vue'

defineProps({
  module: {
    type: Object,
    required: true,
  },
  columns: {
    type: String,
    required: true,
  },
})
</script>

<template>
  <section class="home-grid page-container">
    <HomeSectionHeader :title="module.title" :action="module.action || {}" />
    <div class="home-grid__list" :class="columns">
      <a
        v-for="item in module.items"
        :key="item.id || item.sort"
        class="home-grid__card"
        :href="item.action?.link || undefined"
        :target="item.action?.target === 'blank' ? '_blank' : undefined"
      >
        <div class="home-grid__image-wrap">
          <img v-if="item.image" :src="item.image" :alt="item.title || module.title || 'home section image'" class="home-grid__image" />
          <span v-if="item.badge" class="home-grid__badge">{{ item.badge }}</span>
        </div>
        <div class="home-grid__meta">
          <strong v-if="item.description">{{ item.description }}</strong>
          <p v-if="item.title">{{ item.title }}</p>
        </div>
      </a>
    </div>
  </section>
</template>

<style scoped>
.home-grid {
  padding: 34px 24px 0;
}

.home-grid__list {
  display: grid;
  gap: 18px;
}

.grid-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.grid-4 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.grid-8 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.home-grid__card {
  display: block;
}

.home-grid__image-wrap {
  position: relative;
  overflow: hidden;
  border-radius: 28px;
  background: #ece8df;
}

.home-grid__image {
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  transform: scale(1);
  transition: transform 0.4s ease;
}

.home-grid__badge {
  position: absolute;
  top: 14px;
  right: 14px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #ef5a32;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}

.home-grid__meta {
  padding-top: 12px;
}

.home-grid__meta strong,
.home-grid__meta p {
  display: block;
  color: #181512;
}

.home-grid__meta strong {
  margin-bottom: 4px;
  font-size: 15px;
}

.home-grid__meta p {
  font-size: 14px;
}

@media (hover: hover) and (pointer: fine) {
  .home-grid__card:hover .home-grid__image {
    transform: scale(1.05);
  }
}

@media (max-width: 1024px) {
  .grid-4,
  .grid-8 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .home-grid {
    padding: 24px 16px 0;
  }

  .grid-2,
  .grid-4,
  .grid-8 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
  }

  .home-grid__image {
    border-radius: 22px;
  }
}
</style>
