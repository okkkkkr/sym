<script setup>
import { computed, h, onMounted, ref } from 'vue'
import { NInput, NTag } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import api from '@/api'

defineOptions({ name: '渠道访问数据' })

const $table = ref(null)
const queryItems = ref({})
const sorter = ref({ columnKey: 'click_count', order: 'descend' })

function customNextSortOrder(order) {
  if (!order) return 'descend'
  if (order === 'descend') return 'ascend'
  return false
}

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = computed(() => [
  {
    title: '渠道名称',
    key: 'platform_name',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '自定义名称',
    key: 'custom_name',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '渠道访问数据',
    key: 'click_count',
    width: 130,
    align: 'center',
    sorter: true,
    sortOrder: sorter.value.columnKey === 'click_count' ? sorter.value.order : false,
    customNextSortOrder,
    render(row) {
      return h(NTag, { type: 'warning' }, { default: () => String(row.click_count || 0) })
    },
  },
  {
    title: '渠道状态',
    key: 'status',
    width: 110,
    align: 'center',
    render(row) {
      return h(
        NTag,
        { type: row.status === 'active' ? 'success' : 'default' },
        {
          default: () => (row.status === 'active' ? '正常' : '已删除'),
        }
      )
    },
  },
])
</script>

<template>
  <CommonPage title="渠道访问数据">
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:sorter="sorter"
      :columns="columns"
      :get-data="api.getChannelVisitStatsList"
    >
      <template #queryBar>
        <QueryBarItem label="关键字" :label-width="50">
          <NInput
            v-model:value="queryItems.keyword"
            clearable
            placeholder="搜索渠道名称或自定义名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
