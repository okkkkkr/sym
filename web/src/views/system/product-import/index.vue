<script setup>
import { computed, ref } from 'vue'
import { NAlert, NButton, NCard, NProgress, NSpace, NTag } from 'naive-ui'

import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import CommonPage from '@/components/page/CommonPage.vue'

defineOptions({ name: '好物批量导入' })

const router = useRouter()
const fileInputRef = ref(null)
const selectedFile = ref(null)
const uploadLoading = ref(false)
const uploadPercent = ref(0)
const latestTask = ref(null)
const uploadSpeedText = ref('')
const uploadStatusText = ref('')
const uploadEtaText = ref('')
const activeUploadSession = ref(null)
const pauseRequested = ref(false)

const chunkSize = 5 * 1024 * 1024
const maxFileSize = 500 * 1024 * 1024
const uploadCachePrefix = 'product-import-upload:'

const selectedFileLabel = computed(() => {
  if (!selectedFile.value) return '未选择文件'
  return `${selectedFile.value.name} (${formatFileSize(selectedFile.value.size)})`
})

const uploadButtonText = computed(() => {
  if (uploadLoading.value) return '上传中'
  if (activeUploadSession.value?.uploaded_chunks?.length) return '继续上传'
  return '开始上传'
})

const pauseButtonText = computed(() => (pauseRequested.value ? '继续上传' : '暂停上传'))

const canTogglePause = computed(() => {
  if (!selectedFile.value) return false
  if (uploadLoading.value) return true
  return Boolean(activeUploadSession.value?.upload_id && activeUploadSession.value?.uploaded_chunks?.length)
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

function triggerSelectFile() {
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
  if (bytesPerSecond < 1024 * 1024) {
    return `${(bytesPerSecond / 1024).toFixed(1)} KB/s`
  }
  return `${(bytesPerSecond / (1024 * 1024)).toFixed(2)} MB/s`
}

async function restoreUploadSession(file) {
  activeUploadSession.value = null
  uploadStatusText.value = ''
  uploadSpeedText.value = ''
  uploadEtaText.value = ''
  pauseRequested.value = false
  if (!file) return

  const cachedSession = readCachedSession(file)
  if (!cachedSession?.upload_id) {
    uploadPercent.value = 0
    return
  }

  try {
    const res = await api.getProductImportUploadStatus({ upload_id: cachedSession.upload_id })
    const uploadedChunks = res.data.uploaded_chunks || []
    activeUploadSession.value = {
      upload_id: res.data.upload_id,
      task_id: res.data.task_id,
      uploaded_chunks: uploadedChunks,
      total_chunks: res.data.total_chunks,
    }
    updateUploadProgress(uploadedChunks.length, res.data.total_chunks)
    uploadStatusText.value = uploadedChunks.length
      ? `已恢复上传会话，已完成 ${uploadedChunks.length}/${res.data.total_chunks} 个分片`
      : '已恢复上传会话，等待继续上传'
    writeCachedSession(file, activeUploadSession.value)
  } catch {
    clearCachedSession(file)
    uploadPercent.value = 0
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
    $message.error('文件大小不能超过 500MB')
    event.target.value = ''
    return
  }
  selectedFile.value = file
  await restoreUploadSession(file)
  event.target.value = ''
}

async function startUpload() {
  if (!selectedFile.value || uploadLoading.value) return

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
      const chunkRes = await api.uploadProductImportChunk(formData)
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
      uploadEtaText.value = formatRemainingTime((selectedFile.value.size - uploadedBytes) / bytesPerSecond)
      uploadStatusText.value = `正在上传第 ${chunkIndex + 1}/${totalChunks} 个分片`
      updateUploadProgress(uploadedChunkSet.size, totalChunks)
    }

    await api.completeProductImportUpload({ upload_id: session.upload_id })
    const taskRes = await api.getProductImportTask({ task_id: session.task_id })
    latestTask.value = taskRes.data
    uploadStatusText.value = '上传完成，导入任务已进入队列'
    uploadSpeedText.value = ''
    uploadEtaText.value = ''
    clearCachedSession(selectedFile.value)
    activeUploadSession.value = null
    $message.success('导入任务已创建并进入队列')
    router.push(`/batch/product-import-task?task_id=${session.task_id}`)
  } catch (error) {
    uploadStatusText.value = '上传中断，可稍后继续上传'
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
    return
  }
  if (activeUploadSession.value?.upload_id) {
    startUpload()
  }
}

function goToTaskCenter() {
  router.push('/batch/product-import-task')
}
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
        支持上传不超过 500MB 的 ZIP 包。ZIP 可先包含一层总目录，导入根目录必须包含 product.xlsx，素材目录名需与 Excel 中的
        name 精确一致。
      </NAlert>

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
              <NButton @click="triggerSelectFile">选择 ZIP</NButton>
              <NButton
                v-permission="'post/api/v1/product/import/upload-init'"
                type="primary"
                :disabled="!selectedFile"
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
            class="upload-progress"
            type="line"
            :percentage="uploadPercent"
            :show-indicator="true"
          />
        </NSpace>
      </NCard>

      <NCard title="导入说明" size="small">
        <NSpace vertical :size="10">
          <div>1. 支持 ZIP 外层总目录，导入根目录需为 product.xlsx + 一层素材目录结构。</div>
          <div>2. 品牌、分类、标签均按名称精确匹配。</div>
          <div>3. 图片目录至少包含一张图片，优先使用文件名含 _cover 的图片作为封面。</div>
          <div>4. 同名好物不会覆盖，只会在结果中提示重复风险。</div>
        </NSpace>
      </NCard>

      <NCard v-if="latestTask" title="最近任务" size="small">
        <NSpace align="center" justify="space-between">
          <NSpace>
            <NTag type="info">任务ID {{ latestTask.id }}</NTag>
            <NTag type="warning">{{ latestTask.status }}</NTag>
          </NSpace>
          <NButton
            text
            type="primary"
            @click="router.push(`/batch/product-import-task?task_id=${latestTask.id}`)"
            >查看详情</NButton
          >
        </NSpace>
      </NCard>
    </NSpace>
  </CommonPage>
</template>

<style scoped>
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

.upload-progress :deep(.n-progress-graph-line-indicator) {
  white-space: nowrap;
  min-width: 40px;
}
</style>
