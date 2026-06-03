<script setup>
const props = defineProps({
  module: {
    type: Object,
    required: true,
  },
})

const module = props.module
const hero = module.items?.[0] || {}
</script>

<template>
  <section class="home-single page-container">
    <a
      class="home-single__card"
      :href="hero.action?.link || undefined"
      :target="hero.action?.target === 'blank' ? '_blank' : undefined"
    >
      <img v-if="hero.image" :src="hero.image" :alt="hero.title || module.title || 'home hero'" class="home-single__image" />
      <div class="home-single__overlay" :class="{ 'is-clear': module.config?.overlay === false }">
        <span v-if="module.title" class="home-single__eyebrow">{{ module.title }}</span>
        <h1 v-if="hero.title">{{ hero.title }}</h1>
        <p v-if="hero.description">{{ hero.description }}</p>
        <span v-if="hero.action?.text" class="home-single__button">{{ hero.action.text }}</span>
      </div>
    </a>
  </section>
</template>

<style scoped>
.home-single {
  padding: 24px 24px 0;
}

.home-single__card {
  position: relative;
  display: block;
  overflow: hidden;
  border-radius: 34px;
  background: #d9d2c7;
}

.home-single__image {
  width: 100%;
  aspect-ratio: 16 / 7;
  object-fit: cover;
  transform: scale(1);
  transition: transform 0.45s ease;
}

.home-single__overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 14px;
  padding: 32px;
  color: #fff;
  text-align: center;
  background: linear-gradient(180deg, rgba(22, 18, 14, 0.14), rgba(22, 18, 14, 0.35));
}

.home-single__overlay.is-clear {
  background: none;
}

.home-single__eyebrow {
  font-size: 14px;
  font-weight: 700;
}

.home-single h1 {
  font-size: clamp(42px, 6vw, 78px);
  line-height: 0.94;
  font-weight: 800;
  letter-spacing: -0.05em;
}

.home-single p {
  max-width: 520px;
  font-size: 18px;
}

.home-single__button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 148px;
  min-height: 58px;
  padding: 0 28px;
  border-radius: 999px;
  background: #fff;
  color: #1f1a15;
  font-size: 18px;
  font-weight: 600;
}

@media (hover: hover) and (pointer: fine) {
  .home-single__card:hover .home-single__image {
    transform: scale(1.01);
  }
}

@media (max-width: 640px) {
  .home-single {
    padding: 12px 12px 0;
  }

  .home-single__card,
  .home-single__image {
    border-radius: 20px;
  }

  .home-single__overlay {
    gap: 6px;
    padding: 14px 16px;
  }

  .home-single__eyebrow {
    font-size: 11px;
    line-height: 1.1;
  }

  .home-single h1 {
    max-width: 100%;
    font-size: clamp(22px, 7.6vw, 32px);
    line-height: 0.96;
  }

  .home-single p {
    max-width: 100%;
    font-size: 12px;
    line-height: 1.2;
  }

  .home-single__button {
    min-width: 0;
    min-height: 34px;
    padding: 0 14px;
    font-size: 12px;
  }
}
</style>
