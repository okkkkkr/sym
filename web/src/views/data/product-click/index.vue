<script setup>
import { computed, h, onMounted, ref } from 'vue'
import { NInput, NSelect, NTag } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import api from '@/api'

defineOptions({ name: '好物点击数据' })

const $table = ref(null)
const queryItems = ref({})
const sorter = ref({ columnKey: 'click_count', order: 'descend' })

function customNextSortOrder(order) {
  if (!order) return 'descend'
  if (order === 'descend') return 'ascend'
  return false
}

const statusOptions = [
  { label: '全部状态', value: null },
  { label: '上架', value: true },
  { label: '下架', value: false },
]

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = computed(() => [
  {
    title: '好物名称',
    key: 'name',
    width: 200,
    ellipsis: { tooltip: true },
    fixed: 'left',
  },
  {
    title: '类目',
    key: 'category',
    width: 200,
    render(row) {
      return h('span', row.category?.name || '-')
    },
  },
  {
    title: '品牌',
    key: 'brand',
    width: 200,
    render(row) {
      return h('span', row.brand?.name || '-')
    },
  },
  {
    title: '点击量',
    key: 'click_count',
    width: 100,
    sorter: true,
    sortOrder: sorter.value.columnKey === 'click_count' ? sorter.value.order : false,
    customNextSortOrder,
    render(row) {
      return h(NTag, { type: 'warning' }, { default: () => String(row.click_count || 0) })
    },
  },
  {
    title: '启用状态',
    key: 'status',
    width: 100,
    render(row) {
      return h(NTag, { type: row.status ? 'success' : 'default' }, { default: () => (row.status ? '上架' : '下架') })
    },
  },
  {
    title: '更新时间',
    key: 'updated_at',
    width: 180,
    sorter: true,
    sortOrder: sorter.value.columnKey === 'updated_at' ? sorter.value.order : false,
    customNextSortOrder,
  },
])
</script>

<template>
  <CommonPage title="好物点击数据">
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:sorter="sorter"
      :columns="columns"
      :get-data="api.getProductClickStatsList"
      :scroll-x="980"
    >
      <template #queryBar>
        <QueryBarItem label="好物名称" :label-width="70">
          <NInput
            v-model:value="queryItems.keyword"
            clearable
            type="text"
            placeholder="搜索好物名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="上架状态" :label-width="70">
          <NSelect
            v-model:value="queryItems.status"
            clearable
            :options="statusOptions"
            placeholder="请选择状态"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>