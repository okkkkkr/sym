<script setup>
import { computed, h, onMounted, ref } from 'vue'
import { NInput, NSelect, NTag } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import api from '@/api'

defineOptions({ name: '横幅点击数据' })

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
  { label: '启用', value: true },
  { label: '停用', value: false },
]

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = computed(() => [
  {
    title: '横幅内容',
    key: 'content',
    minWidth: 180,
    ellipsis: { tooltip: true },
  },
  {
    title: '活动备注',
    key: 'note',
    minWidth: 180,
    ellipsis: { tooltip: true },
    render(row) {
      return h('span', row.note || '-')
    },
  },
  {
    title: '跳转路径',
    key: 'link_url',
    minWidth: 180,
    ellipsis: { tooltip: true },
    render(row) {
      return h('span', row.link_url || '-')
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
    key: 'is_active',
    width: 100,
    render(row) {
      return h(NTag, { type: row.is_active ? 'success' : 'default' }, { default: () => (row.is_active ? '启用' : '停用') })
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
  <CommonPage title="横幅点击数据">
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:sorter="sorter"
      :columns="columns"
      :get-data="api.getBannerClickStatsList"
      :scroll-x="1100"
    >
      <template #queryBar>
        <QueryBarItem label="关键字" :label-width="50">
          <NInput
            v-model:value="queryItems.keyword"
            clearable
            type="text"
            placeholder="搜索横幅内容或活动备注"
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