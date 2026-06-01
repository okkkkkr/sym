<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { NAlert, NButton, NCard, NProgress, NSpace, NTag } from 'naive-ui'

import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import CommonPage from '@/components/page/CommonPage.vue'
import { formatDate } from '@/utils'

defineOptions({ name: '好物批量导入' })

const router = useRouter()
const fileInputRef = ref(null)
const selectedFile = ref(null)
const uploadLoading = ref(false)
const uploadPercent = ref(0)
const uploadSpeedText = ref('')
const uploadStatusText = ref('')
const uploadEtaText = ref('')
const activeUploadSession = ref(null)
const pauseRequested = ref(false)
const uploadAbortController = ref(null)
const systemTask = ref(null)
const pollingTimer = ref(null)

const chunkSize = 5 * 1024 * 1024
const maxFileSize = 1024 * 1024 * 1024
const uploadCachePrefix = 'product-import-upload:'
const activeTaskStatuses = ['uploading', 'queued', 'running']

const selectedFileLabel = computed(() => {
  if (!selectedFile.value) return '未选择文件'
  return `${selectedFile.value.name} (${formatFileSize(selectedFile.value.size)})`
})

const hasSystemTask = computed(() => activeTaskStatuses.includes(systemTask.value?.status))
const ownUploadingTask = computed(() =>
  Boolean(
    systemTask.value?.status === 'uploading' &&
      activeUploadSession.value?.task_id &&
      systemTask.value?.id === activeUploadSession.value.task_id
  )
)
const uploadLocked = computed(() => hasSystemTask.value && !ownUploadingTask.value)
const uploadButtonText = computed(() => {
  if (uploadLoading.value) return '上传中'
  if (activeUploadSession.value?.uploaded_chunks?.length) return '继续上传'
  return '开始上传'
})
const pauseButtonText = computed(() => (pauseRequested.value ? '继续上传' : '暂停上传'))
const uploadProgressStatus = computed(() => (uploadPercent.value >= 100 ? 'success' : 'info'))
const currentTaskPercent = computed(() => {
  if (
    systemTask.value?.status === 'uploading' &&
    systemTask.value?.id === activeUploadSession.value?.task_id
  ) {
    return uploadPercent.value
  }
  return systemTask.value?.progress || 0
})
const canTogglePause = computed(() => {
  if (!selectedFile.value || !ownUploadingTask.value) return false
  if (uploadLoading.value) return true
  return Boolean(
    activeUploadSession.value?.upload_id && activeUploadSession.value?.uploaded_chunks?.length
  )
})

function formatFileSize(size) {
  if (!size) return '0 B'
  if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

function formatRemainingTime(seconds) {
  if (!Number.isFinite(seconds) || seconds <= 0) return ''
  if (seconds < 60) return `预计剩余 ${Math.ceil(seconds)} 秒`
  const minutes = Math.floor(seconds / 60)
  const remainSeconds = Math.ceil(seconds % 60)
  if (minutes < 60) return `预计剩余 ${minutes} 分 ${remainSeconds} 秒`
  const hours = Math.floor(minutes / 60)
  const remainMinutes = minutes % 60
  return `预计剩余 ${hours} 小时 ${remainMinutes} 分`
}

function taskStatusLabel(status) {
  if (status === 'uploading') return '上传中'
  if (status === 'queued') return '排队中'
  if (status === 'running') return '同步中'
  if (status === 'success') return '成功'
  if (status === 'warn') return '警告'
  if (status === 'failed') return '失败'
  if (status === 'canceled') return '已取消'
  return '待处理'
}

function taskStatusType(status) {
  if (status === 'success') return 'success'
  if (status === 'warn' || status === 'running') return 'warning'
  if (status === 'failed') return 'error'
  return 'info'
}

function taskStatusDescription(status) {
  if (status === 'uploading') return '正在接收 ZIP 分片，上传完成后会自动进入后台同步。'
  if (status === 'queued') return 'ZIP 已接收完成，正在等待后台处理。'
  if (status === 'running') return '正在解析 ZIP、上传素材并写入数据库。'
  if (status === 'success') return '导入已完成。'
  if (status === 'warn') return '导入已完成，存在部分失败项。'
  if (status === 'failed') return '导入失败，请查看错误信息。'
  if (status === 'canceled') return '任务已取消。'
  return '等待处理。'
}

function triggerSelectFile() {
  if (uploadLocked.value || ownUploadingTask.value) return
  fileInputRef.value?.click()
}

function getFileFingerprint(file) {
  if (!file) return ''
  return `${file.name}:${file.size}:${file.lastModified}`
}

function getUploadCacheKey(file) {
  return `${uploadCachePrefix}${getFileFingerprint(file)}`
}

function readCachedSession(file) {
  if (!file) return null
  const raw = window.localStorage.getItem(getUploadCacheKey(file))
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    window.localStorage.removeItem(getUploadCacheKey(file))
    return null
  }
}

function writeCachedSession(file, session) {
  if (!file || !session) return
  window.localStorage.setItem(getUploadCacheKey(file), JSON.stringify(session))
}

function clearCachedSession(file = selectedFile.value) {
  if (!file) return
  window.localStorage.removeItem(getUploadCacheKey(file))
}

function updateUploadProgress(uploadedChunkCount, totalChunks) {
  uploadPercent.value = totalChunks ? Math.round((uploadedChunkCount / totalChunks) * 100) : 0
}

function formatUploadSpeed(bytesPerSecond) {
  if (!Number.isFinite(bytesPerSecond) || bytesPerSecond <= 0) return ''
  if (bytesPerSecond < 1024 * 1024) return `${(bytesPerSecond / 1024).toFixed(1)} KB/s`
  return `${(bytesPerSecond / (1024 * 1024)).toFixed(2)} MB/s`
}

function resetUploadFeedback() {
  uploadPercent.value = 0
  uploadSpeedText.value = ''
  uploadEtaText.value = ''
  pauseRequested.value = false
}

function extractActiveTask(error) {
  return error?.error?.data?.active_task || null
}

function applySystemTask(task) {
  systemTask.value = task || null
  if (!activeUploadSession.value?.task_id) return
  if (task?.id === activeUploadSession.value.task_id) return
  clearCachedSession()
  activeUploadSession.value = null
  pauseRequested.value = false
  if (!uploadLoading.value) {
    updateUploadProgress(0, 0)
    uploadSpeedText.value = ''
    uploadEtaText.value = ''
  }
}

async function refreshActiveTask() {
  const res = await api.getActiveProductImportTask()
  applySystemTask(res.data)
}

async function refreshUploadSession(uploadId = activeUploadSession.value?.upload_id) {
  if (!uploadId) return
  const res = await api.getProductImportUploadStatus({ upload_id: uploadId })
  const uploadedChunks = res.data.uploaded_chunks || []
  activeUploadSession.value = {
    upload_id: res.data.upload_id,
    task_id: res.data.task_id,
    uploaded_chunks: uploadedChunks,
    total_chunks: res.data.total_chunks,
  }
  updateUploadProgress(uploadedChunks.length, res.data.total_chunks)
  if (!uploadLoading.value) {
    uploadStatusText.value = uploadedChunks.length
      ? `已恢复上传会话，已完成 ${uploadedChunks.length}/${res.data.total_chunks} 个分片`
      : '已恢复上传会话，等待继续上传'
  }
  writeCachedSession(selectedFile.value, activeUploadSession.value)
}

async function restoreUploadSession(file) {
  activeUploadSession.value = null
  uploadStatusText.value = ''
  resetUploadFeedback()
  if (!file) return

  const cachedSession = readCachedSession(file)
  if (!cachedSession?.upload_id) return
  if (systemTask.value?.id !== cachedSession.task_id || systemTask.value?.status !== 'uploading') {
    clearCachedSession(file)
    return
  }

  try {
    await refreshUploadSession(cachedSession.upload_id)
  } catch {
    clearCachedSession(file)
    updateUploadProgress(0, 0)
  }
}

async function handleFileChange(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.zip')) {
    $message.error('仅支持 ZIP 文件')
    event.target.value = ''
    return
  }
  if (file.size > maxFileSize) {
    $message.error('文件大小不能超过 1GB')
    event.target.value = ''
    return
  }
  selectedFile.value = file
  await restoreUploadSession(file)
  event.target.value = ''
}

async function startUpload() {
  if (!selectedFile.value || uploadLoading.value || uploadLocked.value) return

  const totalChunks = Math.ceil(selectedFile.value.size / chunkSize)
  uploadLoading.value = true
  pauseRequested.value = false
  uploadSpeedText.value = ''
  uploadEtaText.value = ''
  try {
    let session = activeUploadSession.value
    if (!session?.upload_id) {
      const initRes = await api.initProductImportUpload({
        filename: selectedFile.value.name,
        file_size: selectedFile.value.size,
        total_chunks: totalChunks,
        chunk_size: chunkSize,
        import_strategy: 'create_only',
      })
      session = {
        upload_id: initRes.data.upload_id,
        task_id: initRes.data.task_id,
        uploaded_chunks: initRes.data.uploaded_chunks || [],
        total_chunks: totalChunks,
      }
      activeUploadSession.value = session
      writeCachedSession(selectedFile.value, session)
      await refreshActiveTask()
    } else {
      session = {
        ...session,
        uploaded_chunks: [...(session.uploaded_chunks || [])],
      }
    }

    const uploadedChunkSet = new Set(session.uploaded_chunks || [])
    updateUploadProgress(uploadedChunkSet.size, totalChunks)
    uploadStatusText.value = uploadedChunkSet.size
      ? `继续上传，已完成 ${uploadedChunkSet.size}/${totalChunks} 个分片`
      : '开始上传新文件'
    const startedAt = Date.now()
    let uploadedBytes = Math.min(uploadedChunkSet.size * chunkSize, selectedFile.value.size)

    for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex += 1) {
      if (uploadedChunkSet.has(chunkIndex)) continue
      if (pauseRequested.value) {
        uploadStatusText.value = `上传已暂停，当前已完成 ${uploadedChunkSet.size}/${totalChunks} 个分片`
        uploadSpeedText.value = ''
        uploadEtaText.value = ''
        return
      }

      const start = chunkIndex * chunkSize
      const end = Math.min(selectedFile.value.size, start + chunkSize)
      const formData = new FormData()
      formData.append('upload_id', session.upload_id)
      formData.append('chunk_index', String(chunkIndex))
      formData.append(
        'file',
        selectedFile.value.slice(start, end),
        `${selectedFile.value.name}.part${chunkIndex}`
      )
      uploadAbortController.value = new AbortController()
      const chunkRes = await api.uploadProductImportChunk(formData, {
        signal: uploadAbortController.value.signal,
      })
      uploadAbortController.value = null
      const uploadedChunks = chunkRes.data.uploaded_chunks || []
      uploadedChunkSet.clear()
      uploadedChunks.forEach((item) => uploadedChunkSet.add(item))
      session.uploaded_chunks = [...uploadedChunkSet]
      activeUploadSession.value = session
      writeCachedSession(selectedFile.value, session)

      uploadedBytes += end - start
      const elapsedSeconds = Math.max((Date.now() - startedAt) / 1000, 1)
      const bytesPerSecond = uploadedBytes / elapsedSeconds
      uploadSpeedText.value = formatUploadSpeed(bytesPerSecond)
      uploadEtaText.value = formatRemainingTime(
        (selectedFile.value.size - uploadedBytes) / bytesPerSecond
      )
      uploadStatusText.value = `正在上传第 ${chunkIndex + 1}/${totalChunks} 个分片`
      updateUploadProgress(uploadedChunkSet.size, totalChunks)
    }

    await api.completeProductImportUpload({ upload_id: session.upload_id })
    clearCachedSession(selectedFile.value)
    activeUploadSession.value = null
    selectedFile.value = null
    updateUploadProgress(0, 0)
    uploadStatusText.value = 'ZIP 上传成功，导入任务已进入队列'
    uploadSpeedText.value = ''
    uploadEtaText.value = ''
    await refreshActiveTask()
    $message.success('ZIP 上传成功，导入任务已进入队列')
  } catch (error) {
    uploadAbortController.value = null
    if (error.code === 'ERR_CANCELED' && pauseRequested.value) {
      uploadStatusText.value = `上传已暂停，当前已完成 ${
        activeUploadSession.value?.uploaded_chunks?.length || 0
      }/${totalChunks} 个分片`
      uploadSpeedText.value = ''
      uploadEtaText.value = ''
      return
    }
    const activeTask = extractActiveTask(error)
    if (activeTask) {
      applySystemTask(activeTask)
      uploadStatusText.value = '系统已有进行中的好物导入任务，请等待当前任务完成后再上传'
    } else {
      uploadStatusText.value = '上传中断，可稍后继续上传'
    }
    uploadSpeedText.value = ''
    uploadEtaText.value = ''
    $message.error(error.message || '上传失败')
  } finally {
    uploadLoading.value = false
  }
}

function togglePauseUpload() {
  if (uploadLoading.value) {
    pauseRequested.value = true
    uploadStatusText.value = '正在等待当前分片上传完成后暂停'
    uploadAbortController.value?.abort()
    return
  }
  if (activeUploadSession.value?.upload_id) {
    startUpload()
  }
}

function goToTaskCenter() {
  if (systemTask.value?.id) {
    router.push(`/batch/product-import-task?task_id=${systemTask.value.id}`)
    return
  }
  router.push('/batch/product-import-task')
}

function startPolling() {
  if (pollingTimer.value) return
  pollingTimer.value = window.setInterval(async () => {
    if (document.hidden) return
    try {
      await refreshActiveTask()
      if (ownUploadingTask.value) {
        await refreshUploadSession()
      }
    } catch {
      // ignore polling failure
    }
  }, 3000)
}

function stopPolling() {
  if (!pollingTimer.value) return
  window.clearInterval(pollingTimer.value)
  pollingTimer.value = null
}

onMounted(async () => {
  try {
    await refreshActiveTask()
  } catch {
    // ignore first screen failure
  }
  startPolling()
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<template>
  <CommonPage title="好物批量导入">
    <template #action>
      <NButton
        v-permission="'get/api/v1/product/import/template'"
        @click="api.downloadProductImportTemplate()"
      >
        <TheIcon icon="mdi:file-download-outline" :size="18" class="mr-5" />下载模板
      </NButton>
      <NButton
        v-permission="'get/api/v1/product/import/example'"
        @click="api.downloadProductImportExample()"
      >
        <TheIcon icon="mdi:folder-zip-outline" :size="18" class="mr-5" />下载示例包
      </NButton>
      <NButton
        v-permission="'get/api/v1/product/import/tasks'"
        type="default"
        @click="goToTaskCenter"
      >
        <TheIcon icon="material-symbols:task-outline" :size="18" class="mr-5" />任务中心
      </NButton>
    </template>

    <NSpace vertical :size="16">
      <NAlert type="info" :show-icon="false">
        支持上传不超过 1GB 的 ZIP 包。ZIP 可先包含一层总目录，导入根目录必须包含
        product.xlsx，素材目录名需与 Excel 中的 name 精确一致。
      </NAlert>

      <NCard v-if="systemTask" title="当前系统导入任务" size="small">
        <NSpace vertical :size="14">
          <div class="task-head">
            <div>
              <div class="task-title">{{ systemTask.filename }}</div>
              <div class="task-subtitle">
                发起人：{{ systemTask.created_by_name }} · 创建时间：{{
                  formatDate(systemTask.created_at)
                }}
              </div>
            </div>
            <NTag :type="taskStatusType(systemTask.status)">{{
              taskStatusLabel(systemTask.status)
            }}</NTag>
          </div>

          <NAlert v-if="uploadLocked" type="warning" :show-icon="false">
            当前系统已有导入任务处理中，请等待完成或取消后再上传新的 ZIP 包。
          </NAlert>

          <div class="task-description">{{ taskStatusDescription(systemTask.status) }}</div>

          <div class="task-metrics">
            <div class="task-metric-card">
              <div class="task-metric-label">任务ID</div>
              <div class="task-metric-value">#{{ systemTask.id }}</div>
            </div>
            <div class="task-metric-card">
              <div class="task-metric-label">处理进度</div>
              <div class="task-metric-value">{{ currentTaskPercent }}%</div>
            </div>
            <div class="task-metric-card">
              <div class="task-metric-label">成功数量</div>
              <div class="task-metric-value">{{ systemTask.success_count || 0 }}</div>
            </div>
            <div class="task-metric-card">
              <div class="task-metric-label">失败数量</div>
              <div class="task-metric-value">{{ systemTask.failed_count || 0 }}</div>
            </div>
          </div>

          <NProgress
            type="line"
            :percentage="currentTaskPercent"
            :status="currentTaskPercent >= 100 ? 'success' : 'info'"
            indicator-placement="inside"
          />

          <div class="task-meta-grid">
            <div class="task-meta-item">
              已处理 {{ systemTask.processed_count || 0 }}/{{ systemTask.total_count || 0 }} 行
            </div>
            <div class="task-meta-item">
              开始时间：{{ systemTask.started_at ? formatDate(systemTask.started_at) : '-' }}
            </div>
            <div class="task-meta-item">导入策略：{{ systemTask.import_strategy || '-' }}</div>
            <div class="task-meta-item">
              更新时间：{{ systemTask.updated_at ? formatDate(systemTask.updated_at) : '-' }}
            </div>
          </div>

          <div v-if="systemTask.error_message" class="task-error">
            {{ systemTask.error_message }}
          </div>

          <NSpace>
            <NButton type="primary" secondary @click="goToTaskCenter">查看任务记录</NButton>
          </NSpace>
        </NSpace>
      </NCard>

      <NCard title="上传 ZIP 包" size="small">
        <NSpace vertical :size="12">
          <input
            ref="fileInputRef"
            type="file"
            accept=".zip"
            style="display: none"
            @change="handleFileChange"
          />
          <div class="upload-panel">
            <div class="upload-meta">
              <div class="upload-name">{{ selectedFileLabel }}</div>
              <div class="upload-desc">导入策略：仅新增，不覆盖历史数据</div>
              <div v-if="uploadStatusText" class="upload-status">{{ uploadStatusText }}</div>
              <div v-if="uploadSpeedText" class="upload-speed">上传速度：{{ uploadSpeedText }}</div>
              <div v-if="uploadEtaText" class="upload-eta">{{ uploadEtaText }}</div>
            </div>
            <NSpace>
              <NButton :disabled="uploadLocked || ownUploadingTask" @click="triggerSelectFile">
                选择 ZIP
              </NButton>
              <NButton
                v-permission="'post/api/v1/product/import/upload-init'"
                type="primary"
                :disabled="!selectedFile || uploadLocked"
                :loading="uploadLoading"
                @click="startUpload"
              >
                {{ uploadButtonText }}
              </NButton>
              <NButton :disabled="!canTogglePause" @click="togglePauseUpload">
                {{ pauseButtonText }}
              </NButton>
            </NSpace>
          </div>
          <NProgress
            v-if="uploadLoading || uploadPercent > 0"
            :status="uploadProgressStatus"
            class="upload-progress"
            type="line"
            :percentage="uploadPercent"
            indicator-placement="inside"
          />
        </NSpace>
      </NCard>

      <NCard title="导入说明" size="small">
        <NSpace vertical :size="10">
          <div>1. 支持 ZIP 外层总目录，导入根目录需为 product.xlsx + 一层素材目录结构。</div>
          <div>2. 品牌、分类、标签均按名称精确匹配。</div>
          <div>3. 图片目录至少包含一张图片，优先使用文件名含 _cover 的图片作为封面。</div>
          <div>4. 同名好物会直接拦截并记为失败，不会创建重复记录。</div>
        </NSpace>
      </NCard>
    </NSpace>
  </CommonPage>
</template>

<style scoped>
.task-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.task-title {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}

.task-subtitle {
  margin-top: 6px;
  color: #6b7280;
  line-height: 1.5;
}

.task-description {
  color: #374151;
  line-height: 1.6;
}

.task-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.task-metric-card {
  padding: 12px;
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e5e7eb;
}

.task-metric-label {
  color: #6b7280;
  font-size: 12px;
}

.task-metric-value {
  margin-top: 8px;
  font-size: 24px;
  font-weight: 700;
  color: #111827;
}

.task-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.task-meta-item {
  padding: 12px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  color: #374151;
}

.task-error {
  color: #b91c1c;
  padding: 12px;
  border-radius: 10px;
  background: #fef2f2;
}

.upload-panel {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.upload-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.upload-name {
  font-size: 15px;
  color: #1f2937;
}

.upload-desc {
  font-size: 13px;
  color: #6b7280;
}

.upload-status {
  font-size: 13px;
  color: #2563eb;
}

.upload-speed {
  font-size: 13px;
  color: #059669;
}

.upload-eta {
  font-size: 13px;
  color: #7c3aed;
}

@media (max-width: 768px) {
  .task-metrics,
  .task-meta-grid {
    grid-template-columns: 1fr;
  }
}
</style>
