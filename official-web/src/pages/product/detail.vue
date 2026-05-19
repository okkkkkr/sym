<script setup>
import { computed, nextTick, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { LeftOutlined, RightOutlined } from "@ant-design/icons-vue";
import { message } from 'ant-design-vue'
import ProductShowcase from '../../components/home/ProductShowcase.vue'
import ProductArtwork from "../../components/product/ProductArtwork.vue";
import { fetchCatalogProduct, reportProductClick } from '../../services/catalog'

const route = useRoute();
const activeIndex = ref(0);
const thumbRefs = ref([]);
const product = ref(null)
const relatedProducts = ref([])
const brandName = ref('SYM Studio')
const categoryLabelText = ref('')

const categoryKey = computed(
  () =>
    product.value?.category ??
    String(route.query.category ?? "").toLowerCase(),
);
const categoryLabel = computed(
  () => categoryLabelText.value || String(categoryKey.value || 'products').toUpperCase(),
);

const gallery = computed(() => {
  if (!product.value) {
    return [];
  }

  const imageSources = [
    product.value.coverImageUrl,
    ...(Array.isArray(product.value.imageUrls) ? product.value.imageUrls : []),
  ]
    .filter((source, index, list) => source && list.indexOf(source) === index)
    .map((src, index) => ({
      key: `image-${index + 1}`,
      label: `Image ${index + 1}`,
      src,
      type: 'image',
    }))

  const videoSources = (Array.isArray(product.value.videoUrls) ? product.value.videoUrls : [])
    .filter((source, index, list) => source && list.indexOf(source) === index)
    .map((src, index) => ({
      key: `video-${index + 1}`,
      label: `Video ${index + 1}`,
      src,
      type: 'video',
    }))

  const mediaSources = [...videoSources, ...imageSources]

  if (!mediaSources.length) {
    return [{ key: 'slide-1', label: 'Image 1', src: '', type: 'image' }]
  }

  return mediaSources
});

const activeSlide = computed(() => gallery.value[activeIndex.value] || gallery.value[0] || null)

watch(product, async () => {
  activeIndex.value = 0;
  await nextTick();
  syncActiveThumb(0);
});

watch(activeIndex, async (current) => {
  await nextTick();
  syncActiveThumb(current);
});

function selectSlide(index) {
  activeIndex.value = index;
}

function setThumbRef(element, index) {
  thumbRefs.value[index] = element;
}

function syncActiveThumb(index) {
  const activeThumb = thumbRefs.value[index];

  activeThumb?.scrollIntoView({
    block: "nearest",
    inline: "nearest",
    behavior: "smooth",
  });
}

function goToPreviousSlide() {
  if (!gallery.value.length) return
  activeIndex.value = activeIndex.value <= 0 ? gallery.value.length - 1 : activeIndex.value - 1
}

function goToNextSlide() {
  if (!gallery.value.length) return
  activeIndex.value = activeIndex.value >= gallery.value.length - 1 ? 0 : activeIndex.value + 1
}

async function loadProduct() {
  try {
    const payload = await fetchCatalogProduct(route.params.productId)
    categoryLabelText.value = payload.categoryLabel || ''
    product.value = payload.product
    relatedProducts.value = payload.relatedProducts || []
    brandName.value = payload.brandName || 'SYM Studio'
    reportProductClick(route.params.productId)
  } catch (error) {
    categoryLabelText.value = ''
    product.value = null
    relatedProducts.value = []
    message.error(error.message)
  }
}

function categoryLink(category) {
  return { path: "/sym", query: { category } };
}

watch(() => route.params.productId, () => {
  loadProduct()
}, { immediate: true })
</script>

<template>
  <template v-if="product">
    <div class="product-detail__top page-container">
      <RouterLink class="product-detail__back" :to="categoryLink(product.category)"
        >← Back to listing</RouterLink
      >
    </div>

    <section class="product-detail page-container">
      <div class="product-detail__gallery">
        <div class="product-detail__thumbs-wrap">
          <div class="product-detail__thumbs">
            <button
              v-for="(slide, index) in gallery"
              :key="slide.key"
              type="button"
              :ref="(element) => setThumbRef(element, index)"
              class="product-detail__thumb"
              :class="{ 'product-detail__thumb--active': index === activeIndex }"
              @click="selectSlide(index)"
            >
              <template v-if="slide.type === 'video'">
                <div class="product-detail__thumb-video">
                  <video
                    class="product-detail__thumb-video-el"
                    :src="slide.src"
                    muted
                    playsinline
                    preload="metadata"
                  />
                  <span class="product-detail__thumb-badge">VIDEO</span>
                </div>
              </template>
              <ProductArtwork v-else :product="product" :image-url="slide.src" mode="thumb" />
            </button>
          </div>
        </div>

        <div class="product-detail__stage-wrap">
          <div class="product-detail__stage">
            <button
              type="button"
              class="product-detail__arrow product-detail__arrow--prev"
              @click="goToPreviousSlide"
            >
              <LeftOutlined style="font-size: 16px;" />
            </button>

            <template v-if="activeSlide?.type === 'video'">
              <div class="product-detail__stage-video-wrap">
                <video
                  class="product-detail__stage-video"
                  :src="activeSlide.src"
                  controls
                  preload="metadata"
                  playsinline
                />
              </div>
            </template>
            <ProductArtwork
              v-else-if="activeSlide"
              :product="product"
              :image-url="activeSlide.src"
              mode="detail"
            />

            <button
              type="button"
              class="product-detail__arrow product-detail__arrow--next"
              @click="goToNextSlide"
            >
              <RightOutlined style="font-size: 16px;" />
            </button>
          </div>
        </div>
      </div>

      <aside class="product-detail__info">
        <h1>{{ product.name }}</h1>
        <p class="product-detail__brand">Brand: {{ brandName }}</p>
        <p class="product-detail__description">
          {{ product.detailDescription ?? product.description }}
        </p>

        <div class="product-detail__meta">
          <p>
            Category:
            <RouterLink :to="categoryLink(product.category)">{{
              categoryLabel
            }}</RouterLink>
          </p>
        </div>
      </aside>
    </section>

    <section
      v-if="relatedProducts.length"
      class="product-related page-container"
    >
      <header class="product-related__header">
        <h2>Related</h2>
      </header>

      <ProductShowcase :products="relatedProducts" :loading="false" />
    </section>
  </template>

  <template v-else>
    <div class="product-detail__top page-container">
      <RouterLink class="product-detail__back" :to="categoryLink('bag')"
        >Back to listing</RouterLink
      >
    </div>

    <section class="product-detail__empty page-container">
      <h1>Product not found</h1>
      <p>The requested item does not exist or is no longer available.</p>
    </section>
  </template>
</template>

<style scoped>
.product-detail__top {
  padding: 32px 24px 0;
}

.product-detail {
  display: grid;
  grid-template-columns: fit-content(min(100%, 584px)) minmax(0, 1fr);
  align-items: start;
  gap: clamp(28px, 4vw, 52px);
  padding: 20px 24px 0;
}

.product-detail__thumbs-wrap {
  position: relative;
  height: 100%;
  max-height: 480px;
  min-width: 0;
}

.product-detail__gallery {
  display: grid;
  width: min(100%, 584px);
  grid-template-columns: clamp(64px, 16%, 82px) minmax(0, 1fr);
  gap: 22px;
  align-items: start;
  min-width: 0;
}

.product-detail__thumbs {
  display: flex;
  flex-direction: column;
  gap: 14px;
  height: 100%;
  max-height: 480px;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 8px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.product-detail__thumbs::-webkit-scrollbar {
  width: 0;
  height: 0;
}

.product-detail__thumb {
  width: 100%;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 18px;
  background: transparent;
  cursor: pointer;
  opacity: 0.58;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    opacity 0.2s ease,
    transform 0.2s ease;
}

.product-detail__thumb--active,
.product-detail__thumb:hover {
  opacity: 1;
  transform: translateX(2px);
  border-color: rgba(17, 17, 17, 0.12);
  box-shadow: 0 12px 24px rgba(17, 17, 17, 0.08);
}

.product-detail__thumb-video {
  position: relative;
}

.product-detail__thumb-video-el {
  width: 100%;
  aspect-ratio: 3 / 4;
  display: block;
  border-radius: 16px;
  background: #111111;
  object-fit: cover;
}

.product-detail__thumb-badge {
  position: absolute;
  left: 8px;
  bottom: 8px;
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(17, 17, 17, 0.72);
  color: #ffffff;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.product-detail__stage-wrap {
  position: relative;
  width: 100%;
  max-width: 480px;
  aspect-ratio: 1 / 1;
  height: auto;
  min-width: 0;
  min-height: 0;
}

.product-detail__stage {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  padding: clamp(8px, 1.2vw, 14px);
  border-radius: 20px;
  background: #f3eee5;
}

.product-detail__arrow {
  position: absolute;
  top: 50%;
  z-index: 2;
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(17, 17, 17, 0.15);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.88);
  color: #111111;
  opacity: 0.42;
  cursor: pointer;
  transform: translateY(-50%);
  transition: border-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
}

.product-detail__arrow:hover,
.product-detail__arrow:focus-visible {
  border-color: #1d62ec;
  color: #1d62ec;
  opacity: 0.92;
  box-shadow: 0 12px 24px rgba(17, 17, 17, 0.1);
}

.product-detail__arrow--prev {
  left: 10px;
}

.product-detail__arrow--next {
  right: 10px;
}

.product-detail__stage-video-wrap {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-detail__stage-video {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 18px;
  background: #111111;
  object-fit: contain;
}

.product-detail__info {
  min-width: 0;
  padding-top: 18px;
}

.product-detail__info h1 {
  margin: 0 0 18px;
  color: #111111;
  font-size: clamp(40px, 4vw, 58px);
  line-height: 0.95;
}

.product-detail__brand {
  margin-bottom: 22px;
  color: #222222;
  font-size: 18px;
  font-weight: 600;
}

.product-detail__description {
  margin-bottom: 28px;
  color: #3e3e3e;
  font-size: 16px;
  line-height: 1.85;
}

.product-detail__meta {
  display: flex;
  flex-direction: column;
  gap: 10px;
  color: #4f4f4f;
  font-size: 14px;
}

.product-detail__meta a {
  font-weight: 700;
}

.product-detail__empty {
  padding: 20px 24px 0;
}

.product-detail__empty h1 {
  margin: 0 0 12px;
  font-size: 42px;
}

.product-detail__empty p {
  margin-bottom: 24px;
  color: #575757;
  font-size: 16px;
}

.product-detail__back {
  display: inline-flex;
  margin-bottom: 20px;
  color: #111111;
  font-weight: 700;
}

.product-related {
  padding: 68px 24px 80px;
}

.product-related__header {
  margin-bottom: 30px;
}

.product-related__header h2 {
  margin: 0;
  color: #3b3a38;
  font-size: clamp(34px, 4vw, 56px);
  line-height: 0.95;
}

@media (max-width: 1100px) {
  .product-detail {
    grid-template-columns: fit-content(min(100%, 480px)) minmax(0, 1fr);
    gap: 34px;
  }

  .product-detail__gallery {
    width: min(100%, 480px);
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .product-detail__thumbs-wrap,
  .product-detail__thumbs {
    max-height: none;
  }

  .product-detail__thumbs-wrap,
  .product-detail__stage-wrap {
    width: 100%;
  }

  .product-detail__thumbs-wrap {
    order: 2;
  }

  .product-detail__stage-wrap {
    order: 1;
  }

  .product-detail__thumbs {
    flex-direction: row;
    overflow-x: auto;
    overflow-y: hidden;
    height: auto;
    width: 100%;
    padding-top: 6px;
    padding-right: 0;
  }

  .product-detail__thumb {
    flex: 0 0 auto;
    width: clamp(68px, 12vw, 82px);
  }

  .product-detail__thumb--active,
  .product-detail__thumb:hover {
    transform: translateY(-2px);
  }

  .product-detail__info {
    padding-top: 0;
  }

  .product-detail__info h1 {
    font-size: clamp(34px, 4vw, 48px);
  }
}

@media (max-width: 767px) {
  .product-detail__top {
    padding: 24px 24px 0;
  }

  .product-detail {
    grid-template-columns: 1fr;
    padding: 8px 24px 0;
  }

  .product-detail__gallery {
    width: 100%;
    grid-template-columns: 1fr;
  }

  .product-detail__thumbs-wrap,
  .product-detail__thumbs {
    max-height: none;
  }

  .product-detail__thumbs-wrap,
  .product-detail__stage-wrap {
    width: 100%;
  }

  .product-detail__stage-wrap,
  .product-detail__stage {
    height: min(100vw - 48px, 480px);
    min-height: min(100vw - 48px, 480px);
  }

  .product-detail__thumbs-wrap {
    order: 2;
  }

  .product-detail__stage-wrap {
    order: 1;
  }

  .product-detail__thumbs {
    flex-direction: row;
    overflow-x: auto;
    overflow-y: hidden;
    max-height: none;
    height: auto;
    width: 100%;
    padding-top: 6px;
    padding-right: 0;
  }

  .product-detail__thumb {
    flex: 0 0 auto;
    width: clamp(68px, 18vw, 82px);
  }

  .product-detail__thumb--active,
  .product-detail__thumb:hover {
    transform: translateY(-2px);
  }

  .product-detail__thumbs-wrap {
    max-height: none;
  }

  .product-detail__thumbs-fade {
    display: none;
  }

  :deep(.product-detail__carousel .slick-prev) {
    left: 8px;
  }

  :deep(.product-detail__carousel .slick-next) {
    right: 8px;
  }

  .product-detail__stage-wrap {
    min-height: auto;
  }

  .product-detail__stage {
    min-height: auto;
  }

  .product-related {
    padding: 48px 24px 64px;
  }
}

@media (max-width: 480px) {
  .product-detail__top {
    padding: 20px 24px 0;
  }

  .product-detail {
    gap: 24px;
    padding: 4px 24px 0;
  }

  .product-detail__gallery {
    gap: 16px;
  }

  .product-detail__thumbs {
    gap: 10px;
  }

  .product-detail__info h1 {
    font-size: 34px;
  }

  .product-detail__brand {
    margin-bottom: 16px;
    font-size: 16px;
  }

  .product-detail__description {
    margin-bottom: 22px;
    font-size: 14px;
    line-height: 1.7;
  }

  :deep(.product-detail__carousel .slick-arrow) {
    width: 38px;
    height: 38px;
  }
}
</style>
