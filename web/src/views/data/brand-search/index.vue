<script setup>
import { computed, h, onMounted, ref } from 'vue'
import { NInput, NSelect, NTag } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import api from '@/api'

defineOptions({ name: '品牌检索数据' })

const $table = ref(null)
const queryItems = ref({})
const sorter = ref({ columnKey: 'search_count', order: 'descend' })

function customNextSortOrder(order) {
  if (!order) return 'descend'
  if (order === 'descend') return 'ascend'
  return false
}

const statusOptions = [
  { label: '全部状态', value: null },
  { label: '启用', value: true },
  { label: '停用', value: false },
]

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = computed(() => [
  {
    title: '品牌名称',
    key: 'name',
    minWidth: 180,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '类目',
    key: 'category',
    minWidth: 140,
    align: 'center',
    render(row) {
      return h('span', row.category?.name || '-')
    },
  },
  {
    title: '检索次数',
    key: 'search_count',
    width: 110,
    align: 'center',
    sorter: true,
    sortOrder: sorter.value.columnKey === 'search_count' ? sorter.value.order : false,
    customNextSortOrder,
    render(row) {
      return h(NTag, { type: 'info' }, { default: () => String(row.search_count || 0) })
    },
  },
  {
    title: '启用状态',
    key: 'is_active',
    width: 100,
    align: 'center',
    render(row) {
      return h(NTag, { type: row.is_active ? 'success' : 'default' }, { default: () => (row.is_active ? '启用' : '停用') })
    },
  },
  {
    title: '更新时间',
    key: 'updated_at',
    width: 180,
    align: 'center',
    sorter: true,
    sortOrder: sorter.value.columnKey === 'updated_at' ? sorter.value.order : false,
    customNextSortOrder,
  },
])
</script>

<template>
  <CommonPage title="品牌检索数据">
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:sorter="sorter"
      :columns="columns"
      :get-data="api.getBrandSearchStatsList"
      :scroll-x="860"
    >
      <template #queryBar>
        <QueryBarItem label="品牌名称" :label-width="70">
          <NInput
            v-model:value="queryItems.name"
            clearable
            type="text"
            placeholder="请输入品牌名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="40">
          <NSelect
            v-model:value="queryItems.is_active"
            clearable
            :options="statusOptions"
            placeholder="请选择状态"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>