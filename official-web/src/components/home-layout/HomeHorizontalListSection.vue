<script setup>
import { ref } from 'vue'

import HomeSectionHeader from './HomeSectionHeader.vue'

const props = defineProps({
  module: {
    type: Object,
    required: true,
  },
})
const listRef = ref(null)

function handleWheel(event) {
  const container = listRef.value
  if (!container) return
  if (Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return
  const canScroll = container.scrollWidth > container.clientWidth
  if (!canScroll) return
  event.preventDefault()
  container.scrollLeft += event.deltaY
}
</script>

<template>
  <section class="home-horizontal page-container">
    <HomeSectionHeader :title="module.title" :action="module.action || {}" />
    <div ref="listRef" class="home-horizontal__list" @wheel="handleWheel">
      <a
        v-for="item in module.items"
        :key="item.id || item.sort"
        class="home-horizontal__card"
        :href="item.action?.link || undefined"
        :target="item.action?.target === 'blank' ? '_blank' : undefined"
      >
        <div class="home-horizontal__media">
          <img v-if="item.image" :src="item.image" :alt="item.title || 'list image'" class="home-horizontal__image" />
          <span v-if="item.badge" class="home-horizontal__badge">{{ item.badge }}</span>
        </div>
        <div class="home-horizontal__meta">
          <strong v-if="item.title">{{ item.title }}</strong>
          <p v-if="item.description">{{ item.description }}</p>
          <span v-if="item.action?.text">{{ item.action.text }}</span>
        </div>
      </a>
    </div>
  </section>
</template>

<style scoped>
.home-horizontal {
  padding: 34px 24px 0;
}

.home-horizontal__list {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: calc((100% - 4 * 24px) / 5);
  gap: 24px;
  overflow-x: auto;
  padding-bottom: 6px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.home-horizontal__list::-webkit-scrollbar {
  display: none;
}

.home-horizontal__card {
  display: block;
  min-width: 0;
  overflow-wrap: anywhere;
}

.home-horizontal__media {
  position: relative;
  height: 440px;
  overflow: hidden;
  border-radius: 0;
  background: #ece8df;
}

.home-horizontal__image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1);
  transition: transform 0.4s ease;
}

.home-horizontal__badge {
  position: absolute;
  top: 14px;
  left: 14px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(20, 18, 16, 0.72);
  color: #fff;
  font-size: 12px;
}

.home-horizontal__meta {
  padding-top: 12px;
}

.home-horizontal__meta strong,
.home-horizontal__meta p,
.home-horizontal__meta span {
  display: block;
}

.home-horizontal__meta strong {
  margin-bottom: 4px;
  color: #181512;
}

.home-horizontal__meta p {
  color: #4d463f;
}

.home-horizontal__meta span {
  margin-top: 10px;
  color: #181512;
  font-weight: 600;
}

@media (hover: hover) and (pointer: fine) {
  .home-horizontal__card:hover .home-horizontal__image {
    transform: scale(1.05);
  }
}

@media (max-width: 1024px) {
  .home-horizontal__list {
    grid-auto-columns: calc((100% - 4 * 20px) / 5);
    gap: 20px;
  }
}

@media (width < 1000px) {
  .home-horizontal {
    padding: 24px 16px 0;
  }

  .home-horizontal__list {
    grid-auto-columns: calc((100% - 16px) / 2);
    gap: 16px;
  }
}
</style>
