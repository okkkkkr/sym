<script setup>
import { computed, h, ref, watch } from 'vue'
import { NDataTable, NModal, NTag } from 'naive-ui'

import api from '@/api'
import { formatDate } from '@/utils'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '关联好物',
  },
  filters: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['update:show'])

const loading = ref(false)
const productList = ref([])

const modalShow = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value),
})

const columns = [
  {
    title: '好物名称',
    key: 'name',
    align: 'center',
    width: 180,
    ellipsis: { tooltip: true },
  },
  {
    title: '好物识别码',
    key: 'product_code',
    align: 'center',
    width: 180,
    ellipsis: { tooltip: true },
    render(row) {
      return row.product_code || '-'
    },
  },
  {
    title: '所属分类',
    key: 'category_name',
    align: 'center',
    width: 140,
    render(row) {
      return row.category_name || row.category?.name || '-'
    },
  },
  {
    title: '所属品牌',
    key: 'brand_name',
    align: 'center',
    width: 140,
    render(row) {
      return row.brand_name || row.brand?.name || '-'
    },
  },
  {
    title: '关联标签',
    key: 'tags',
    align: 'center',
    minWidth: 220,
    render(row) {
      if (!row.tags?.length) {
        return '-'
      }
      return h(
        'div',
        { style: 'display: flex; flex-wrap: wrap; justify-content: center; gap: 6px;' },
        row.tags.map((item) =>
          h(NTag, { size: 'small', type: 'info', bordered: false }, { default: () => item.name })
        )
      )
    },
  },
  {
    title: '点击量',
    key: 'click_count',
    align: 'center',
    width: 90,
    render(row) {
      return h(NTag, { type: 'warning' }, { default: () => String(row.click_count ?? 0) })
    },
  },
  {
    title: '上架状态',
    key: 'status',
    align: 'center',
    width: 100,
    render(row) {
      return h(NTag, { type: row.status ? 'success' : 'default' }, { default: () => (row.status ? '上架' : '下架') })
    },
  },
  {
    title: '更新时间',
    key: 'updated_at',
    align: 'center',
    width: 180,
    render(row) {
      return formatDate(row.updated_at)
    },
  },
]

async function loadProducts() {
  loading.value = true
  try {
    const res = await api.getProductList({
      page: 1,
      page_size: 999,
      ...props.filters,
    })
    productList.value = res.data || []
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.show, JSON.stringify(props.filters || {})],
  ([show]) => {
    if (show) {
      loadProducts()
      return
    }
    productList.value = []
  },
  { immediate: true }
)
</script>

<template>
  <NModal
    v-model:show="modalShow"
    preset="card"
    :title="title"
    style="width: 80%; max-width: 80vw;"
    :mask-closable="true"
  >
    <NDataTable
      :loading="loading"
      :columns="columns"
      :data="productList"
      :bordered="false"
      :single-line="false"
      :pagination="false"
      :max-height="520"
      :scroll-x="1180"
      :row-key="(row) => row.id"
    />
  </NModal>
</template>