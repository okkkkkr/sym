<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import FilterSidebar from '../components/home/FilterSidebar.vue'
import ProductShowcase from '../components/home/ProductShowcase.vue'
import { fetchCatalog, reportBrandSearch } from '../services/catalog'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const brands = ref([])
const hotBrands = ref([])
const hotTags = ref([])
const products = ref([])
const currentCategoryLabel = ref('')
const total = ref(0)
const productsContainer = ref(null)
const mobileFiltersOpen = ref(false)
const PAGE_SIZE = 24
const LOAD_MORE_THRESHOLD_RATIO = 0.1
const LOAD_MORE_THRESHOLD_MIN = 48
const LOAD_MORE_THRESHOLD_MAX = 120
const loadingMore = ref(false)
const activeQueryKey = ref('')
const loadedPage = ref(0)
const pageAdvancePending = ref(false)
const currentPage = ref(1)

const requestedCategory = computed(() => String(route.query.category || '').trim())

const currentKeyword = computed(() => String(route.query.keyword || '').trim())

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

const hasMore = computed(() => loadedPage.value < totalPages.value)
const catalogQueryKey = computed(() => buildQueryKey())

const selectedBrandIds = computed(() => {
  const value = route.query.brand

  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean)
  }

  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
})

const selectedTagIds = computed(() => {
  const value = route.query.tag

  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean)
  }

  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
})

const pageTitle = computed(() => currentCategoryLabel.value || 'PRODUCTS')

function buildQueryKey() {
  return JSON.stringify({
    category: requestedCategory.value,
    keyword: currentKeyword.value,
    brandIds: [...selectedBrandIds.value].sort(),
    tagIds: [...selectedTagIds.value].sort(),
  })
}

function getPreloadThreshold(viewportHeight) {
  return Math.min(
    LOAD_MORE_THRESHOLD_MAX,
    Math.max(LOAD_MORE_THRESHOLD_MIN, Math.round(viewportHeight * LOAD_MORE_THRESHOLD_RATIO)),
  )
}

function isViewportScrollMode() {
  const container = productsContainer.value
  if (!container || typeof window === 'undefined') {
    return false
  }

  const { overflowY } = window.getComputedStyle(container)
  return overflowY === 'visible'
}

function getScrollHost() {
  if (typeof window === 'undefined') {
    return null
  }

  return productsContainer.value?.closest('.site-layout__main') || window
}

function getRemainingScrollDistance() {
  const container = productsContainer.value
  if (!container || typeof window === 'undefined') {
    return Number.POSITIVE_INFINITY
  }

  if (isViewportScrollMode()) {
    return container.getBoundingClientRect().bottom - window.innerHeight
  }

  return container.scrollHeight - container.scrollTop - container.clientHeight
}

function getViewportHeight() {
  const container = productsContainer.value
  if (!container || typeof window === 'undefined') {
    return 0
  }

  if (isViewportScrollMode()) {
    return window.innerHeight
  }

  return container.clientHeight
}

async function loadCatalog() {
  const queryKey = catalogQueryKey.value
  const shouldAppend = queryKey === activeQueryKey.value && currentPage.value === loadedPage.value + 1 && currentPage.value > 1

  if (shouldAppend) {
    loadingMore.value = true
  } else {
    loading.value = true
  }

  try {
    const payload = await fetchCatalog({
      category: requestedCategory.value,
      keyword: currentKeyword.value,
      brandIds: selectedBrandIds.value,
      tagIds: selectedTagIds.value,
      page: currentPage.value,
      pageSize: PAGE_SIZE,
    })
    currentCategoryLabel.value = payload.categoryLabel || ''
    brands.value = payload.brands || []
    hotBrands.value = payload.hotBrands || []
    hotTags.value = payload.hotTags || []
    if (shouldAppend) {
      const existingIds = new Set(products.value.map((item) => item.id))
      const nextProducts = (payload.products || []).filter((item) => !existingIds.has(item.id))
      products.value = [...products.value, ...nextProducts]
    } else {
      products.value = payload.products || []
    }
    total.value = Number(payload.total || 0)
    activeQueryKey.value = queryKey
    loadedPage.value = Number(payload.page || currentPage.value || 1)

    if (payload.category && payload.category !== requestedCategory.value) {
      router.replace({
        query: {
          ...route.query,
          category: payload.category,
          brand: undefined,
          tag: undefined,
          page: undefined,
        },
      })
    }

    await nextTick()
    maybeLoadNextPage()
  } catch (error) {
    message.error(error.message)
    currentCategoryLabel.value = ''
    brands.value = []
    hotBrands.value = []
    hotTags.value = []
    products.value = []
    total.value = 0
    loadedPage.value = 0
  } finally {
    loading.value = false
    loadingMore.value = false
    pageAdvancePending.value = false
  }
}

function updateQuery(nextQuery) {
  return router.replace({
    query: {
      ...route.query,
      ...nextQuery,
    },
  })
}

function scrollResultsToTop() {
  nextTick(() => {
    const container = productsContainer.value
    const scrollHost = container?.closest('.site-layout__main')

    productsContainer.value?.scrollTo({
      top: 0,
      behavior: 'smooth',
    })

    if (container && scrollHost) {
      const hostRect = scrollHost.getBoundingClientRect()
      const containerRect = container.getBoundingClientRect()
      const nextTop = scrollHost.scrollTop + containerRect.top - hostRect.top

      scrollHost.scrollTo({
        top: Math.max(0, nextTop),
        behavior: 'smooth',
      })
      return
    }

    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    })
  })
}

function handleApply(filters) {
  const nextBrandIds = [...filters.brandIds].map((item) => String(item)).filter(Boolean).sort()
  const currentBrandIds = [...selectedBrandIds.value].map((item) => String(item)).filter(Boolean).sort()
  const nextTagIds = [...filters.tagIds].map((item) => String(item)).filter(Boolean).sort()
  const hasBrandSelectionChanged = nextBrandIds.join(',') !== currentBrandIds.join(',')

  updateQuery({
    keyword: filters.keyword || undefined,
    brand: filters.brandIds.length ? filters.brandIds.join(',') : undefined,
    tag: filters.tagIds.length ? filters.tagIds.join(',') : undefined,
    page: undefined,
  })

  if (hasBrandSelectionChanged && nextBrandIds.length) {
    reportBrandSearch(nextBrandIds)
  }

  mobileFiltersOpen.value = false
}

function handlePageChange(page) {
  currentPage.value = Math.max(1, page)
}

function maybeLoadNextPage() {
  if (loading.value || loadingMore.value || pageAdvancePending.value || !hasMore.value) {
    return
  }

  const viewportHeight = getViewportHeight()
  if (!viewportHeight) {
    return
  }

  const remainingDistance = getRemainingScrollDistance()
  const threshold = getPreloadThreshold(viewportHeight)

  if (remainingDistance > threshold) {
    return
  }

  pageAdvancePending.value = true
  handlePageChange(currentPage.value + 1)
}

function toggleMobileFilters() {
  mobileFiltersOpen.value = !mobileFiltersOpen.value
}

function handleProductsScroll() {
  maybeLoadNextPage()
}

function bindScrollListeners() {
  const container = productsContainer.value
  const scrollHost = getScrollHost()

  container?.addEventListener('scroll', handleProductsScroll, { passive: true })
  if (scrollHost && scrollHost !== container) {
    scrollHost.addEventListener('scroll', handleProductsScroll, { passive: true })
  }
  window.addEventListener('resize', handleProductsScroll, { passive: true })
}

function unbindScrollListeners() {
  const container = productsContainer.value
  const scrollHost = getScrollHost()

  container?.removeEventListener('scroll', handleProductsScroll)
  if (scrollHost && scrollHost !== container) {
    scrollHost.removeEventListener('scroll', handleProductsScroll)
  }
  window.removeEventListener('resize', handleProductsScroll)
}

watch([catalogQueryKey, currentPage], () => {
  loadCatalog()
}, { immediate: true })

watch(catalogQueryKey, (queryKey, previousQueryKey) => {
  if (previousQueryKey !== undefined && queryKey !== previousQueryKey) {
    currentPage.value = 1
    loadedPage.value = 0
    activeQueryKey.value = ''
    pageAdvancePending.value = false
    scrollResultsToTop()
  }
})

watch(() => route.query.page, (page) => {
  if (page === undefined) {
    return
  }

  router.replace({
    query: {
      ...route.query,
      page: undefined,
    },
  })
}, { immediate: true })

onMounted(() => {
  bindScrollListeners()
  nextTick(() => {
    maybeLoadNextPage()
  })
})

onBeforeUnmount(() => {
  unbindScrollListeners()
})
</script>

<template>
  <div class="product-page">
    <section class="product-page__catalog page-container">
      <div class="product-page__mobile-header">
        <h2 class="product-page__mobile-title">{{ pageTitle }}</h2>
        <button
          type="button"
          class="product-page__mobile-filter-toggle"
          :aria-expanded="mobileFiltersOpen"
          @click="toggleMobileFilters"
        >
          {{ mobileFiltersOpen ? 'Hide Filters' : 'Show Filters' }}
        </button>
      </div>
      <div class="product-page__sidebar" :class="{ 'product-page__sidebar--open': mobileFiltersOpen }">
        <FilterSidebar
          :title="pageTitle"
          :brands="brands"
          :hot-brands="hotBrands"
          :hot-tags="hotTags"
          :keyword="currentKeyword"
          :selected-brands="selectedBrandIds"
          :selected-tags="selectedTagIds"
          @apply="handleApply"
        />
      </div>
      <div ref="productsContainer" class="product-page__products pretty-scrollbar pretty-scrollbar--hover">
        <ProductShowcase :products="products" :loading="loading" />
        <div v-if="products.length" class="product-page__load-state">
          <a-spin v-if="loadingMore" size="small" />
          <span v-else-if="hasMore">继续向下滚动加载更多</span>
          <span v-else-if="total > PAGE_SIZE">No more products</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.product-page {
  height: 100%;
  min-height: 0;
}

.product-page__catalog {
  display: grid;
  grid-template-columns: minmax(180px, 220px) minmax(0, 1fr);
  height: 100%;
  min-height: 0;
  gap: 24px;
  padding: 36px 24px;
}

.product-page__mobile-header {
  display: none;
}

.product-page__sidebar {
  min-width: 0;
}

.product-page__products {
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-gutter: stable;
  padding: 24px;
  margin: -24px;
}

.product-page__load-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 28px 0 8px;
  color: #6a6a6a;
  font-size: 12px;
  letter-spacing: 0.04em;
}

@media (max-width: 900px) {
  .product-page {
    height: auto;
  }

  .product-page__catalog {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
    height: auto;
    gap: 18px;
    padding: 28px 24px 0;
  }

  .product-page__mobile-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }

  .product-page__mobile-title {
    margin: 0;
    color: #111111;
    font-size: 22px;
    font-weight: 700;
    line-height: 1.1;
  }

  .product-page__mobile-filter-toggle {
    flex: 0 0 auto;
    min-height: 40px;
    border: 1px solid #111111;
    background: transparent;
    padding: 0 14px;
    color: #111111;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  .product-page__sidebar {
    display: none;
  }

  .product-page__sidebar--open {
    display: block;
  }

  .product-page__sidebar :deep(.filter-sidebar__group--title) {
    display: none;
  }

  .product-page__products {
    overflow: visible;
  }
}
</style>
