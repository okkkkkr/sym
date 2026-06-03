<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import ProductArtwork from '../product/ProductArtwork.vue'

const props = defineProps({
  products: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const CARD_WIDTH = 180
const CARD_HEIGHT = 220
const viewportRef = ref(null)
const availableWidth = ref(0)

let resizeObserver

function ensureViewportObserver() {
  if (!resizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      updateAvailableWidth()
    })
  }

  resizeObserver.disconnect()

  if (viewportRef.value) {
    resizeObserver.observe(viewportRef.value)
    updateAvailableWidth()
  }
}

const columnGap = computed(() => {
  if (availableWidth.value <= 767) {
    return 20
  }

  if (availableWidth.value <= 1100) {
    return 18
  }

  return 20
})

const rowGap = computed(() => {
  if (availableWidth.value <= 767) {
    return 20
  }

  if (availableWidth.value <= 1100) {
    return 28
  }

  return 42
})

const isMobileLayout = computed(() => {
  const width = availableWidth.value
  if (!width) {
    return false
  }

  return width <= 767
})

const hasProducts = computed(() => props.products.length > 0)

const columnCount = computed(() => {
  const productCount = props.products.length || 1
  const width = availableWidth.value

  if (!width) {
    return 1
  }

   if (isMobileLayout.value) {
    return Math.min(productCount, 2)
  }

  const columns = Math.floor((width + columnGap.value) / (CARD_WIDTH + columnGap.value))
  return Math.min(productCount, Math.max(1, columns))
})

const isSingleColumnLayout = computed(() => {
  const width = availableWidth.value

  if (!width) {
    return false
  }

  return Math.floor((width + columnGap.value) / (CARD_WIDTH + columnGap.value)) <= 1
})

const gridWidth = computed(() => {
  if (isMobileLayout.value) {
    return availableWidth.value
  }

  if (isSingleColumnLayout.value) {
    return availableWidth.value
  }

  if (columnCount.value === 1) {
    return Math.min(availableWidth.value, CARD_WIDTH)
  }

  const gaps = Math.max(0, columnCount.value - 1) * columnGap.value
  return columnCount.value * CARD_WIDTH + gaps
})

const isSingleColumn = computed(() => columnCount.value === 1)
const shouldUseFluidCard = computed(() => isSingleColumn.value && isSingleColumnLayout.value)

const gridStyle = computed(() => ({
  width: isSingleColumn.value ? `${gridWidth.value}px` : `${gridWidth.value}px`,
  gap: `${rowGap.value}px ${columnGap.value}px`,
}))

const cardStyle = computed(() => {
  if (isMobileLayout.value) {
    const width = Math.max(0, (availableWidth.value - columnGap.value) / 2)
    return {
      flexBasis: `${width}px`,
      minWidth: `${width}px`,
      width: `${width}px`,
      maxWidth: `${width}px`,
    }
  }

  if (isSingleColumn.value && shouldUseFluidCard.value) {
    return {
      flexBasis: '100%',
      minWidth: '100%',
      width: '100%',
      maxWidth: '100%',
    }
  }

  return {
    flexBasis: `${CARD_WIDTH}px`,
    minWidth: `${CARD_WIDTH}px`,
    width: `${CARD_WIDTH}px`,
    maxWidth: `${CARD_WIDTH}px`,
  }
})

function updateAvailableWidth() {
  availableWidth.value = viewportRef.value?.clientWidth ?? 0
}

onMounted(() => {
  ensureViewportObserver()
})

watch(hasProducts, async (value) => {
  if (!value) {
    availableWidth.value = 0
    resizeObserver?.disconnect()
    return
  }

  await nextTick()
  ensureViewportObserver()
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
})

function productLink(product) {
  return {
    path: `/sym/${product.id}`,
    query: {
      category: product.category,
    },
  }
}
</script>

<template>
  <section class="product-showcase">
    <a-spin :spinning="loading">
      <div v-if="hasProducts" ref="viewportRef" class="product-showcase__viewport">
        <div class="product-showcase__grid" :style="gridStyle">
          <RouterLink
            v-for="product in products"
            :key="product.id"
            :to="productLink(product)"
            class="product-card"
            :style="cardStyle"
          >
            <a-card hoverable class="product-card__panel">
              <template #cover>
                <div class="product-card__frame">
                  <ProductArtwork :product="product" mode="card" />
                </div>
              </template>

              <a-card-meta :title="product.name">
                <template #description>
                  <p class="product-card__description">{{ product.description }}</p>
                </template>
              </a-card-meta>
            </a-card>
          </RouterLink>
        </div>
      </div>
      <div v-else class="product-showcase__empty">
        <a-empty description="No items found" />
      </div>
    </a-spin>
  </section>
</template>

<style scoped>
.product-showcase {
  width: 100%;
}

.product-showcase__viewport {
  width: 100%;
  overflow-x: hidden;
}

.product-showcase__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 360px;
}

.product-showcase__grid {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: flex-start;
  margin: 0 auto;
}

.product-card {
  display: block;
  flex: 0 0 180px;
  min-width: 180px;
  width: 180px;
  max-width: 180px;
  color: inherit;
}

.product-card :deep(.ant-card) {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 14px;
}

.product-card :deep(.ant-card-body) {
  flex: 1 1 auto;
  display: flex;
  align-items: center;
  min-height: 0;
  padding: 10px 14px 12px;
  overflow: hidden;
}

.product-card :deep(.ant-card-meta) {
  width: 100%;
}

.product-card__panel {
  width: 100%;
  height: 220px;
  border-radius: 14px;
  box-shadow: 0 10px 26px rgba(18, 18, 18, 0.05);
}

.product-card__panel:hover {
  box-shadow: 0 18px 40px rgba(18, 18, 18, 0.12);
}

.product-card__frame {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 144px;
  height: 144px;
  background: #f0efeb;
  padding: 14px;
  overflow: hidden;
}

.product-card :deep(.product-artwork--card) {
  width: auto;
  height: 100%;
  max-width: 116px;
  max-height: 100%;
}

.product-card :deep(.ant-card-meta-title) {
  margin: 0 0 2px;
  color: #101010;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-card__description {
  margin: 0;
  color: #5d5d5d;
  font-size: 12px;
  line-height: 1.45;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  text-overflow: ellipsis;
}

.shape-rect {
  border-radius: 0;
}

.shape-quarter {
  border-radius: 0 999px 0 0;
}
</style>
