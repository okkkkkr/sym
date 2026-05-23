<script setup>
import {
  computed,
  h,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
} from 'vue'
import {
  NButton,
  NCard,
  NDrawer,
  NDrawerContent,
  NEmpty,
  NPopconfirm,
  NProgress,
  NSelect,
  NSpace,
  NTag,
} from 'naive-ui'

import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { usePermissionStore, useUserStore } from '@/store'
import { formatDate } from '@/utils'

defineOptions({ name: '导入任务记录' })

const $table = ref(null)
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const permissionStore = usePermissionStore()
const queryItems = ref({ status: null })
const sorter = ref({ columnKey: 'created_at', order: 'descend' })
const tableData = ref([])
const detailVisible = ref(false)
const currentTask = ref(null)
const detailItems = ref([])
const detailLoading = ref(false)
const detailStatus = ref(null)
const detailPagination = reactive({ page: 1, page_size: 20, total: 0 })
const pollingTimer = ref(null)

const statusOptions = [
  { label: '全部状态', value: null },
  { label: '待处理', value: 'pending' },
  { label: '上传中', value: 'uploading' },
  { label: '排队中', value: 'queued' },
  { label: '执行中', value: 'running' },
  { label: '成功', value: 'success' },
  { label: '警告', value: 'warn' },
  { label: '失败', value: 'failed' },
  { label: '已取消', value: 'canceled' },
]

function getTaskTableData(params = {}) {
  return api.getProductImportTasks(params)
}

function canAccess(permission) {
  if (userStore.isSuperUser) return true
  return permissionStore.apis.includes(permission)
}

function statusTagType(status) {
  if (status === 'success') return 'success'
  if (status === 'warn' || status === 'running') return 'warning'
  if (status === 'failed') return 'error'
  return 'info'
}

function itemStatusTagType(status) {
  if (status === 'success') return 'success'
  if (status === 'failed') return 'error'
  return 'warning'
}

function statusLabel(status) {
  return (
    statusOptions.find((item) => item.value === status)?.label ||
    detailStatusOptions.find((item) => item.value === status)?.label ||
    status ||
    '-'
  )
}

function canRetryTask(row) {
  return ['failed', 'warn', 'canceled'].includes(row?.status)
}

function canRetryFailedRows(row) {
  return canRetryTask(row) && Number(row?.failed_count || 0) > 0
}

function canCancelTask(row) {
  return ['pending', 'uploading', 'queued', 'running'].includes(row?.status)
}

const taskSummaryCards = computed(() => {
  const tasks = tableData.value || []
  const total = tasks.length
  const runningCount = tasks.filter((item) =>
    ['pending', 'uploading', 'queued', 'running'].includes(item.status),
  ).length
  const failedCount = tasks.filter((item) =>
    ['warn', 'failed'].includes(item.status),
  ).length
  const latestFinished = tasks.find((item) =>
    ['success', 'warn', 'failed', 'canceled'].includes(item.status),
  )

  return [
    {
      key: 'total',
      title: '最近任务数',
      value: total,
      helper: total ? '当前列表页已加载任务' : '暂无任务记录',
    },
    {
      key: 'running',
      title: '运行中任务',
      value: runningCount,
      helper: runningCount ? '包含待处理 / 上传中 / 排队中 / 执行中' : '当前没有运行中任务',
    },
    {
      key: 'failed',
      title: '失败任务',
      value: failedCount,
      helper: failedCount ? '建议优先查看错误报告或重试' : '当前列表页无失败任务',
    },
    {
      key: 'latest',
      title: '最近完成状态',
      value: latestFinished ? statusLabel(latestFinished.status) : '无',
      helper: latestFinished
        ? `${latestFinished.filename} · ${formatDate(latestFinished.finished_at || latestFinished.updated_at || latestFinished.created_at)}`
        : '等待首个完成任务',
    },
  ]
})

const detailStatusOptions = [
  { label: '全部明细', value: null },
  { label: '成功', value: 'success' },
  { label: '失败', value: 'failed' },
  { label: '跳过', value: 'skipped' },
  { label: '待处理', value: 'pending' },
]

const isCurrentTaskRunning = computed(() =>
  ['queued', 'running', 'uploading', 'pending'].includes(currentTask.value?.status),
)
const hasActiveTasks = computed(() =>
  (tableData.value || []).some((item) =>
    ['pending', 'uploading', 'queued', 'running'].includes(item.status),
  ),
)
const shouldPoll = computed(
  () =>
    !document.hidden &&
    (hasActiveTasks.value || (detailVisible.value && isCurrentTaskRunning.value)),
)
const detailStatusBreakdown = computed(
  () => currentTask.value?.detail_summary?.status_breakdown || [],
)
const detailErrorCategories = computed(
  () => currentTask.value?.detail_summary?.error_categories || [],
)
const detailOverviewCards = computed(() => {
  if (!currentTask.value) return []
  const resultSummary = currentTask.value.result_summary || {}
  return [
    {
      key: 'total',
      label: '模板总行数',
      value: resultSummary.total_count ?? currentTask.value.total_count ?? 0,
    },
    {
      key: 'valid',
      label: '预校验通过',
      value: resultSummary.valid_rows ?? currentTask.value.success_count ?? 0,
    },
    {
      key: 'invalid',
      label: '预校验失败',
      value: resultSummary.invalid_rows ?? currentTask.value.failed_count ?? 0,
    },
    {
      key: 'processed',
      label: '已处理行数',
      value: currentTask.value.processed_count ?? 0,
    },
  ]
})

const columns = computed(() => [
  {
    title: '任务ID',
    key: 'id',
    width: 90,
    align: 'center',
  },
  {
    title: '文件名',
    key: 'filename',
    minWidth: 220,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '状态',
    key: 'status',
    width: 120,
    align: 'center',
    render(row) {
      return h(NTag, { type: statusTagType(row.status) }, { default: () => statusLabel(row.status) })
    },
  },
  {
    title: '进度',
    key: 'progress',
    width: 100,
    align: 'center',
    render(row) {
      return `${row.progress || 0}%`
    },
  },
  {
    title: '成功/失败',
    key: 'result',
    width: 120,
    align: 'center',
    render(row) {
      return `${row.success_count || 0}/${row.failed_count || 0}`
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    align: 'center',
    render(row) {
      return formatDate(row.created_at)
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 280,
    align: 'center',
    render(row) {
      const actions = [
        h(
          NButton,
          {
            size: 'tiny',
            quaternary: true,
            type: 'primary',
            onClick: () => openTaskDetail(row),
          },
          { default: () => '详情' },
        ),
      ]
      if (canAccess('get/api/v1/product/import/task/errors')) {
        actions.push(
          h(
            NButton,
            {
              size: 'tiny',
              quaternary: true,
              type: 'info',
              disabled: !row.error_report_path,
              onClick: () => api.downloadProductImportErrors(row.id),
            },
            { default: () => '错误报告' },
          ),
        )
      }
      if (canAccess('post/api/v1/product/import/task/retry-failed')) {
        actions.push(
          h(
            NPopconfirm,
            { onPositiveClick: () => handleRetryFailed(row) },
            {
              trigger: () =>
                h(
                  NButton,
                  {
                    size: 'tiny',
                    quaternary: true,
                    type: 'warning',
                    disabled: !canRetryFailedRows(row),
                  },
                  { default: () => '失败项重试' },
                ),
              default: () => '确认仅重试当前任务的失败项吗？',
            },
          ),
        )
      }
      if (canAccess('post/api/v1/product/import/task/cancel')) {
        actions.push(
          h(
            NPopconfirm,
            { onPositiveClick: () => handleCancel(row) },
            {
              trigger: () =>
                h(
                  NButton,
                  {
                    size: 'tiny',
                    quaternary: true,
                    type: 'error',
                    disabled: !canCancelTask(row),
                  },
                  { default: () => '取消' },
                ),
              default: () => '确认取消该导入任务吗？',
            },
          ),
        )
      }
      return h('div', { style: 'display:flex;justify-content:center;gap:8px;flex-wrap:wrap;' }, actions)
    },
  },
])

async function openTaskDetail(row) {
  detailVisible.value = true
  currentTask.value = row
  detailStatus.value = null
  detailPagination.page = 1
  try {
    await Promise.all([fetchTaskDetail(row.id), fetchDetailItems()])
  } catch (error) {
    $message.error(error.message || '读取任务详情失败')
  } finally {
    if (!currentTask.value?.id) {
      detailVisible.value = false
    }
  }
}

async function fetchTaskDetail(taskId = currentTask.value?.id) {
  if (!taskId) return
  const taskRes = await api.getProductImportTask({ task_id: taskId })
  currentTask.value = taskRes.data
}

async function fetchDetailItems() {
  if (!currentTask.value?.id) return
  detailLoading.value = true
  try {
    const itemsRes = await api.getProductImportTaskItems({
      task_id: currentTask.value.id,
      page: detailPagination.page,
      page_size: detailPagination.page_size,
      status: detailStatus.value,
    })
    detailItems.value = itemsRes.data || []
    detailPagination.total = itemsRes.total || 0
  } finally {
    detailLoading.value = false
  }
}

async function handleDetailPageChange(page) {
  detailPagination.page = page
  await fetchDetailItems()
}

async function handleDetailPageSizeChange(pageSize) {
  detailPagination.page_size = pageSize
  detailPagination.page = 1
  await fetchDetailItems()
}

async function handleDetailStatusChange(value) {
  detailStatus.value = value
  detailPagination.page = 1
  await fetchDetailItems()
}

function handleTaskDataChange(data) {
  tableData.value = data || []
  syncPollingState()
}

function closeDetail() {
  detailVisible.value = false
  syncPollingState()
}

async function handleRetry(row) {
  await api.retryProductImportTask({ task_id: row.id })
  $message.success('任务已重新入队')
  $table.value?.handleSearch()
  if (currentTask.value?.id === row.id) {
    await Promise.all([fetchTaskDetail(row.id), fetchDetailItems()])
  }
}

async function handleRetryFailed(row) {
  const res = await api.retryFailedProductImportTask({ task_id: row.id })
  $message.success('失败项已重新入队')
  await $table.value?.handleSearch()
  if (res.data?.task_id) {
    await openTaskDetail({ id: res.data.task_id })
  }
}

async function handleCancel(row) {
  await api.cancelProductImportTask({ task_id: row.id })
  $message.success('任务已取消')
  $table.value?.handleSearch()
  if (currentTask.value?.id === row.id) {
    await Promise.all([fetchTaskDetail(row.id), fetchDetailItems()])
  }
}

function startPolling() {
  if (pollingTimer.value || !shouldPoll.value) return
  stopPolling()
  pollingTimer.value = window.setInterval(async () => {
    await $table.value?.handleSearch()
    if (detailVisible.value && currentTask.value?.id) {
      await fetchTaskDetail(currentTask.value.id)
      if (isCurrentTaskRunning.value) {
        await fetchDetailItems()
      }
    }
    syncPollingState()
  }, 3000)
}

function stopPolling() {
  if (pollingTimer.value) {
    window.clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}

function syncPollingState() {
  if (shouldPoll.value) {
    startPolling()
    return
  }
  stopPolling()
}

function handleVisibilityChange() {
  syncPollingState()
}

onMounted(async () => {
  await $table.value?.handleSearch()
  const taskId = Number(route.query.task_id || 0)
  if (taskId) {
    await openTaskDetail({ id: taskId })
  }
  document.addEventListener('visibilitychange', handleVisibilityChange)
  syncPollingState()
})

onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  stopPolling()
})
</script>

<template>
  <CommonPage title="导入任务记录">
    <template #action>
      <NButton type="default" @click="router.push('/batch/product-import')">
        <TheIcon icon="material-symbols:upload-file-outline" :size="18" class="mr-5" />去上传
      </NButton>
    </template>

    <div class="summary-grid">
      <NCard v-for="card in taskSummaryCards" :key="card.key" size="small" class="summary-card">
        <div class="summary-title">{{ card.title }}</div>
        <div class="summary-value">{{ card.value }}</div>
        <div class="summary-helper">{{ card.helper }}</div>
      </NCard>
    </div>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:sorter="sorter"
      :columns="columns"
      :get-data="getTaskTableData"
      :scroll-x="1100"
      @on-data-change="handleTaskDataChange"
    >
      <template #queryBar>
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

    <NDrawer
      v-model:show="detailVisible"
      placement="right"
      :width="720"
      @after-leave="currentTask = null"
    >
      <NDrawerContent
        v-if="currentTask"
        :title="`任务详情 #${currentTask.id}`"
        closable
        @close="closeDetail"
      >
        <NSpace vertical :size="16">
          <div class="detail-meta">
            <NTag :type="statusTagType(currentTask.status)">{{
              statusLabel(currentTask.status)
            }}</NTag>
            <span>文件：{{ currentTask.filename }}</span>
            <span>进度：{{ currentTask.progress || 0 }}%</span>
            <span>成功：{{ currentTask.success_count || 0 }}</span>
            <span>失败：{{ currentTask.failed_count || 0 }}</span>
          </div>

          <NProgress
            type="line"
            :percentage="currentTask.progress || 0"
            :status="currentTask.progress === 100 ? 'success' : 'info'"
            indicator-placement="inside"
          />

          <div class="detail-overview-grid">
            <div class="detail-overview-card">
              <div class="detail-overview-label">创建时间</div>
              <div class="detail-overview-value">{{ formatDate(currentTask.created_at) }}</div>
            </div>
            <div class="detail-overview-card">
              <div class="detail-overview-label">开始时间</div>
              <div class="detail-overview-value">
                {{ currentTask.started_at ? formatDate(currentTask.started_at) : '-' }}
              </div>
            </div>
            <div class="detail-overview-card">
              <div class="detail-overview-label">结束时间</div>
              <div class="detail-overview-value">
                {{ currentTask.finished_at ? formatDate(currentTask.finished_at) : '-' }}
              </div>
            </div>
            <div class="detail-overview-card">
              <div class="detail-overview-label">导入策略</div>
              <div class="detail-overview-value">{{ currentTask.import_strategy || '-' }}</div>
            </div>
          </div>

          <div class="detail-metric-grid">
            <div v-for="card in detailOverviewCards" :key="card.key" class="detail-metric-card">
              <div class="detail-metric-label">{{ card.label }}</div>
              <div class="detail-metric-value">{{ card.value }}</div>
            </div>
          </div>

          <div class="detail-section">
            <div class="detail-section-title">行级状态分布</div>
            <div v-if="detailStatusBreakdown.length" class="detail-pill-grid">
              <div
                v-for="item in detailStatusBreakdown"
                :key="item.status"
                class="detail-pill-card"
              >
                <NTag :type="itemStatusTagType(item.status)">{{ statusLabel(item.status) }}</NTag>
                <span class="detail-pill-count">{{ item.count }}</span>
              </div>
            </div>
            <NEmpty v-else description="暂无状态分布数据" />
          </div>

          <div class="detail-section">
            <div class="detail-section-title">错误原因聚合</div>
            <div v-if="detailErrorCategories.length" class="detail-error-grid">
              <div
                v-for="item in detailErrorCategories"
                :key="item.message"
                class="detail-error-card"
              >
                <div class="detail-error-card-message">{{ item.message }}</div>
                <div class="detail-error-card-count">{{ item.count }} 次</div>
              </div>
            </div>
            <NEmpty v-else description="当前任务暂无错误聚合" />
          </div>

          <div v-if="currentTask.error_message" class="detail-error">
            {{ currentTask.error_message }}
          </div>

          <div class="detail-toolbar">
            <NSelect
              v-model:value="detailStatus"
              class="detail-filter"
              clearable
              :options="detailStatusOptions"
              placeholder="筛选明细状态"
              @update:value="handleDetailStatusChange"
            />
            <NSpace>
              <NButton
                v-if="canAccess('post/api/v1/product/import/task/retry-failed')"
                type="warning"
                secondary
                :disabled="!canRetryFailedRows(currentTask)"
                @click="handleRetryFailed(currentTask)"
              >
                失败项重试
              </NButton>
              <NButton
                v-if="canAccess('post/api/v1/product/import/task/retry')"
                type="default"
                :disabled="!canRetryTask(currentTask)"
                @click="handleRetry(currentTask)"
              >
                整任务重试
              </NButton>
            </NSpace>
            <div class="detail-toolbar-text">
              共 {{ detailPagination.total }} 条明细，当前第 {{ detailPagination.page }} 页
            </div>
          </div>

          <div v-if="detailLoading" class="detail-loading">加载中...</div>
          <div v-else-if="detailItems.length" class="detail-items">
            <div v-for="(item, index) in detailItems" :key="item.id" class="detail-item-row">
              <div class="detail-item-head">
                <div class="detail-item-title">
                  #{{ (detailPagination.page - 1) * detailPagination.page_size + index + 1 }}
                  {{ item.product_name || '-' }}
                </div>
                <NTag :type="itemStatusTagType(item.status)">{{ statusLabel(item.status) }}</NTag>
              </div>
              <div class="detail-item-grid">
                <div>分类：{{ item.category_name || '-' }}</div>
                <div>品牌：{{ item.brand_name || '-' }}</div>
                <div>产品ID：{{ item.product_id || '-' }}</div>
                <div>重复提示：{{ item.duplicate_hint ? '是' : '否' }}</div>
              </div>
              <div class="detail-item-message">{{ item.message || '-' }}</div>
            </div>
          </div>
          <NEmpty v-else description="当前筛选条件下暂无明细" />

          <div class="detail-pagination">
            <n-pagination
              :page="detailPagination.page"
              :page-size="detailPagination.page_size"
              :item-count="detailPagination.total"
              :page-sizes="[20, 50, 100]"
              show-size-picker
              @update:page="handleDetailPageChange"
              @update:page-size="handleDetailPageSizeChange"
            />
          </div>
        </NSpace>
      </NDrawerContent>
    </NDrawer>
  </CommonPage>
</template>

<style scoped>
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.summary-card {
  min-height: 132px;
}

.summary-title {
  font-size: 13px;
  color: #6b7280;
}

.summary-value {
  margin-top: 12px;
  font-size: 28px;
  font-weight: 700;
  color: #111827;
}

.summary-helper {
  margin-top: 10px;
  line-height: 1.5;
  color: #4b5563;
}

.detail-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.detail-overview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.detail-metric-card {
  padding: 12px;
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e5e7eb;
}

.detail-metric-label {
  font-size: 12px;
  color: #6b7280;
}

.detail-metric-value {
  margin-top: 8px;
  font-size: 24px;
  font-weight: 700;
  color: #111827;
}

.detail-overview-card {
  padding: 12px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
}

.detail-overview-label {
  font-size: 12px;
  color: #6b7280;
}

.detail-overview-value {
  margin-top: 6px;
  color: #111827;
}

.detail-error {
  color: #b91c1c;
  padding: 12px;
  border-radius: 10px;
  background: #fef2f2;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-section-title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.detail-pill-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.detail-pill-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
}

.detail-pill-count {
  font-weight: 700;
  color: #111827;
}

.detail-error-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-error-card {
  padding: 12px;
  border-radius: 10px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
}

.detail-error-card-message {
  line-height: 1.5;
  color: #9a3412;
}

.detail-error-card-count {
  margin-top: 8px;
  font-weight: 700;
  color: #c2410c;
}

.detail-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.detail-filter {
  width: 220px;
}

.detail-toolbar-text {
  color: #6b7280;
  font-size: 13px;
}

.detail-loading {
  color: #6b7280;
  padding: 16px 0;
}

.detail-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-item-row {
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
}

.detail-item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.detail-item-title {
  font-weight: 600;
  color: #111827;
}

.detail-item-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 12px;
  margin-bottom: 10px;
  color: #4b5563;
}

.detail-item-message {
  color: #4b5563;
}

.detail-pagination {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .summary-grid,
  .detail-metric-grid,
  .detail-overview-grid,
  .detail-pill-grid,
  .detail-error-grid,
  .detail-item-grid {
    grid-template-columns: 1fr;
  }

  .detail-pagination {
    justify-content: flex-start;
  }
}
</style>
