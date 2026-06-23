<script setup>
import {
  computed,
  h,
  onBeforeUnmount,
  onMounted,
  ref,
  resolveDirective,
  watch,
  withDirectives,
} from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NIcon,
  NImage,
  NInput,
  NInputNumber,
  NPopconfirm,
  NSelect,
  NSwitch,
  NTabPane,
  NTabs,
  NTag,
  NUpload,
} from 'naive-ui'

import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import BatchDeleteModal from '@/components/table/BatchDeleteModal.vue'
import BatchExportModal from '@/components/table/BatchExportModal.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { formatDate } from '@/utils'
import {
  PERSISTED_RESOURCE_STATE,
  TRANSIENT_RESOURCE_STATE,
  collectTransientResourceKeys,
  findRemovedUploadFiles,
  markUploadFilesPersisted,
  normalizeManagedUploadFileList,
} from '@/utils/media/resource'

defineOptions({ name: '好物管理' })

const router = useRouter()

const DEFAULT_DETAIL_DESCRIPTION = JSON.stringify(
  [
    {
      type: 'text',
      title: '产品介绍',
      content: '请填写该好物的核心卖点、材质亮点与适用场景。',
    },
  ],
  null,
  2
)

let uploadFileSeed = 0
const mediaIndexPattern = /_(\d+)(?:\.[^.]+)?$/
const uuidPrefixPattern = /^[0-9a-f]{32}_(.+)$/i

const $table = ref(null)
const queryItems = ref({})
const sorter = ref({ columnKey: 'updated_at', order: 'descend' })
const checkedRowKeys = ref([])
const batchDeleteModalVisible = ref(false)
const batchExportModalVisible = ref(false)
const categories = ref([])
const brands = ref([])
const tags = ref([])
const modalVisible = ref(false)
const modalLoading = ref(false)
const exportLoading = ref(false)
const modalAction = ref('add')
const modalFormRef = ref(null)
const statusUpdatingIds = ref([])
const vPermission = resolveDirective('permission')
const actionCellStyle =
  'display: flex; justify-content: center; align-items: center; gap: 8px; flex-wrap: wrap;'
const hasActiveFilters = computed(() =>
  Object.values(queryItems.value).some(isEffectiveFilterValue)
)

function isEffectiveFilterValue(value) {
  if (Array.isArray(value)) return value.length > 0
  return value !== null && value !== undefined && value !== '' && value !== 'all'
}

const initForm = () => ({
  id: undefined,
  category_id: null,
  brand_id: null,
  tag_ids: [],
  name: '',
  product_code_custom: '',
  product_code: '',
  desc: '',
  detail_description_text: DEFAULT_DETAIL_DESCRIPTION,
  cover_file_list: [],
  image_file_list: [],
  video_file_list: [],
  click_count: 0,
  status: true,
  order: null,
})

const modalForm = ref(initForm())

const rules = {
  category_id: {
    required: true,
    type: 'number',
    message: '请选择所属分类',
    trigger: ['change', 'blur'],
  },
  brand_id: {
    required: true,
    type: 'number',
    message: '请选择所属品牌',
    trigger: ['change', 'blur'],
  },
  name: {
    required: true,
    message: '请输入好物名称',
    trigger: ['input', 'blur'],
  },
  product_code_custom: {
    validator: () => true,
    trigger: ['input', 'blur'],
  },
  cover_file_list: {
    required: true,
    validator: (_, value) => {
      if (buildUploadKeys(value).length) return true
      return new Error('请上传封面图')
    },
    trigger: ['change', 'blur'],
  },
}

const modalTitle = computed(() => (modalAction.value === 'edit' ? '编辑好物' : '新增好物'))

const categoryOptions = computed(() =>
  categories.value.map((item) => ({
    label: item.name,
    value: item.id,
  }))
)

const queryBrandOptions = computed(() => {
  const selectedCategoryId = queryItems.value.category_id
  return brands.value
    .filter((item) => !selectedCategoryId || (item.category_ids || []).includes(selectedCategoryId))
    .map((item) => ({ label: item.name, value: item.id }))
})

const modalBrandOptions = computed(() => {
  const selectedCategoryId = modalForm.value.category_id
  return brands.value
    .filter((item) => !selectedCategoryId || (item.category_ids || []).includes(selectedCategoryId))
    .map((item) => ({ label: item.name, value: item.id }))
})

const tagOptions = computed(() =>
  tags.value.map((item) => ({
    label: item.name,
    value: item.id,
  }))
)

const statusOptions = [
  { label: '全部状态', value: 'all' },
  { label: '上架', value: 'true' },
  { label: '下架', value: 'false' },
]

function normalizeBooleanFilter(value) {
  if (value === 'true') return true
  if (value === 'false') return false
  return undefined
}

function getProductTableData(params = {}) {
  const { status, ...rest } = params
  const normalizedStatus = normalizeBooleanFilter(status)
  return api.getProductList({
    ...rest,
    ...(normalizedStatus === undefined ? {} : { status: normalizedStatus }),
  })
}

function customNextSortOrder(order) {
  if (!order) return 'descend'
  if (order === 'descend') return 'ascend'
  return false
}

function nextUploadFileId(prefix = 'file') {
  uploadFileSeed += 1
  return `${prefix}-${Date.now()}-${uploadFileSeed}`
}

function getFileNameFromUrl(url, prefix = 'file') {
  if (!url) return `${prefix}-${uploadFileSeed}`
  const [path] = String(url).split('?')
  const fileName = path.split('/').pop()
  return decodeURIComponent(fileName || `${prefix}-${uploadFileSeed}`)
}

function getMediaSortName(value) {
  const fileName = getFileNameFromUrl(value)
  const matched = fileName.match(uuidPrefixPattern)
  return matched?.[1] || fileName
}

function getMediaSortIndex(value) {
  const matched = getMediaSortName(value).match(mediaIndexPattern)
  return matched ? Number(matched[1]) : null
}

function compareMediaOrder(left, right) {
  const leftName = getMediaSortName(left).toLowerCase()
  const rightName = getMediaSortName(right).toLowerCase()
  const leftIndex = getMediaSortIndex(left)
  const rightIndex = getMediaSortIndex(right)
  if (leftIndex !== null && rightIndex !== null && leftIndex !== rightIndex) {
    return leftIndex - rightIndex
  }
  if (leftIndex !== null) return -1
  if (rightIndex !== null) return 1
  return leftName.localeCompare(rightName)
}

function sortUploadFileList(fileList = []) {
  return [...fileList].sort((left, right) =>
    compareMediaOrder(
      left?.rawUrl || left?.name || left?.url || left?.thumbnailUrl || '',
      right?.rawUrl || right?.name || right?.url || right?.thumbnailUrl || ''
    )
  )
}

function isImageUploadPrefix(prefix = 'file') {
  return prefix === 'cover' || prefix === 'image'
}

function decorateUploadFile(file, prefix = 'file') {
  if (!file) return file
  const normalizedFile = { ...file }
  const previewUrl = normalizedFile.url || normalizedFile.thumbnailUrl || ''

  if (isImageUploadPrefix(prefix) && previewUrl) {
    normalizedFile.thumbnailUrl = previewUrl
    normalizedFile.type = normalizedFile.type || 'image/*'
  }

  return normalizedFile
}

function createUploadFile(url, prefix = 'file', rawUrl = url) {
  if (!url) return null
  return decorateUploadFile(
    {
      id: nextUploadFileId(prefix),
      name: getFileNameFromUrl(url, prefix),
      status: 'finished',
      url,
      rawUrl,
      resourceState: PERSISTED_RESOURCE_STATE,
    },
    prefix
  )
}

function createVideoResourceFile(resource, fallbackName = '') {
  if (!resource?.id) return null
  return {
    id: nextUploadFileId('video'),
    name: fallbackName || `video-${resource.id}.mp4`,
    status: 'finished',
    url: '',
    rawUrl: '',
    videoResourceId: resource.id,
    videoStatus: resource.status || 'pending',
    errorMessage: resource.error_message || '',
    deleteToken: resource.delete_token || `video-resource:${resource.id}`,
    resourceState: TRANSIENT_RESOURCE_STATE,
  }
}

function createVideoResourceFileFromItem(item = {}) {
  if (item?.type === 'key') {
    return createUploadFile(item.url || item.value, 'video', item.value)
  }
  if (item?.type === 'resource' && item.resource?.id) {
    const resource = item.resource
    return {
      id: nextUploadFileId('video'),
      name: getFileNameFromUrl(resource.public_url || `video-${resource.id}.mp4`, 'video'),
      status: 'finished',
      url: resource.public_url || '',
      rawUrl: resource.storage_key || '',
      videoResourceId: resource.id,
      videoStatus: resource.status || 'pending',
      errorMessage: resource.error_message || '',
      deleteToken: resource.delete_token || `video-resource:${resource.id}`,
      resourceState:
        resource.status === 'uploaded' && resource.storage_key
          ? PERSISTED_RESOURCE_STATE
          : TRANSIENT_RESOURCE_STATE,
    }
  }
  return null
}

function buildPresetUploadList(urls = [], prefix = 'file', rawUrls = []) {
  return urls
    .map((url, index) => createUploadFile(url, prefix, rawUrls[index] || url))
    .filter(Boolean)
}

function normalizeUploadFileList(fileList = [], prefix = 'file') {
  const normalizedList = normalizeManagedUploadFileList(
    fileList
      .filter((item) => item?.status !== 'removed')
      .map((item) => {
        if (item.url || item.thumbnailUrl) return decorateUploadFile(item, prefix)
        const objectUrl = item.file ? URL.createObjectURL(item.file) : ''
        return objectUrl ? decorateUploadFile({ ...item, url: objectUrl }, prefix) : item
      })
  )
  return prefix === 'image' ? sortUploadFileList(normalizedList) : normalizedList
}

async function deleteMediaKeys(keys = []) {
  const normalizedKeys = [...new Set(keys.map((item) => String(item || '').trim()).filter(Boolean))]
  if (!normalizedKeys.length) return
  try {
    await api.deleteMediaFiles({ keys: normalizedKeys })
  } catch (error) {
    console.error('删除未保存媒体失败', error)
  }
}

function buildUploadKeys(fileList = []) {
  const uploadKeys = normalizeUploadFileList(fileList)
    .filter((item) => !item?.status || item.status === 'finished')
    .map((item) => String(item.rawUrl || item.url || item.thumbnailUrl || '').trim())
    .filter((url) => !url.startsWith('blob:'))
    .filter(Boolean)
  return sortUploadFileList(
    uploadKeys.map((item) => ({
      rawUrl: item,
      name: getFileNameFromUrl(item),
    }))
  ).map((item) => item.rawUrl)
}

function buildVideoItems(fileList = []) {
  return normalizeUploadFileList(fileList, 'video')
    .filter((item) => !item?.status || item.status === 'finished')
    .map((item) => {
      if (item.videoResourceId) {
        return { type: 'resource', value: Number(item.videoResourceId) }
      }
      const key = String(item.rawUrl || item.url || '').trim()
      return key && !key.startsWith('blob:') ? { type: 'key', value: key } : null
    })
    .filter(Boolean)
}

function syncUploadField(fieldName, prefix) {
  modalForm.value[fieldName] = normalizeUploadFileList(modalForm.value[fieldName], prefix)
}

function applyUploadedFile(fieldName, prefix, file, url) {
  if (url) {
    file.url = url
  }
  if (url && isImageUploadPrefix(prefix)) {
    file.thumbnailUrl = url
  }
  if (!file.name) {
    file.name = getFileNameFromUrl(file.rawUrl || url, prefix)
  }
  Object.assign(file, decorateUploadFile(file, prefix))
  syncUploadField(fieldName, prefix)
}

function createProductMediaUploadRequest(fieldName, prefix, mediaType) {
  return async ({ file, onError, onFinish, onProgress }) => {
    try {
      if (!file?.file) {
        throw new Error('未找到待上传文件')
      }

      const response = await api.uploadProductMedia(file.file, mediaType, {
        onUploadProgress: (event) => {
          if (!event.total) return
          onProgress({ percent: Math.round((event.loaded / event.total) * 100) })
        },
      })
      const result = response.data || {}
      if (mediaType === 'video') {
        const uploadedFile = createVideoResourceFile(result, file.name || file.file?.name || '')
        if (!uploadedFile) {
          throw new Error('视频上传响应无效')
        }
        Object.assign(file, uploadedFile)
        syncUploadField(fieldName, prefix)
      } else {
        file.rawUrl = result.key
        file.resourceState = TRANSIENT_RESOURCE_STATE
        applyUploadedFile(fieldName, prefix, file, result.url)
      }
      onFinish()
    } catch (error) {
      syncUploadField(fieldName, prefix)
      onError()
      if (!error?.code) {
        $message.error(error.message || '上传失败')
      }
    }
  }
}

const uploadCoverFile = createProductMediaUploadRequest('cover_file_list', 'cover', 'cover')
const uploadImageFile = createProductMediaUploadRequest('image_file_list', 'image', 'image')
const uploadVideoFile = createProductMediaUploadRequest('video_file_list', 'video', 'video')

const columns = computed(() => [
  {
    type: 'selection',
    width: 48,
    align: 'center',
    fixed: 'left',
  },
  {
    title: '好物名称',
    key: 'name',
    width: 200,
    ellipsis: { tooltip: true },
  },
  {
    title: '好物识别码',
    key: 'product_code',
    width: 250,
    ellipsis: { tooltip: true },
    render(row) {
      return h('span', row.product_code || '-')
    },
  },
  {
    title: '所属品牌',
    key: 'brand',
    width: 200,
    align: 'center',
    render(row) {
      return h('span', row.brand_name || row.brand?.name || '-')
    },
  },
  {
    title: '所属分类',
    key: 'category',
    width: 200,
    render(row) {
      return h('span', row.category_name || row.category?.name || '-')
    },
  },
  {
    title: '关联标签',
    key: 'tags',
    width: 120,
    render(row) {
      if (!row.tags?.length) {
        return h('span', '-')
      }
      return h(
        'div',
        { style: 'display: flex; flex-wrap: wrap; gap: 6px;' },
        row.tags.map((item) =>
          h(NTag, { size: 'small', type: 'info', bordered: false }, { default: () => item.name })
        )
      )
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
      return h(NTag, { type: 'warning' }, { default: () => row.click_count || 0 })
    },
  },
  {
    title: '排序',
    key: 'order',
    width: 100,
    render(row) {
      return h('span', row.order ?? '未设置')
    },
  },
  {
    title: '上架状态',
    key: 'status',
    width: 100,
    render(row) {
      return withDirectives(
        h(NSwitch, {
          size: 'small',
          rubberBand: false,
          value: !!row.status,
          loading: statusUpdatingIds.value.includes(row.id),
          onUpdateValue: (value) => handleStatusSwitch(row, value),
        }),
        [[vPermission, 'post/api/v1/product/update']]
      )
    },
  },

  {
    title: '封面',
    key: 'cover_image_url',
    width: 100,
    render(row) {
      return h(NImage, {
        width: 56,
        src: row.cover_image_url,
        objectFit: 'cover',
      })
    },
  },
  {
    title: '更新时间',
    key: 'updated_at',
    width: 180,
    sorter: true,
    sortOrder: sorter.value.columnKey === 'updated_at' ? sorter.value.order : false,
    customNextSortOrder,
    render(row) {
      return h('span', formatDate(row.updated_at))
    },
  },
  {
    title: '操作',
    key: 'actions',
    align: 'center',
    width: 120,
    fixed: 'right',
    render(row) {
      return h('div', { style: actionCellStyle }, [
        withDirectives(
          h(
            NButton,
            {
              size: 'tiny',
              quaternary: true,
              type: 'info',
              onClick: () => openEditModal(row),
            },
            {
              default: () => '编辑',
            }
          ),
          [[vPermission, 'post/api/v1/product/update']]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete([row.id]),
          },
          {
            trigger: () =>
              withDirectives(
                h(
                  NButton,
                  {
                    size: 'tiny',
                    quaternary: true,
                    type: 'error',
                  },
                  {
                    default: () => '删除',
                  }
                ),
                [[vPermission, 'delete/api/v1/product/delete']]
              ),
            default: () => h('div', {}, '确定删除该好物吗?'),
          }
        ),
      ])
    },
  },
])

onMounted(async () => {
  await Promise.all([loadCategories(), loadBrands(), loadTags()])
  $table.value?.handleSearch()
})

async function loadCategories() {
  const res = await api.getCategoryList({ page: 1, page_size: 999 })
  categories.value = res.data || []
}

async function loadBrands() {
  const res = await api.getBrandList({ page: 1, page_size: 999 })
  brands.value = res.data || []
}

async function loadTags() {
  const res = await api.getTagList({ page: 1, page_size: 999 })
  tags.value = res.data || []
}

function resetModalForm() {
  modalForm.value = initForm()
  modalForm.value.category_id = categoryOptions.value[0]?.value ?? null
  syncModalBrand()
}

function syncModalBrand() {
  const options = modalBrandOptions.value
  if (!options.some((item) => item.value === modalForm.value.brand_id)) {
    modalForm.value.brand_id = options[0]?.value ?? null
  }
}

function openAddModal() {
  modalAction.value = 'add'
  resetModalForm()
  modalVisible.value = true
}

function openEditModal(row) {
  const videoItemFiles = (row.video_items || [])
    .map((item) => createVideoResourceFileFromItem(item))
    .filter(Boolean)
  modalAction.value = 'edit'
  modalForm.value = {
    id: row.id,
    category_id: row.category_id,
    brand_id: row.brand_id,
    tag_ids: [...(row.tag_ids || [])],
    name: row.name,
    product_code_custom: row.product_code_custom || '',
    product_code: row.product_code || '',
    desc: row.desc || '',
    detail_description_text: JSON.stringify(row.detail_description || [], null, 2),
    cover_file_list: buildPresetUploadList(
      row.cover_image_url ? [row.cover_image_url] : [],
      'cover',
      row.cover_image_key ? [row.cover_image_key] : []
    ),
    image_file_list: buildPresetUploadList(row.image_urls || [], 'image', row.image_keys || []),
    video_file_list:
      videoItemFiles.length > 0
        ? videoItemFiles
        : buildPresetUploadList(row.video_urls || [], 'video', row.video_keys || []),
    click_count: row.click_count || 0,
    status: row.status,
    order: row.order ?? null,
  }
  syncModalBrand()
  modalVisible.value = true
}

function handleCoverFileListChange(fileList) {
  const removedFiles = findRemovedUploadFiles(modalForm.value.cover_file_list, fileList)
  modalForm.value.cover_file_list = normalizeUploadFileList(fileList, 'cover')
  deleteMediaKeys(collectTransientResourceKeys(removedFiles))
}

function handleImageFileListChange(fileList) {
  const removedFiles = findRemovedUploadFiles(modalForm.value.image_file_list, fileList)
  modalForm.value.image_file_list = normalizeUploadFileList(fileList, 'image')
  deleteMediaKeys(collectTransientResourceKeys(removedFiles))
}

function handleVideoFileListChange(fileList) {
  const removedFiles = findRemovedUploadFiles(modalForm.value.video_file_list, fileList)
  modalForm.value.video_file_list = normalizeUploadFileList(fileList, 'video')
  deleteMediaKeys(collectTransientResourceKeys(removedFiles))
}

function handleCategoryFilterChange() {
  if (!queryBrandOptions.value.some((item) => item.value === queryItems.value.brand_id)) {
    queryItems.value.brand_id = null
  }
}

function handleModalCategoryChange() {
  syncModalBrand()
}

function buildProductPayload() {
  let detailDescription = []

  try {
    detailDescription = JSON.parse(modalForm.value.detail_description_text || '[]')
  } catch {
    throw new Error('detail_description 必须是合法 JSON')
  }

  if (!Array.isArray(detailDescription)) {
    throw new Error('detail_description 需要使用 JSON 数组结构')
  }

  const coverKeys = buildUploadKeys(modalForm.value.cover_file_list)
  if (!coverKeys.length) {
    throw new Error('请上传封面图')
  }

  return {
    category_id: modalForm.value.category_id,
    brand_id: modalForm.value.brand_id,
    tag_ids: [...new Set(modalForm.value.tag_ids || [])],
    name: modalForm.value.name.trim(),
    product_code_custom: String(modalForm.value.product_code_custom || '').trim(),
    desc: modalForm.value.desc.trim(),
    detail_description: detailDescription,
    cover_image_key: coverKeys[0],
    image_keys: buildUploadKeys(modalForm.value.image_file_list),
    video_keys: buildUploadKeys(modalForm.value.video_file_list),
    video_items: buildVideoItems(modalForm.value.video_file_list),
    click_count: Number(modalForm.value.click_count || 0),
    status: !!modalForm.value.status,
    order: modalForm.value.order ?? null,
  }
}

async function handleSave() {
  modalFormRef.value?.validate(async (err) => {
    if (err) return

    try {
      const payload = buildProductPayload()
      modalLoading.value = true
      if (modalAction.value === 'edit') {
        await api.updateProduct({ id: modalForm.value.id, ...payload })
        $message.success(
          payload.video_items?.some((item) => item.type === 'resource')
            ? '好物编辑成功，视频处理中'
            : '好物编辑成功'
        )
      } else {
        await api.createProduct(payload)
        $message.success(
          payload.video_items?.some((item) => item.type === 'resource')
            ? '好物新增成功，视频处理中'
            : '好物新增成功'
        )
      }
      modalForm.value.cover_file_list = markUploadFilesPersisted(modalForm.value.cover_file_list)
      modalForm.value.image_file_list = markUploadFilesPersisted(modalForm.value.image_file_list)
      modalForm.value.video_file_list = markUploadFilesPersisted(modalForm.value.video_file_list)
      modalVisible.value = false
      modalLoading.value = false
      $table.value?.handleSearch()
    } catch (error) {
      modalLoading.value = false
      $message.error(error.message || '好物保存失败')
    }
  })
}

async function handleDelete(payload) {
  const normalizedPayload = Array.isArray(payload) ? { scope: 'selected', ids: payload } : payload
  if (normalizedPayload.scope === 'selected' && !(normalizedPayload.ids || []).length) return
  const response = await api.deleteProduct(normalizedPayload)
  $message.success(`成功删除 ${response.data?.deleted ?? 0} 个好物`)
  batchDeleteModalVisible.value = false
  clearSelection()
  $table.value?.handleSearch()
}

function clearSelection() {
  checkedRowKeys.value = []
}

function openBatchDeleteModal() {
  batchDeleteModalVisible.value = true
}

function openBatchExportModal() {
  batchExportModalVisible.value = true
}

function handleBatchDelete(scope) {
  handleDelete({
    scope,
    ids: scope === 'selected' ? [...checkedRowKeys.value] : [],
    filters: scope === 'filtered' ? { ...queryItems.value } : {},
  })
}

async function handleBatchExport(scope) {
  exportLoading.value = true
  try {
    await api.exportProduct({
      scope,
      ids: scope === 'selected' ? [...checkedRowKeys.value] : [],
      filters: scope === 'filtered' ? { ...queryItems.value } : {},
    })
    $message.success('好物导出成功')
    batchExportModalVisible.value = false
  } finally {
    exportLoading.value = false
  }
}

function handleStatusSwitch(row, value) {
  if (value === !!row.status) return

  const actionText = value ? '上架' : '下架'
  $dialog.confirm({
    title: '确认状态变更',
    content: `确定要${actionText}该好物吗？`,
    confirm: async () => {
      statusUpdatingIds.value = [...statusUpdatingIds.value, row.id]
      try {
        await toggleStatus(row, value)
      } finally {
        statusUpdatingIds.value = statusUpdatingIds.value.filter((id) => id !== row.id)
      }
    },
  })
}

async function toggleStatus(row, nextValue) {
  await api.updateProduct({
    id: row.id,
    category_id: row.category_id,
    brand_id: row.brand_id,
    tag_ids: row.tag_ids || [],
    name: row.name,
    product_code_custom: row.product_code_custom || '',
    desc: row.desc || '',
    detail_description: row.detail_description || [],
    cover_image_key: row.cover_image_key || '',
    image_keys: row.image_keys || [],
    video_keys: row.video_keys || [],
    video_items:
      row.video_items?.length > 0
        ? row.video_items.map((item) => ({ type: item.type, value: item.value }))
        : (row.video_keys || []).map((item) => ({ type: 'key', value: item })),
    click_count: row.click_count || 0,
    status: nextValue,
    order: row.order ?? null,
  })
  $message.success(nextValue ? '好物已上架' : '好物已下架')
  $table.value?.handleSearch()
}

function goToProductImport() {
  router.push('/batch/product-import')
}

watch(modalVisible, (visible, wasVisible) => {
  if (visible || !wasVisible) return
  deleteMediaKeys([
    ...collectTransientResourceKeys(modalForm.value.cover_file_list),
    ...collectTransientResourceKeys(modalForm.value.image_file_list),
    ...collectTransientResourceKeys(modalForm.value.video_file_list),
  ])
})

onBeforeUnmount(() => {
  deleteMediaKeys([
    ...collectTransientResourceKeys(modalForm.value.cover_file_list),
    ...collectTransientResourceKeys(modalForm.value.image_file_list),
    ...collectTransientResourceKeys(modalForm.value.video_file_list),
  ])
})
</script>

<template>
  <CommonPage show-footer title="好物列表">
    <template #action>
      <NButton
        v-permission="'get/api/v1/product/import/tasks'"
        type="default"
        @click="goToProductImport"
      >
        <TheIcon icon="material-symbols:upload-file-outline" :size="18" class="mr-5" />去批量导入
      </NButton>
      <NButton
        v-permission="'post/api/v1/product/export'"
        type="default"
        :loading="exportLoading"
        @click="openBatchExportModal"
      >
        <TheIcon icon="mdi:file-export-outline" :size="18" class="mr-5" />批量导出
      </NButton>
      <NButton
        v-permission="'delete/api/v1/product/delete'"
        type="error"
        secondary
        @click="openBatchDeleteModal"
      >
        <TheIcon icon="material-symbols:delete-outline" :size="18" class="mr-5" />批量删除
      </NButton>
      <NButton v-permission="'post/api/v1/product/create'" type="primary" @click="openAddModal">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建好物
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:sorter="sorter"
      v-model:checked-row-keys="checkedRowKeys"
      :columns="columns"
      :get-data="getProductTableData"
      :scroll-x="1560"
      @on-data-change="clearSelection"
    >
      <template #queryBar>
        <QueryBarItem label="名称" :label-width="40">
          <NInput
            v-model:value="queryItems.keyword"
            clearable
            placeholder="搜索好物名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="分类" :label-width="40">
          <NSelect
            v-model:value="queryItems.category_id"
            clearable
            :options="categoryOptions"
            placeholder="请选择分类"
            @update:value="handleCategoryFilterChange"
          />
        </QueryBarItem>
        <QueryBarItem label="品牌" :label-width="40">
          <NSelect
            v-model:value="queryItems.brand_id"
            clearable
            :options="queryBrandOptions"
            placeholder="请选择品牌"
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

    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="90"
        :model="modalForm"
        :rules="rules"
      >
        <NTabs type="line" animated>
          <NTabPane name="basic" tab="基础信息">
            <NFormItem label="好物名称" path="name">
              <NInput v-model:value="modalForm.name" clearable placeholder="请输入好物名称" />
            </NFormItem>
            <NFormItem label="好物识别码" path="product_code_custom">
              <NInput
                v-model:value="modalForm.product_code_custom"
                clearable
                placeholder="请输入自定义字符串，例如 SKU-666"
              />
            </NFormItem>
            <NFormItem label="所属分类" path="category_id">
              <NSelect
                v-model:value="modalForm.category_id"
                :options="categoryOptions"
                placeholder="请选择所属分类"
                @update:value="handleModalCategoryChange"
              />
            </NFormItem>
            <NFormItem label="所属品牌" path="brand_id">
              <NSelect
                v-model:value="modalForm.brand_id"
                :options="modalBrandOptions"
                placeholder="请选择所属品牌"
              />
            </NFormItem>
            <NFormItem label="关联标签" path="tag_ids">
              <NSelect
                v-model:value="modalForm.tag_ids"
                clearable
                filterable
                multiple
                :options="tagOptions"
                placeholder="请选择标签"
              />
            </NFormItem>
            <NFormItem label="好物简介" path="desc">
              <NInput
                v-model:value="modalForm.desc"
                type="textarea"
                :rows="3"
                placeholder="请输入好物简介"
              />
            </NFormItem>
            <NFormItem label="封面图" path="cover_file_list">
              <NUpload
                v-model:file-list="modalForm.cover_file_list"
                accept="image/*"
                :custom-request="uploadCoverFile"
                list-type="image-card"
                :max="1"
                @update:file-list="handleCoverFileListChange"
              >
                <NIcon v-if="modalForm.cover_file_list.length < 1" size="40">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
                    <path
                      d="M368.5 240H272v-96.5c0-8.8-7.2-16-16-16s-16 7.2-16 16V240h-96.5c-8.8 0-16 7.2-16 16 0 4.4 1.8 8.4 4.7 11.3 2.9 2.9 6.9 4.7 11.3 4.7H240v96.5c0 4.4 1.8 8.4 4.7 11.3 2.9 2.9 6.9 4.7 11.3 4.7 8.8 0 16-7.2 16-16V272h96.5c8.8 0 16-7.2 16-16s-7.2-16-16-16z"
                    />
                  </svg>
                </NIcon>
              </NUpload>
            </NFormItem>
            <NFormItem label="图片列表" path="image_file_list">
              <NUpload
                v-model:file-list="modalForm.image_file_list"
                accept="image/*"
                :custom-request="uploadImageFile"
                list-type="image-card"
                multiple
                @update:file-list="handleImageFileListChange"
              >
                <NIcon size="40">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
                    <path
                      d="M368.5 240H272v-96.5c0-8.8-7.2-16-16-16s-16 7.2-16 16V240h-96.5c-8.8 0-16 7.2-16 16 0 4.4 1.8 8.4 4.7 11.3 2.9 2.9 6.9 4.7 11.3 4.7H240v96.5c0 4.4 1.8 8.4 4.7 11.3 2.9 2.9 6.9 4.7 11.3 4.7 8.8 0 16-7.2 16-16V272h96.5c8.8 0 16-7.2 16-16s-7.2-16-16-16z"
                    />
                  </svg>
                </NIcon>
              </NUpload>
            </NFormItem>
            <NFormItem label="视频列表" path="video_file_list">
              <NUpload
                v-model:file-list="modalForm.video_file_list"
                accept="video/*"
                :custom-request="uploadVideoFile"
                multiple
                @update:file-list="handleVideoFileListChange"
              >
                <NButton secondary>上传视频</NButton>
              </NUpload>
            </NFormItem>
            <NFormItem label="点击量" path="click_count">
              <NInputNumber v-model:value="modalForm.click_count" :min="0" style="width: 100%" />
            </NFormItem>
            <NFormItem label="排序" path="order">
              <NInputNumber
                v-model:value="modalForm.order"
                clearable
                :min="1"
                placeholder="从 1 开始，留空表示未设置"
                style="width: 100%"
              />
            </NFormItem>
            <NFormItem label="上架状态" path="status">
              <NSwitch v-model:value="modalForm.status" />
            </NFormItem>
          </NTabPane>

          <NTabPane name="detail" tab="结构化详情">
            <NFormItem label="detail JSON" path="detail_description_text">
              <NInput
                v-model:value="modalForm.detail_description_text"
                type="textarea"
                :rows="10"
                placeholder="请输入 detail_description JSON 数组"
              />
            </NFormItem>
          </NTabPane>
        </NTabs>
      </NForm>
    </CrudModal>
    <BatchDeleteModal
      v-model:show="batchDeleteModalVisible"
      title="批量删除好物"
      :checked-count="checkedRowKeys.length"
      :has-active-filters="hasActiveFilters"
      @confirm="handleBatchDelete"
    />
    <BatchExportModal
      v-model:show="batchExportModalVisible"
      title="批量导出好物"
      :checked-count="checkedRowKeys.length"
      :has-active-filters="hasActiveFilters"
      :loading="exportLoading"
      @confirm="handleBatchExport"
    />
  </CommonPage>
</template>
