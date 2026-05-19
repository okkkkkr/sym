<script setup>
import { h, onMounted, ref } from 'vue'
import { NDatePicker, NInput } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import api from '@/api'
import { resolveTimezoneRegionLabel } from '@/utils'

defineOptions({ name: '访问量数据' })

const $table = ref(null)
const queryItems = ref({})
const datetimeRange = ref(null)

onMounted(() => {
  $table.value?.handleSearch()
})

function formatTimestamp(timestamp) {
  const date = new Date(timestamp)
  const pad = (num) => String(num).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

function handleDateRangeChange(value) {
  if (!value) {
    queryItems.value.start_time = null
    queryItems.value.end_time = null
    return
  }

  queryItems.value.start_time = formatTimestamp(value[0])
  queryItems.value.end_time = formatTimestamp(value[1])
}

const columns = [
  {
    title: '访客标识',
    key: 'visitor_id',
    minWidth: 180,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '所属区域',
    key: 'region',
    minWidth: 180,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      const rawTimezone = row.region || ''
      const mappedRegion = resolveTimezoneRegionLabel(rawTimezone)

      return h('div', { style: 'line-height: 1.5; text-align: center;' }, [
        h('div', mappedRegion),
        h(
          'div',
          {
            style: 'font-size: 12px; color: var(--n-text-color-disabled);',
          },
          rawTimezone || '-'
        ),
      ])
    },
  },
  {
    title: '用户代理',
    key: 'user_agent',
    minWidth: 320,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h('span', row.user_agent || '-')
    },
  },
  {
    title: '访问时间',
    key: 'visited_at',
    width: 180,
    align: 'center',
  },
]
</script>

<template>
  <CommonPage title="访问量数据">
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getSiteVisitStatsList"
      :scroll-x="980"
    >
      <template #queryBar>
        <QueryBarItem label="关键字" :label-width="50">
          <NInput
            v-model:value="queryItems.keyword"
            clearable
            type="text"
            placeholder="搜索访客标识或用户代理"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="区域" :label-width="40">
          <NInput
            v-model:value="queryItems.region"
            clearable
            type="text"
            placeholder="请输入原始时区，如 Asia/Shanghai"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="时间范围" :label-width="70" :content-width="320">
          <NDatePicker
            v-model:value="datetimeRange"
            type="datetimerange"
            clearable
            style="width: 320px"
            @update:value="handleDateRangeChange"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>