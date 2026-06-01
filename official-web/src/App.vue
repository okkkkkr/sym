<script setup>
import { onMounted } from 'vue'

import { reportChannelVisit, reportSiteVisit } from './services/catalog'

onMounted(() => {
  reportSiteVisit()
  reportChannelVisit()
})
</script>

<template>
  <router-view />
</template>
