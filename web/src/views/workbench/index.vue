<template>
  <AppPage :show-footer="false">
    <n-spin :show="isLoading">
      <div class="workbench-dashboard">
        <n-card class="hero-card" :bordered="false">
          <div class="metric-grid">
            <button
              v-for="item in statisticData"
              :key="item.id"
              class="metric-card"
              type="button"
              @click="navigateToRoute(item.routeName)"
            >
              <span class="metric-card__label">{{ item.label }}</span>
              <strong class="metric-card__value">{{ item.value }}</strong>
              <span class="metric-card__hint">{{ item.hint }}</span>
            </button>
          </div>
        </n-card>

        <div class="dashboard-layout">
          <div class="ranking-grid">
            <n-card
              v-for="panel in rankingPanels"
              :key="panel.id"
              :title="panel.title"
              size="small"
              rounded-10
            >
              <template #header-extra>
                <button class="ranking-card__link" type="button" @click="navigateToRoute(panel.routeName)">
                  {{ $t('views.workbench.action_view_more') }}
                </button>
              </template>

              <div class="ranking-card">
                <div v-if="panel.items.length" class="ranking-list">
                  <button
                    v-for="(item, index) in panel.items"
                    :key="item.id || `${panel.id}-${index}`"
                    class="ranking-item"
                    type="button"
                    @click="navigateToRoute(panel.routeName)"
                  >
                    <span class="ranking-item__index">{{ String(index + 1).padStart(2, '0') }}</span>
                    <div class="ranking-item__body">
                      <strong class="ranking-item__title">{{ panel.getTitle(item) }}</strong>
                      <span class="ranking-item__meta">{{ panel.getMeta(item) }}</span>
                    </div>
                    <strong class="ranking-item__value">{{ panel.getValue(item) }}</strong>
                  </button>
                </div>
                <div v-else class="ranking-empty">{{ $t('views.workbench.text_rank_empty') }}</div>
              </div>
            </n-card>
          </div>
        </div>
      </div>
    </n-spin>
  </AppPage>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import api from '@/api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n({ useScope: 'global' })
const router = useRouter()
const isLoading = ref(false)

const dashboardState = ref({
  productTotal: 0,
  activeProductTotal: 0,
  inactiveProductTotal: 0,
  categoryTotal: 0,
  activeCategoryTotal: 0,
  inactiveCategoryTotal: 0,
  brandTotal: 0,
  activeBrandTotal: 0,
  inactiveBrandTotal: 0,
  contactTotal: 0,
  activeContactTotal: 0,
  inactiveContactTotal: 0,
  todayAuditTotal: 0,
  todayVisitTotal: 0,
})

const rankingState = ref({
  productClicks: [],
  brandSearches: [],
  bannerClicks: [],
})

const statisticData = computed(() => [
  {
    id: 0,
    label: t('views.workbench.label_today_visits'),
    value: dashboardState.value.todayVisitTotal,
    hint: t('views.workbench.text_today_visit_hint', {
      count: dashboardState.value.todayAuditTotal,
    }),
    routeName: '访问量数据',
  },
  {
    id: 1,
    label: t('views.workbench.label_product_total'),
    value: dashboardState.value.productTotal,
    hint: t('views.workbench.text_product_status', {
      active: dashboardState.value.activeProductTotal,
      inactive: dashboardState.value.inactiveProductTotal,
    }),
    routeName: '好物管理',
  },
  {
    id: 2,
    label: t('views.workbench.label_active_products'),
    value: dashboardState.value.activeProductTotal,
    hint: t('views.workbench.text_product_coverage', {
      total: dashboardState.value.productTotal,
    }),
    routeName: '好物管理',
  },
  {
    id: 3,
    label: t('views.workbench.label_category_total'),
    value: dashboardState.value.categoryTotal,
    hint: t('views.workbench.text_active_count', {
      count: dashboardState.value.activeCategoryTotal,
    }),
    routeName: '分类管理',
  },
  {
    id: 4,
    label: t('views.workbench.label_brand_total'),
    value: dashboardState.value.brandTotal,
    hint: t('views.workbench.text_active_count', {
      count: dashboardState.value.activeBrandTotal,
    }),
    routeName: '品牌管理',
  },
])

const rankingPanels = computed(() => [
  {
    id: 'product-click',
    title: t('views.workbench.label_top_product_clicks'),
    routeName: '好物点击数据',
    items: rankingState.value.productClicks,
    getTitle: (item) => item.name || '-',
    getMeta: (item) => [item.category?.name, item.brand?.name].filter(Boolean).join(' / ') || t('views.workbench.text_rank_no_meta'),
    getValue: (item) => item.click_count || 0,
  },
  {
    id: 'brand-search',
    title: t('views.workbench.label_top_brand_searches'),
    routeName: '品牌检索数据',
    items: rankingState.value.brandSearches,
    getTitle: (item) => item.name || '-',
    getMeta: (item) => item.category?.name || t('views.workbench.text_rank_no_meta'),
    getValue: (item) => item.search_count || 0,
  },
  {
    id: 'banner-click',
    title: t('views.workbench.label_top_banner_clicks'),
    routeName: '横幅点击数据',
    items: rankingState.value.bannerClicks,
    getTitle: (item) => item.content || '-',
    getMeta: (item) => item.note || item.link_url || t('views.workbench.text_rank_no_meta'),
    getValue: (item) => item.click_count || 0,
  },
])

function navigateToRoute(routeName) {
  if (!routeName) return

  const candidates = [routeName, `${routeName}Default`]
  const matchedName = candidates.find((item) => router.hasRoute(item))

  if (!matchedName) {
    $message.warning(t('views.workbench.message_route_missing'))
    return
  }

  router.push({ name: matchedName })
}

async function fetchDashboardData() {
  try {
    const { data } = await api.getDashboardOverview()

    dashboardState.value = {
      productTotal: data?.product_total || 0,
      activeProductTotal: data?.active_product_total || 0,
      inactiveProductTotal: data?.inactive_product_total || 0,
      categoryTotal: data?.category_total || 0,
      activeCategoryTotal: data?.active_category_total || 0,
      inactiveCategoryTotal: data?.inactive_category_total || 0,
      brandTotal: data?.brand_total || 0,
      activeBrandTotal: data?.active_brand_total || 0,
      inactiveBrandTotal: data?.inactive_brand_total || 0,
      contactTotal: data?.contact_total || 0,
      activeContactTotal: data?.active_contact_total || 0,
      inactiveContactTotal: data?.inactive_contact_total || 0,
      todayAuditTotal: data?.today_audit_total || 0,
      todayVisitTotal: data?.today_visit_total || 0,
    }
  } catch (error) {
    console.error('fetchDashboardData error', error)
  }
}

async function fetchRankingData() {
  try {
    const [productRes, brandRes, bannerRes] = await Promise.all([
      api.getProductClickStatsList({ page: 1, page_size: 10 }),
      api.getBrandSearchStatsList({ page: 1, page_size: 10 }),
      api.getBannerClickStatsList({ page: 1, page_size: 10 }),
    ])

    rankingState.value = {
      productClicks: productRes?.data || [],
      brandSearches: brandRes?.data || [],
      bannerClicks: bannerRes?.data || [],
    }
  } catch (error) {
    console.error('fetchRankingData error', error)
  }
}

async function fetchWorkbenchData() {
  isLoading.value = true

  try {
    await Promise.all([fetchDashboardData(), fetchRankingData()])
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchWorkbenchData()
})
</script>

<style scoped>
.workbench-dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-card :deep(.n-card__content) {
  background: linear-gradient(135deg, #fff8f1 0%, #fff 60%, #f8fbff 100%);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  border: 1px solid rgba(237, 125, 49, 0.14);
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  padding: 16px;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
  border-color: rgba(237, 125, 49, 0.3);
}

.metric-card__label {
  font-size: 13px;
  color: rgba(23, 32, 51, 0.6);
}

.metric-card__value {
  font-size: 32px;
  line-height: 1;
  color: #172033;
}

.metric-card__hint {
  font-size: 12px;
  color: #eb6a31;
}

.dashboard-layout {
  display: block;
}

.ranking-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.ranking-card {
  min-height: 360px;
}

.ranking-card__link {
  padding: 0;
  border: 0;
  background: transparent;
  color: #eb6a31;
  font-size: 13px;
  cursor: pointer;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ranking-item {
  width: 100%;
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 14px 12px;
  border: 1px solid #eef2f8;
  border-radius: 14px;
  background: linear-gradient(180deg, #fff 0%, #fbfcfe 100%);
  text-align: left;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.ranking-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
  border-color: rgba(237, 125, 49, 0.28);
}

.ranking-item__index {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(235, 106, 49, 0.1);
  color: #eb6a31;
  font-weight: 700;
  font-size: 13px;
}

.ranking-item__body {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ranking-item__title {
  font-size: 14px;
  color: #172033;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ranking-item__meta {
  font-size: 12px;
  color: rgba(23, 32, 51, 0.58);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ranking-item__value {
  font-size: 18px;
  font-weight: 700;
  color: var(--n-info-color, #2080f0);
  line-height: 1;
}

.ranking-empty {
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #e7ecf3;
  border-radius: 16px;
  color: rgba(23, 32, 51, 0.45);
  background: linear-gradient(180deg, #fff 0%, #fbfcfe 100%);
}

@media (max-width: 1280px) {
  .metric-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .ranking-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .metric-grid {
    grid-template-columns: 1fr;
  }

  .ranking-item {
    grid-template-columns: 32px minmax(0, 1fr);
  }

  .ranking-item__value {
    grid-column: 2;
  }
}
</style>
