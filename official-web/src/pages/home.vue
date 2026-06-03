<script setup>
import { computed } from 'vue'

import HomeCarouselSection from '../components/home-layout/HomeCarouselSection.vue'
import HomeGrid2Section from '../components/home-layout/HomeGrid2Section.vue'
import HomeGrid4Section from '../components/home-layout/HomeGrid4Section.vue'
import HomeGrid8Section from '../components/home-layout/HomeGrid8Section.vue'
import HomeHorizontalListSection from '../components/home-layout/HomeHorizontalListSection.vue'
import HomeSingleImageSection from '../components/home-layout/HomeSingleImageSection.vue'

const props = defineProps({
  layout: {
    type: Object,
    default: () => ({
      modules: [],
    }),
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
})

const sectionComponents = {
  single_image: HomeSingleImageSection,
  grid_2: HomeGrid2Section,
  grid_4: HomeGrid4Section,
  grid_8: HomeGrid8Section,
  carousel: HomeCarouselSection,
  horizontal_list: HomeHorizontalListSection,
}

const visibleModules = computed(() =>
  (props.layout.modules || []).filter(
    (module) => module && module.is_enabled !== false && sectionComponents[module.type]
  )
)
</script>

<template>
  <div class="home-page">
    <div v-if="loading" class="home-page__state page-container">首页内容加载中...</div>
    <div v-else-if="error" class="home-page__state page-container">{{ error }}</div>
    <div v-else-if="visibleModules.length">
      <component
        :is="sectionComponents[module.type]"
        v-for="module in visibleModules"
        :key="module.id || `${module.type}-${module.sort}`"
        :module="module"
      />
    </div>
    <div v-else class="home-page__state page-container">当前首页还没有已发布内容。</div>
  </div>
</template>

<style scoped>
.home-page {
  padding-bottom: 48px;
}

.home-page__state {
  padding: 120px 24px 0;
  color: #5d564f;
  font-size: 18px;
}

@media (max-width: 768px) {
  .home-page__state {
    padding: 64px 16px 0;
    font-size: 16px;
  }
}
</style>
