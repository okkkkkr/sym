<script setup>
import { computed } from 'vue'

const props = defineProps({
  product: {
    type: Object,
    required: true,
  },
  imageUrl: {
    type: String,
    default: '',
  },
  mode: {
    type: String,
    default: 'card',
  },
})

const modeClass = {
  card: 'product-artwork--card',
  detail: 'product-artwork--detail',
  thumb: 'product-artwork--thumb',
}[props.mode] ?? 'product-artwork--card'

const imageSrc = computed(() => {
  if (props.imageUrl) {
    return props.imageUrl
  }

  if (props.product?.coverImageUrl) {
    return props.product.coverImageUrl
  }

  if (Array.isArray(props.product?.imageUrls) && props.product.imageUrls.length) {
    return props.product.imageUrls[0]
  }

  return ''
})
</script>

<template>
  <div class="product-artwork" :class="modeClass">
    <img v-if="imageSrc" :src="imageSrc" :alt="product.name" class="product-artwork__image" />
    <span v-else class="product-artwork__placeholder">No Image</span>
  </div>
</template>

<style scoped>
.product-artwork {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 1px solid rgba(17, 17, 17, 0.08);
  border-radius: 18px;
  background: #f7f4ee;
}

.product-artwork--card {
  width: 100%;
  height: 100%;
}

.product-artwork--detail {
  width: 100%;
  height: 100%;
  border-radius: 20px;
}

.product-artwork--thumb {
  width: 100%;
  aspect-ratio: 3 / 4;
  border-radius: 16px;
}

.product-artwork__image {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.product-artwork__placeholder {
  color: rgba(17, 17, 17, 0.4);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
</style>