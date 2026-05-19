<script setup>
import { computed, onMounted, ref } from 'vue'

import { fetchActiveBanners, reportBannerClick } from '../../services/banners'

const fallbackBanners = [{ id: 'default', content: 'Appreciate the item and then choose it', link_url: '' }]
const banners = ref([])

const slides = computed(() => (banners.value.length ? banners.value : fallbackBanners))

function resolveBannerTarget(linkUrl) {
  const value = String(linkUrl || '').trim()
  if (!value) {
    return { href: '', external: false }
  }

  return {
    href: value,
    external: /^https?:\/\//i.test(value),
  }
}

onMounted(() => {
  fetchActiveBanners()
    .then((data) => {
      banners.value = data
    })
    .catch(() => {
      banners.value = []
    })
})

function shouldUseNativeNavigation(event, target) {
  return (
    event.defaultPrevented
    || event.button !== 0
    || event.metaKey
    || event.ctrlKey
    || event.shiftKey
    || event.altKey
    || target.external
  )
}

async function handleBannerClick(event, banner) {
  const target = resolveBannerTarget(banner.link_url)
  if (!target.href || shouldUseNativeNavigation(event, target)) {
    reportBannerClick(banner.id)
    return
  }

  event.preventDefault()
  await reportBannerClick(banner.id, { transport: 'fetch' })
  window.location.assign(target.href)
}
</script>

<template>
  <div class="announcement-bar">
    <div class="page-container announcement-bar__inner">
      <a-carousel class="announcement-bar__carousel" :autoplay="true" :autoplay-speed="3000" :dots="false">
        <div v-for="item in slides" :key="item.id" class="announcement-bar__slide">
          <a
            v-if="resolveBannerTarget(item.link_url).href"
            class="announcement-bar__link"
            :href="resolveBannerTarget(item.link_url).href"
            :target="resolveBannerTarget(item.link_url).external ? '_blank' : '_self'"
            :rel="resolveBannerTarget(item.link_url).external ? 'noreferrer' : undefined"
            @click="handleBannerClick($event, item)"
          >
            {{ item.content }}
          </a>
          <span v-else class="announcement-bar__text">{{ item.content }}</span>
        </div>
      </a-carousel>
    </div>
  </div>
</template>

<style scoped>
.announcement-bar {
  background: #050505;
  color: #f8f8f4;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.02em;
}

.announcement-bar__inner {
  height: 40px;
  padding: 0 24px;
  text-align: center;
}

.announcement-bar__carousel {
  height: 40px;
  color: #f8f8f4;
}

.announcement-bar__slide {
  display: flex !important;
  align-items: center;
  justify-content: center;
  height: 40px;
  color: #f8f8f4;
}

.announcement-bar__link,
.announcement-bar__text {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 12px;
  color: #f8f8f4 !important;
  text-decoration: none;
  line-height: 1;
}

.announcement-bar__link:hover {
  color: #ffffff;
  text-decoration: none;
}

:deep(.announcement-bar__carousel a) {
  color: #f8f8f4 !important;
  text-decoration: none !important;
}

:deep(.announcement-bar__carousel a:hover) {
  color: #ffffff !important;
  text-decoration: none !important;
}

:deep(.announcement-bar__carousel .slick-list),
:deep(.announcement-bar__carousel .slick-track),
:deep(.announcement-bar__carousel .slick-slide),
:deep(.announcement-bar__carousel .slick-slide > div) {
  height: 40px;
}

@media (max-width: 767px) {
  .announcement-bar__inner {
    padding: 0 16px;
  }
}
</style>
