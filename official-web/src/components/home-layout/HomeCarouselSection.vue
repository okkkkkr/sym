<script setup>
import HomeSectionHeader from './HomeSectionHeader.vue'

const props = defineProps({
  module: {
    type: Object,
    required: true,
  },
})

const module = props.module
</script>

<template>
  <section class="home-carousel page-container">
    <HomeSectionHeader :title="module.title" :action="module.action || {}" />
    <a-carousel
      class="home-carousel__carousel"
      :autoplay="module.config?.autoplay !== false"
      :autoplay-speed="module.config?.interval || 3000"
      :dots="module.config?.show_dots !== false"
    >
      <a
        v-for="item in module.items"
        :key="item.id || item.sort"
        class="home-carousel__slide"
        :href="item.action?.link || undefined"
        :target="item.action?.target === 'blank' ? '_blank' : undefined"
      >
        <img v-if="item.image" :src="item.image" :alt="item.title || 'carousel image'" class="home-carousel__image" />
        <div class="home-carousel__overlay">
          <span v-if="item.badge" class="home-carousel__badge">{{ item.badge }}</span>
          <h2 v-if="item.title">{{ item.title }}</h2>
          <p v-if="item.description">{{ item.description }}</p>
          <span v-if="item.action?.text" class="home-carousel__button">{{ item.action.text }}</span>
        </div>
      </a>
    </a-carousel>
  </section>
</template>

<style scoped>
.home-carousel {
  padding: 34px 24px 0;
}

.home-carousel__slide {
  position: relative;
  display: block;
  overflow: hidden;
  border-radius: 34px;
}

.home-carousel__image {
  width: 100%;
  aspect-ratio: 16 / 7;
  object-fit: cover;
  transform: scale(1);
  transition: transform 0.45s ease;
}

.home-carousel__overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 12px;
  padding: 40px;
  background: linear-gradient(180deg, rgba(18, 18, 18, 0.04), rgba(18, 18, 18, 0.46));
  color: #fff;
}

.home-carousel__badge {
  width: fit-content;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.22);
  font-size: 12px;
}

.home-carousel h2 {
  font-size: clamp(36px, 4vw, 58px);
  line-height: 0.96;
  font-weight: 800;
  letter-spacing: -0.05em;
}

.home-carousel p {
  max-width: 520px;
  font-size: 18px;
}

.home-carousel__button {
  display: inline-flex;
  width: fit-content;
  align-items: center;
  min-height: 54px;
  padding: 0 24px;
  border-radius: 999px;
  background: #fff;
  color: #181512;
  font-weight: 600;
}

@media (hover: hover) and (pointer: fine) {
  .home-carousel__slide:hover .home-carousel__image {
    transform: scale(1.04);
  }
}

@media (max-width: 768px) {
  .home-carousel {
    padding: 24px 16px 0;
  }

  .home-carousel__slide,
  .home-carousel__image {
    border-radius: 24px;
  }

  .home-carousel__image {
    aspect-ratio: 4 / 5;
  }

  .home-carousel__overlay {
    padding: 28px 22px;
  }
}
</style>
