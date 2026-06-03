<script setup>
import HomeGridSection from './HomeGridSection.vue'

defineProps({
  module: {
    type: Object,
    required: true,
  },
})
</script>

<template>
  <HomeGridSection :module="module" columns="grid-4" />
</template>
