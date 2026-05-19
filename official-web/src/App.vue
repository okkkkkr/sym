<script setup>
import { onMounted } from 'vue'

import { reportSiteVisit } from './services/catalog'

onMounted(() => {
  reportSiteVisit()
})
</script>

<template>
  <router-view />
</template>
