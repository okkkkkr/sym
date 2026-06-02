<script setup>
import { computed, h, onMounted, ref } from 'vue'
import { NInput, NSelect, NTag } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import api from '@/api'

defineOptions({ name: '联系方式点击数据' })

const $table = ref(null)
const queryItems = ref({})
const sorter = ref({ columnKey: 'click_count', order: 'descend' })

const contactTypeOptions = [
  { label: '全部类型', value: '' },
  { label: 'social', value: 'social' },
  { label: 'messaging', value: 'messaging' },
  { label: 'email', value: 'email' },
  { label: 'phone', value: 'phone' },
]

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '启用', value: 'active' },
  { label: '停用', value: 'inactive' },
  { label: '已删除', value: 'deleted' },
]

function customNextSortOrder(order) {
  if (!order) return 'descend'
  if (order === 'descend') return 'ascend'
  return false
}

function resolveStatusTag(row) {
  if (row.status === 'active') {
    return { type: 'success', label: '启用' }
  }
  if (row.status === 'inactive') {
    return { type: 'warning', label: '停用' }
  }
  return { type: 'default', label: '已删除' }
}

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = computed(() => [
  {
    title: '平台',
    key: 'platform',
    minWidth: 120,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '展示名称',
    key: 'display_name',
    minWidth: 160,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '联系类型',
    key: 'contact_type',
    width: 110,
    align: 'center',
    render(row) {
      return row.contact_type
        ? h(NTag, { type: 'info' }, { default: () => row.contact_type })
        : h('span', '-')
    },
  },
  {
    title: '联系内容',
    key: 'contact_value',
    minWidth: 200,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h('span', row.contact_value || '-')
    },
  },
  {
    title: '点击量',
    key: 'click_count',
    width: 100,
    align: 'center',
    sorter: true,
    sortOrder: sorter.value.columnKey === 'click_count' ? sorter.value.order : false,
    customNextSortOrder,
    render(row) {
      return h(NTag, { type: 'warning' }, { default: () => String(row.click_count || 0) })
    },
  },
  {
    title: '当前状态',
    key: 'status',
    width: 100,
    align: 'center',
    render(row) {
      const tag = resolveStatusTag(row)
      return h(NTag, { type: tag.type }, { default: () => tag.label })
    },
  },
])
</script>

<template>
  <CommonPage title="联系方式点击数据">
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:sorter="sorter"
      :columns="columns"
      :get-data="api.getContactClickStatsList"
      :scroll-x="1050"
    >
      <template #queryBar>
        <QueryBarItem label="关键字" :label-width="50">
          <NInput
            v-model:value="queryItems.keyword"
            clearable
            placeholder="搜索平台、名称或联系内容"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="类型" :label-width="40">
          <NSelect
            v-model:value="queryItems.contact_type"
            clearable
            :options="contactTypeOptions"
            placeholder="请选择类型"
          />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="40">
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
