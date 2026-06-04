<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  NButton,
  NCard,
  NCollapse,
  NCollapseItem,
  NEmpty,
  NFormItem,
  NIcon,
  NInput,
  NInputNumber,
  NSelect,
  NSwitch,
  NTag,
  NTooltip,
  NUpload,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'
import {
  PERSISTED_RESOURCE_STATE,
  TRANSIENT_RESOURCE_STATE,
  collectTransientResourceKeys,
  findRemovedUploadFiles,
  normalizeManagedUploadFileList,
} from '@/utils/media/resource'

defineOptions({ name: '首页装修' })

const moduleTypeOptions = [
  { label: '单图片', value: 'single_image' },
  { label: '二宫格', value: 'grid_2' },
  { label: '四宫格', value: 'grid_4' },
  { label: '八宫格', value: 'grid_8' },
  { label: '轮播图', value: 'carousel' },
  { label: '水平滑动列表', value: 'horizontal_list' },
]

const fixedItemCounts = {
  single_image: 1,
  grid_2: 2,
  grid_4: 4,
  grid_8: 8,
}

const typeLabels = moduleTypeOptions.reduce((labels, item) => {
  labels[item.value] = item.label
  return labels
}, {})

const loading = ref(false)
const saving = ref(false)
const publishing = ref(false)
const selectedModuleIndex = ref(-1)
const pendingModuleType = ref('single_image')
const sidebarExpandedNames = ref(['common-config', 'module-list'])
const itemExpandedNames = ref([])
const draftPayload = ref('')
const publishedPayload = ref('')
const hasSavedDraftToPublish = ref(false)
const layout = ref(createEmptyLayout())
const currentPublished = ref({
  version: 0,
  published_at: null,
})
let imageFileSeed = 0

function createCommonConfig() {
  return {
    show_banner: true,
    show_navigation: true,
    show_footer: true,
  }
}

function createEmptyLayout() {
  return {
    page_code: 'home',
    version: 0,
    status: 'draft',
    updated_at: null,
    common_config: createCommonConfig(),
    modules: [],
  }
}

function createAction() {
  return {
    text: '',
    link: '',
    target: 'self',
  }
}

function createItem(index = 0) {
  return {
    id: null,
    sort: index + 1,
    image: '',
    image_file_list: [],
    title: '',
    description: '',
    badge: '',
    action: createAction(),
  }
}

function createConfig(type) {
  if (type === 'single_image') {
    return { overlay: true }
  }
  if (type === 'carousel') {
    return { autoplay: true, interval: 3000, show_dots: true }
  }
  return {}
}

function createModule(type, index = 0) {
  const itemCount = fixedItemCounts[type] || 1
  return {
    id: null,
    type,
    sort: index + 1,
    is_enabled: true,
    title: '',
    action: createAction(),
    config: createConfig(type),
    items: Array.from({ length: itemCount }, (_, itemIndex) => createItem(itemIndex)),
  }
}

function getFileNameFromUrl(url) {
  const normalized = String(url || '').trim()
  if (!normalized) return 'image'
  try {
    const parsed = new URL(normalized)
    return parsed.pathname.split('/').filter(Boolean).pop() || 'image'
  } catch {
    return normalized.split('/').filter(Boolean).pop() || 'image'
  }
}

function createUploadFile(url, rawUrl = url) {
  if (!url) return null
  imageFileSeed += 1
  return {
    id: `home-layout-image-${imageFileSeed}`,
    name: getFileNameFromUrl(rawUrl || url),
    status: 'finished',
    url,
    thumbnailUrl: url,
    rawUrl,
    resourceState: PERSISTED_RESOURCE_STATE,
  }
}

function normalizeUploadFileList(fileList = []) {
  return normalizeManagedUploadFileList(
    fileList
      .map((file) => {
        if (!file) return null
        if (file.url || file.thumbnailUrl) {
          return {
            ...file,
            url: file.url || file.thumbnailUrl,
            thumbnailUrl: file.thumbnailUrl || file.url,
            rawUrl: file.rawUrl || file.url || file.thumbnailUrl || '',
          }
        }
        if (!file.file) return file
        const objectUrl = URL.createObjectURL(file.file)
        return { ...file, url: objectUrl, thumbnailUrl: objectUrl, rawUrl: file.rawUrl || '' }
      })
      .filter(Boolean)
  )
}

async function deleteMediaKeys(keys = []) {
  const normalizedKeys = [...new Set(keys.map((item) => String(item || '').trim()).filter(Boolean))]
  if (!normalizedKeys.length) return
  try {
    await api.deleteMediaFiles({ keys: normalizedKeys })
  } catch (error) {
    console.error('删除未保存首页图片失败', error)
  }
}

function normalizeLayout(data = {}) {
  const modules = Array.isArray(data.modules) ? data.modules : []
  return {
    page_code: 'home',
    version: Number(data.version || 0),
    status: data.status || 'draft',
    updated_at: data.updated_at || null,
    common_config: {
      ...createCommonConfig(),
      ...(data.common_config || {}),
    },
    modules: modules.map((module, index) => normalizeModule(module, index)),
  }
}

function normalizeModule(module = {}, index = 0) {
  const type = module.type || 'single_image'
  const normalized = {
    id: module.id ?? null,
    type,
    sort: index + 1,
    is_enabled: module.is_enabled !== false,
    title: module.title || '',
    action: normalizeAction(module.action),
    config: { ...createConfig(type), ...(module.config || {}) },
    items: Array.isArray(module.items) ? module.items : [],
  }
  ensureModuleStructure(normalized)
  return normalized
}

function normalizeItem(item = {}, index = 0) {
  const rawImage = item.image_key || item.image || ''
  const previewImage = item.image || ''
  return {
    id: item.id ?? null,
    sort: index + 1,
    image: rawImage,
    image_file_list: previewImage ? [createUploadFile(previewImage, rawImage)] : [],
    title: item.title || '',
    description: item.description || '',
    badge: item.badge || '',
    action: normalizeAction(item.action),
  }
}

function normalizeAction(action = {}) {
  return {
    text: action?.text || '',
    link: action?.link || '',
    target: action?.target || 'self',
  }
}

function ensureModuleStructure(module) {
  module.config = { ...createConfig(module.type), ...(module.config || {}) }
  const fixedCount = fixedItemCounts[module.type]
  if (fixedCount) {
    module.items = Array.from({ length: fixedCount }, (_, index) =>
      normalizeItem(module.items[index], index)
    )
  } else if (!module.items.length) {
    module.items = [createItem()]
  } else {
    module.items = module.items.map((item, index) => normalizeItem(item, index))
  }
  reindexItems(module)
}

function reindexModules() {
  layout.value.modules.forEach((module, index) => {
    module.sort = index + 1
  })
}

function reindexItems(module) {
  module.items.forEach((item, index) => {
    item.sort = index + 1
  })
}

const selectedModule = computed(() => layout.value.modules[selectedModuleIndex.value] || null)
const hasUnsavedChanges = computed(
  () => JSON.stringify(buildComparablePayload()) !== draftPayload.value
)
const hasDraftToPublish = computed(() => hasSavedDraftToPublish.value)
const saveDisabled = computed(
  () => loading.value || saving.value || publishing.value || !hasUnsavedChanges.value
)
const publishDisabled = computed(
  () =>
    loading.value ||
    saving.value ||
    publishing.value ||
    hasUnsavedChanges.value ||
    !hasDraftToPublish.value
)

async function loadPage() {
  loading.value = true
  try {
    const [draftResponse, currentResponse] = await Promise.all([
      api.getHomeLayoutDraft(),
      api.getCurrentHomeLayout(),
    ])
    layout.value = normalizeLayout(draftResponse.data)
    const publishedLayout = normalizeLayout(currentResponse.data)
    currentPublished.value = {
      version: publishedLayout.version,
      published_at: currentResponse.data?.published_at || null,
    }
    publishedPayload.value = JSON.stringify(buildComparablePayload(publishedLayout))
    draftPayload.value = JSON.stringify(buildComparablePayload())
    hasSavedDraftToPublish.value = !!draftResponse.data?.has_draft_to_publish
    selectedModuleIndex.value = layout.value.modules.length ? 0 : -1
    syncItemExpandedNames()
  } finally {
    loading.value = false
  }
}

function buildPayload(source = layout.value) {
  return {
    page_code: 'home',
    common_config: {
      show_banner: source.common_config.show_banner !== false,
      show_navigation: source.common_config.show_navigation !== false,
      show_footer: source.common_config.show_footer !== false,
    },
    modules: source.modules.map((module, moduleIndex) => ({
      id: module.id,
      type: module.type,
      sort: moduleIndex + 1,
      is_enabled: module.is_enabled,
      title: module.title.trim(),
      action: {
        text: module.action.text.trim(),
        link: module.action.link.trim(),
        target: module.action.target || 'self',
      },
      config: sanitizeConfig(module),
      items: module.items.map((item, itemIndex) => ({
        id: item.id,
        sort: itemIndex + 1,
        image: item.image.trim(),
        title: item.title.trim(),
        description: item.description.trim(),
        badge: item.badge.trim(),
        action: {
          text: item.action.text.trim(),
          link: item.action.link.trim(),
          target: item.action.target || 'self',
        },
      })),
    })),
  }
}

function buildComparablePayload(source = layout.value) {
  return {
    page_code: 'home',
    common_config: {
      show_banner: source.common_config.show_banner !== false,
      show_navigation: source.common_config.show_navigation !== false,
      show_footer: source.common_config.show_footer !== false,
    },
    modules: source.modules.map((module, moduleIndex) => ({
      type: module.type,
      sort: moduleIndex + 1,
      is_enabled: module.is_enabled,
      title: module.title.trim(),
      action: {
        text: module.action.text.trim(),
        link: module.action.link.trim(),
        target: module.action.target || 'self',
      },
      config: sanitizeConfig(module),
      items: module.items.map((item, itemIndex) => ({
        sort: itemIndex + 1,
        image: item.image.trim(),
        title: item.title.trim(),
        description: item.description.trim(),
        badge: item.badge.trim(),
        action: {
          text: item.action.text.trim(),
          link: item.action.link.trim(),
          target: item.action.target || 'self',
        },
      })),
    })),
  }
}

function sanitizeConfig(module) {
  if (module.type === 'single_image') {
    return {
      overlay: !!module.config.overlay,
    }
  }
  if (module.type === 'carousel') {
    return {
      autoplay: !!module.config.autoplay,
      interval: Number(module.config.interval || 3000),
      show_dots: !!module.config.show_dots,
    }
  }
  return {}
}

function handleAddModule() {
  const module = createModule(pendingModuleType.value, layout.value.modules.length)
  layout.value.modules.push(module)
  reindexModules()
  selectedModuleIndex.value = layout.value.modules.length - 1
  syncItemExpandedNames()
}

function handleRemoveModule(index) {
  deleteMediaKeys(
    layout.value.modules[index]?.items.flatMap((item) =>
      collectTransientResourceKeys(item.image_file_list)
    ) || []
  )
  layout.value.modules.splice(index, 1)
  reindexModules()
  if (!layout.value.modules.length) {
    selectedModuleIndex.value = -1
    syncItemExpandedNames()
    return
  }
  selectedModuleIndex.value = Math.min(index, layout.value.modules.length - 1)
  syncItemExpandedNames()
}

function moveModule(index, direction) {
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= layout.value.modules.length) return
  const [module] = layout.value.modules.splice(index, 1)
  layout.value.modules.splice(targetIndex, 0, module)
  reindexModules()
  selectedModuleIndex.value = targetIndex
}

function handleModuleTypeChange(value) {
  if (!selectedModule.value) return
  const previousTransientKeys = selectedModule.value.items.flatMap((item) =>
    collectTransientResourceKeys(item.image_file_list)
  )
  selectedModule.value.type = value
  selectedModule.value.config = createConfig(value)
  ensureModuleStructure(selectedModule.value)
  const nextTransientKeys = new Set(
    selectedModule.value.items.flatMap((item) => collectTransientResourceKeys(item.image_file_list))
  )
  deleteMediaKeys(previousTransientKeys.filter((item) => !nextTransientKeys.has(item)))
  syncItemExpandedNames()
}

function handleAddItem() {
  if (!selectedModule.value || fixedItemCounts[selectedModule.value.type]) return
  selectedModule.value.items.push(createItem(selectedModule.value.items.length))
  reindexItems(selectedModule.value)
  syncItemExpandedNames()
}

function handleRemoveItem(index) {
  if (!selectedModule.value || selectedModule.value.items.length === 1) return
  deleteMediaKeys(
    collectTransientResourceKeys(selectedModule.value.items[index]?.image_file_list || [])
  )
  selectedModule.value.items.splice(index, 1)
  reindexItems(selectedModule.value)
  syncItemExpandedNames()
}

function moveItem(index, direction) {
  if (!selectedModule.value) return
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= selectedModule.value.items.length) return
  const [item] = selectedModule.value.items.splice(index, 1)
  selectedModule.value.items.splice(targetIndex, 0, item)
  reindexItems(selectedModule.value)
  syncItemExpandedNames()
}

function syncItemExpandedNames() {
  itemExpandedNames.value = selectedModule.value
    ? selectedModule.value.items.map((_, index) => `item-${index}`)
    : []
}

function syncItemImageValue(item, fileList = []) {
  item.image_file_list = normalizeUploadFileList(fileList).slice(-1)
  item.image = item.image_file_list[0]?.rawUrl || ''
}

async function handleItemImageUpload({ file, onError, onFinish, onProgress }, item) {
  try {
    if (!file?.file) {
      throw new Error('未找到待上传图片')
    }
    const credential = await api.getHomeLayoutImageUploadToken({
      file_name: file.name,
      content_type: file.type || '',
    })
    await new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      const formData = new FormData()

      xhr.open('POST', credential.data.upload_url, true)
      xhr.upload.onprogress = (event) => {
        if (!event.lengthComputable) return
        onProgress({ percent: Math.round((event.loaded / event.total) * 100) })
      }
      xhr.onerror = () => reject(new Error('上传到七牛失败'))
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve()
          return
        }
        reject(new Error('上传到七牛失败'))
      }

      formData.append('token', credential.data.upload_token)
      formData.append('key', credential.data.object_key)
      formData.append('file', file.file)
      xhr.send(formData)
    })

    file.url = credential.data.preview_url || credential.data.url
    file.thumbnailUrl = file.url
    file.rawUrl = credential.data.object_key
    file.resourceState = TRANSIENT_RESOURCE_STATE
    if (!file.name) {
      file.name = getFileNameFromUrl(file.rawUrl)
    }
    syncItemImageValue(item, [file])
    onFinish()
  } catch (error) {
    syncItemImageValue(item, item.image_file_list)
    onError()
    if (!error?.code) {
      $message.error(error.message || '上传失败')
    }
  }
}

function handleItemImageFileListChange(item, fileList) {
  const removedFiles = findRemovedUploadFiles(item.image_file_list, fileList)
  syncItemImageValue(item, fileList)
  deleteMediaKeys(collectTransientResourceKeys(removedFiles))
}

async function handleSave() {
  saving.value = true
  try {
    const response = await api.saveHomeLayoutDraft(buildPayload())
    layout.value = normalizeLayout(response.data)
    syncItemExpandedNames()
    draftPayload.value = JSON.stringify(buildComparablePayload())
    hasSavedDraftToPublish.value = !!response.data?.has_draft_to_publish
    $message.success('首页装修草稿已保存')
  } finally {
    saving.value = false
  }
}

async function handlePublish() {
  if (!hasDraftToPublish.value) {
    $message.warning('当前没有可发布的变更')
    return
  }
  publishing.value = true
  try {
    const savedDraftResponse = await api.saveHomeLayoutDraft(buildPayload())
    layout.value = normalizeLayout(savedDraftResponse.data)
    const response = await api.publishHomeLayout({ page_code: 'home' })
    currentPublished.value = {
      version: response.data?.version || 0,
      published_at: response.data?.published_at || null,
    }
    publishedPayload.value = JSON.stringify(buildComparablePayload())
    draftPayload.value = JSON.stringify(buildComparablePayload())
    hasSavedDraftToPublish.value = false
    $message.success('首页装修已发布')
  } finally {
    publishing.value = false
  }
}

function formatPublishedMeta() {
  if (!currentPublished.value.version) {
    return '当前还没有已发布版本'
  }
  return `当前发布版本 v${currentPublished.value.version}${
    currentPublished.value.published_at ? `，发布时间 ${currentPublished.value.published_at}` : ''
  }`
}

watch(selectedModuleIndex, () => {
  syncItemExpandedNames()
})

onMounted(() => {
  loadPage()
})

onBeforeUnmount(() => {
  deleteMediaKeys(
    layout.value.modules.flatMap((module) =>
      module.items.flatMap((item) => collectTransientResourceKeys(item.image_file_list))
    )
  )
})
</script>

<template>
  <CommonPage show-footer title="首页装修">
    <template #action>
      <div class="home-layout-admin__actions">
        <div class="home-layout-admin__save-group">
          <NButton :loading="saving" :disabled="saveDisabled" @click="handleSave">保存草稿</NButton>
        </div>
        <NButton
          type="primary"
          :loading="publishing"
          :disabled="publishDisabled"
          @click="handlePublish"
        >
          发布
          <span v-if="hasDraftToPublish && !hasUnsavedChanges && layout.updated_at">
            （待发布草稿：{{ layout.updated_at }}）
          </span>
        </NButton>
      </div>
    </template>

    <div class="home-layout-admin">
      <aside class="home-layout-admin__sidebar">
        <NCard size="small" class="home-layout-admin__sidebar-card">
          <NCollapse
            v-model:expanded-names="sidebarExpandedNames"
            class="home-layout-admin__collapse"
          >
            <NCollapseItem title="公共配置" name="common-config">
              <div class="home-layout-admin__common-list">
                <div class="home-layout-admin__common-row">
                  <span>Banner 横幅</span>
                  <NSwitch v-model:value="layout.common_config.show_banner" />
                </div>
                <div class="home-layout-admin__common-row">
                  <span>导航</span>
                  <NSwitch v-model:value="layout.common_config.show_navigation" />
                </div>
                <div class="home-layout-admin__common-row">
                  <span>底部内容</span>
                  <NSwitch v-model:value="layout.common_config.show_footer" />
                </div>
              </div>
            </NCollapseItem>

            <NCollapseItem title="模块列表" name="module-list">
              <div class="home-layout-admin__module-create">
                <NSelect v-model:value="pendingModuleType" :options="moduleTypeOptions" />
                <NButton type="primary" @click="handleAddModule">新增模块</NButton>
              </div>
              <p class="home-layout-admin__published">{{ formatPublishedMeta() }}</p>
              <div v-if="layout.modules.length" class="home-layout-admin__module-list">
                <button
                  v-for="(module, index) in layout.modules"
                  :key="`${module.type}-${index}`"
                  class="home-layout-admin__module-item"
                  :class="{ 'is-active': selectedModuleIndex === index }"
                  @click="selectedModuleIndex = index"
                >
                  <div class="home-layout-admin__module-main">
                    <span>{{ index + 1 }}. {{ module.title || typeLabels[module.type] }}</span>
                    <NTag size="small" :type="module.is_enabled ? 'success' : 'default'">
                      {{ module.is_enabled ? '启用' : '停用' }}
                    </NTag>
                  </div>
                  <div class="home-layout-admin__module-sub">
                    <span>{{ typeLabels[module.type] }}</span>
                    <div class="home-layout-admin__module-buttons">
                      <NTooltip trigger="hover">
                        <template #trigger>
                          <NButton
                            quaternary
                            circle
                            size="small"
                            @click.stop="moveModule(index, -1)"
                          >
                            <TheIcon icon="tabler:arrow-up" :size="16" />
                          </NButton>
                        </template>
                        上移
                      </NTooltip>
                      <NTooltip trigger="hover">
                        <template #trigger>
                          <NButton
                            quaternary
                            circle
                            size="small"
                            @click.stop="moveModule(index, 1)"
                          >
                            <TheIcon icon="tabler:arrow-down" :size="16" />
                          </NButton>
                        </template>
                        下移
                      </NTooltip>
                      <NButton
                        quaternary
                        circle
                        size="small"
                        type="error"
                        @click.stop="handleRemoveModule(index)"
                      >
                        <TheIcon icon="material-symbols:delete-outline" :size="17" />
                      </NButton>
                    </div>
                  </div>
                </button>
              </div>
              <NEmpty v-else description="还没有模块，先新增一个吧" />
            </NCollapseItem>
          </NCollapse>
        </NCard>
      </aside>

      <section class="home-layout-admin__editor">
        <NCard v-if="selectedModule" title="模块编辑" size="small">
          <div class="home-layout-admin__grid">
            <NFormItem label="模块类型">
              <NSelect
                :value="selectedModule.type"
                :options="moduleTypeOptions"
                @update:value="handleModuleTypeChange"
              />
            </NFormItem>
            <NFormItem label="启用状态">
              <NSwitch v-model:value="selectedModule.is_enabled" />
            </NFormItem>
            <NFormItem label="模块标题" class="home-layout-admin__full">
              <NInput v-model:value="selectedModule.title" placeholder="请输入模块标题" />
            </NFormItem>
          </div>

          <div class="home-layout-admin__action-card">
            <h3>模块操作</h3>
            <div class="home-layout-admin__grid">
              <NFormItem label="文案">
                <NInput v-model:value="selectedModule.action.text" placeholder="如 Shop range" />
              </NFormItem>
              <NFormItem label="跳转地址">
                <NInput
                  v-model:value="selectedModule.action.link"
                  placeholder="/collections/best-sellers"
                />
              </NFormItem>
              <NFormItem label="打开方式">
                <NSelect
                  v-model:value="selectedModule.action.target"
                  :options="[
                    { label: '当前页打开', value: 'self' },
                    { label: '新窗口打开', value: 'blank' },
                  ]"
                />
              </NFormItem>
            </div>
          </div>

          <div
            v-if="Object.keys(selectedModule.config).length"
            class="home-layout-admin__action-card"
          >
            <h3>模块配置</h3>
            <div class="home-layout-admin__grid">
              <template v-if="selectedModule.type === 'single_image'">
                <NFormItem label="显示蒙层">
                  <NSwitch v-model:value="selectedModule.config.overlay" />
                </NFormItem>
              </template>

              <template v-if="selectedModule.type === 'carousel'">
                <NFormItem label="自动轮播">
                  <NSwitch v-model:value="selectedModule.config.autoplay" />
                </NFormItem>
                <NFormItem label="轮播间隔(ms)">
                  <NInputNumber v-model:value="selectedModule.config.interval" :min="1000" />
                </NFormItem>
                <NFormItem label="显示圆点">
                  <NSwitch v-model:value="selectedModule.config.show_dots" />
                </NFormItem>
              </template>
            </div>
          </div>

          <div class="home-layout-admin__action-card">
            <div class="home-layout-admin__section-header">
              <h3>内容项</h3>
              <NButton
                v-if="!fixedItemCounts[selectedModule.type]"
                type="primary"
                secondary
                @click="handleAddItem"
              >
                新增内容项
              </NButton>
            </div>

            <div class="home-layout-admin__items">
              <NCollapse
                v-model:expanded-names="itemExpandedNames"
                class="home-layout-admin__item-collapse"
                arrow-placement="right"
              >
                <NCollapseItem
                  v-for="(item, index) in selectedModule.items"
                  :key="`${selectedModule.type}-${index}`"
                  :name="`item-${index}`"
                  class="home-layout-admin__item-card"
                >
                  <template #header>
                    <div class="home-layout-admin__item-header">
                      <span>内容项 {{ index + 1 }}</span>
                      <div class="home-layout-admin__module-buttons">
                        <NTooltip trigger="hover">
                          <template #trigger>
                            <NButton
                              quaternary
                              circle
                              size="small"
                              @click.stop="moveItem(index, -1)"
                            >
                              <TheIcon icon="tabler:arrow-up" :size="16" />
                            </NButton>
                          </template>
                          上移
                        </NTooltip>
                        <NTooltip trigger="hover">
                          <template #trigger>
                            <NButton
                              quaternary
                              circle
                              size="small"
                              @click.stop="moveItem(index, 1)"
                            >
                              <TheIcon icon="tabler:arrow-down" :size="16" />
                            </NButton>
                          </template>
                          下移
                        </NTooltip>
                        <NButton
                          v-if="!fixedItemCounts[selectedModule.type]"
                          quaternary
                          circle
                          size="small"
                          type="error"
                          @click.stop="handleRemoveItem(index)"
                        >
                          <TheIcon icon="material-symbols:delete-outline" :size="17" />
                        </NButton>
                      </div>
                    </div>
                  </template>

                  <div class="home-layout-admin__grid">
                    <NFormItem label="图片" class="home-layout-admin__full">
                      <NUpload
                        v-model:file-list="item.image_file_list"
                        accept="image/*"
                        :custom-request="(options) => handleItemImageUpload(options, item)"
                        list-type="image-card"
                        :max="1"
                        @update:file-list="
                          (fileList) => handleItemImageFileListChange(item, fileList)
                        "
                      >
                        <NIcon v-if="item.image_file_list.length < 1" size="40">
                          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
                            <path
                              d="M368.5 240H272v-96.5c0-8.8-7.2-16-16-16s-16 7.2-16 16V240h-96.5c-8.8 0-16 7.2-16 16 0 4.4 1.8 8.4 4.7 11.3 2.9 2.9 6.9 4.7 11.3 4.7H240v96.5c0 4.4 1.8 8.4 4.7 11.3 2.9 2.9 6.9 4.7 11.3 4.7 8.8 0 16-7.2 16-16V272h96.5c8.8 0 16-7.2 16-16s-7.2-16-16-16z"
                            />
                          </svg>
                        </NIcon>
                      </NUpload>
                    </NFormItem>
                    <NFormItem label="主文案">
                      <NInput v-model:value="item.title" placeholder="主标题或文案" />
                    </NFormItem>
                    <NFormItem label="角标">
                      <NInput v-model:value="item.badge" placeholder="如 Hot / New" />
                    </NFormItem>
                    <NFormItem label="辅助文案" class="home-layout-admin__full">
                      <NInput v-model:value="item.description" placeholder="辅助说明文案" />
                    </NFormItem>
                  </div>

                  <div class="home-layout-admin__grid">
                    <NFormItem label="按钮文案">
                      <NInput v-model:value="item.action.text" placeholder="如 Shop now" />
                    </NFormItem>
                    <NFormItem label="跳转地址">
                      <NInput v-model:value="item.action.link" placeholder="/sym" />
                    </NFormItem>
                    <NFormItem label="打开方式">
                      <NSelect
                        v-model:value="item.action.target"
                        :options="[
                          { label: '当前页打开', value: 'self' },
                          { label: '新窗口打开', value: 'blank' },
                        ]"
                      />
                    </NFormItem>
                  </div>
                </NCollapseItem>
              </NCollapse>
            </div>
          </div>
        </NCard>

        <NEmpty v-else description="请选择左侧模块进行编辑" />
      </section>
    </div>
  </CommonPage>
</template>

<style scoped>
.home-layout-admin {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 16px;
  height: calc(100vh - 210px);
  min-height: 640px;
}

.home-layout-admin__actions {
  display: flex;
  gap: 12px;
}

.home-layout-admin__save-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.home-layout-admin__draft-tip {
  color: #6b7280;
  font-size: 13px;
  white-space: nowrap;
}

.home-layout-admin__module-create {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  margin-bottom: 12px;
}

.home-layout-admin__published {
  margin: 0 0 12px;
  color: #6b7280;
  font-size: 13px;
}

.home-layout-admin__sidebar-card {
  flex: 1 1 auto;
  min-height: 0;
}

.home-layout-admin__common-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.home-layout-admin__common-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.home-layout-admin__sidebar,
.home-layout-admin__editor {
  min-height: 0;
}

.home-layout-admin__sidebar {
  display: flex;
  flex-direction: column;
}

.home-layout-admin__sidebar-card,
.home-layout-admin__editor :deep(.n-card) {
  height: 100%;
}

.home-layout-admin__sidebar-card :deep(.n-card__content),
.home-layout-admin__editor :deep(.n-card__content) {
  height: 100%;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.55) transparent;
}

.home-layout-admin__sidebar-card :deep(.n-card__content::-webkit-scrollbar),
.home-layout-admin__editor :deep(.n-card__content::-webkit-scrollbar) {
  width: 10px;
}

.home-layout-admin__sidebar-card :deep(.n-card__content::-webkit-scrollbar-track),
.home-layout-admin__editor :deep(.n-card__content::-webkit-scrollbar-track) {
  background: transparent;
}

.home-layout-admin__sidebar-card :deep(.n-card__content::-webkit-scrollbar-thumb),
.home-layout-admin__editor :deep(.n-card__content::-webkit-scrollbar-thumb) {
  background: transparent;
  border-radius: 999px;
  border: 2px solid transparent;
  background-clip: padding-box;
  transition: background-color 0.2s ease;
}

.home-layout-admin__sidebar-card :deep(.n-card__content:hover::-webkit-scrollbar-thumb),
.home-layout-admin__editor :deep(.n-card__content:hover::-webkit-scrollbar-thumb) {
  background-color: rgba(148, 163, 184, 0.55);
}

.home-layout-admin__sidebar-card :deep(.n-card__content::-webkit-scrollbar-thumb:hover),
.home-layout-admin__editor :deep(.n-card__content::-webkit-scrollbar-thumb:hover) {
  background-color: rgba(249, 115, 22, 0.75);
}

.home-layout-admin__collapse :deep(.n-collapse-item__header) {
  font-weight: 600;
}

.home-layout-admin__collapse :deep(.n-collapse-item__content-inner) {
  padding-top: 12px;
}

.home-layout-admin__module-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.home-layout-admin__item-collapse :deep(.n-collapse-item) {
  margin-bottom: 12px;
  padding: 0 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
}

.home-layout-admin__item-collapse :deep(.n-collapse-item__header) {
  min-height: 56px;
  padding-top: 0;
}

.home-layout-admin__item-collapse :deep(.n-collapse-item__content-inner) {
  padding-top: 4px;
  padding-bottom: 16px;
}

.home-layout-admin__module-item {
  width: 100%;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  text-align: left;
  cursor: pointer;
}

.home-layout-admin__module-item.is-active {
  border-color: #18a058;
  box-shadow: 0 0 0 1px rgba(24, 160, 88, 0.12);
}

.home-layout-admin__module-main,
.home-layout-admin__module-sub,
.home-layout-admin__section-header,
.home-layout-admin__item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.home-layout-admin__section-header {
  margin-bottom: 12px;
}

.home-layout-admin__module-sub {
  margin-top: 8px;
  color: #6b7280;
  font-size: 13px;
}

.home-layout-admin__module-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.home-layout-admin__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 16px;
}

.home-layout-admin__full {
  grid-column: 1 / -1;
}

.home-layout-admin__action-card {
  margin-top: 20px;
}

.home-layout-admin__action-card h3 {
  margin-bottom: 12px;
  font-size: 16px;
}

.home-layout-admin__items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.home-layout-admin__item-card {
  background: #fafaf9;
}

@media (max-width: 1200px) {
  .home-layout-admin {
    grid-template-columns: 1fr;
    height: auto;
  }

  .home-layout-admin__sidebar-card :deep(.n-card__content),
  .home-layout-admin__editor :deep(.n-card__content) {
    height: auto;
    overflow: visible;
  }
}

@media (max-width: 768px) {
  .home-layout-admin__grid,
  .home-layout-admin__module-create {
    grid-template-columns: 1fr;
  }
}
</style>
