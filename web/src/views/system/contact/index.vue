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
  NTag,
  NUpload,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { formatDate } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import {
  PERSISTED_RESOURCE_STATE,
  TRANSIENT_RESOURCE_STATE,
  collectTransientResourceKeys,
  findRemovedUploadFiles,
  markUploadFilesPersisted,
  normalizeManagedUploadFileList,
} from '@/utils/media/resource'

defineOptions({ name: '联系方式管理' })

let qrFileSeed = 0

const $table = ref(null)
const queryItems = ref({})
const sorter = ref({ columnKey: 'updated_at', order: 'descend' })
const vPermission = resolveDirective('permission')
const statusUpdatingIds = ref([])
const uploadingQr = ref(false)
const qrFileList = ref([])
const qrObjectKey = ref('')
const actionCellStyle =
  'display: flex; justify-content: center; align-items: center; gap: 8px; flex-wrap: wrap;'

const initForm = {
  platform: '',
  display_name: '',
  contact_type: null,
  contact_value: '',
  link_url: '',
  qr_image_url: '',
  order: null,
  is_active: true,
}

const {
  modalVisible,
  modalTitle,
  modalLoading,
  handleSave: saveContact,
  modalForm,
  modalFormRef,
  handleEdit: editContact,
  handleDelete,
  handleAdd: addContact,
} = useCRUD({
  name: '联系方式',
  initForm,
  doCreate: api.createContact,
  doUpdate: api.updateContact,
  doDelete: api.deleteContact,
  refresh: () => $table.value?.handleSearch(),
})

const contactTypeOptions = [
  { label: 'social', value: 'social' },
  { label: 'messaging', value: 'messaging' },
  { label: 'email', value: 'email' },
  { label: 'phone', value: 'phone' },
]

const platformOptions = [
  { label: 'facebook', value: 'facebook' },
  { label: 'whatsapp', value: 'whatsapp' },
  { label: 'wechat', value: 'wechat' },
  { label: 'email', value: 'email' },
  { label: 'phone', value: 'phone' },
]

const contactTypeFilterOptions = [{ label: '全部类型', value: 'all' }, ...contactTypeOptions]
const statusOptions = [
  { label: '全部状态', value: 'all' },
  { label: '启用', value: 'true' },
  { label: '停用', value: 'false' },
]

function normalizeBooleanFilter(value) {
  if (value === 'true') return true
  if (value === 'false') return false
  return undefined
}

function getContactTableData(params = {}) {
  const { contact_type, is_active, ...rest } = params
  const normalizedStatus = normalizeBooleanFilter(is_active)
  return api.getContactList({
    ...rest,
    ...(contact_type && contact_type !== 'all' ? { contact_type } : {}),
    ...(normalizedStatus === undefined ? {} : { is_active: normalizedStatus }),
  })
}

function customNextSortOrder(order) {
  if (!order) return 'descend'
  if (order === 'descend') return 'ascend'
  return false
}

function getQrPreviewUrl(row) {
  return String(row?.qr_image_preview_url || '').trim()
}

function getFileNameFromUrl(url) {
  const normalized = String(url || '').trim()
  if (!normalized) return 'qr'
  try {
    const parsed = new URL(normalized)
    return parsed.pathname.split('/').filter(Boolean).pop() || 'qr'
  } catch {
    return normalized.split('/').filter(Boolean).pop() || 'qr'
  }
}

function createQrUploadFile(url, rawUrl = url) {
  if (!url) return null
  qrFileSeed += 1
  return {
    id: `qr-${qrFileSeed}`,
    name: getFileNameFromUrl(rawUrl || url),
    status: 'finished',
    url,
    thumbnailUrl: url,
    rawUrl,
    resourceState: PERSISTED_RESOURCE_STATE,
  }
}

function normalizeQrFileList(fileList = []) {
  return normalizeManagedUploadFileList(
    fileList
      .map((file) => {
        if (!file) return null
        if (file.url || file.thumbnailUrl) {
          return {
            ...file,
            url: file.url || file.thumbnailUrl,
            thumbnailUrl: file.thumbnailUrl || file.url,
            rawUrl: file.rawUrl || '',
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
    console.error('删除未保存二维码失败', error)
  }
}

function syncQrValue(fileList = []) {
  qrFileList.value = normalizeQrFileList(fileList).slice(-1)
  modalForm.value.qr_image_url = qrObjectKey.value
}

function syncQrFileList(row = null) {
  qrObjectKey.value = String(row?.qr_image_url || '').trim()
  qrFileList.value = row?.qr_image_preview_url
    ? [createQrUploadFile(row.qr_image_preview_url, row.qr_image_url)]
    : []
}

function handleAdd() {
  addContact()
  qrObjectKey.value = ''
  qrFileList.value = []
}

function handleEdit(row) {
  editContact(row)
  syncQrFileList(row)
}

async function handleQrUpload({ file, onError, onFinish, onProgress }) {
  uploadingQr.value = true
  try {
    if (!file?.file) {
      throw new Error('未找到待上传图片')
    }

    const response = await api.uploadContactQr(file.file, {
      onUploadProgress: (event) => {
        if (!event.total) return
        onProgress({ percent: Math.round((event.loaded / event.total) * 100) })
      },
    })
    const result = response.data || {}

    file.url = result.url
    file.thumbnailUrl = file.url
    file.rawUrl = result.key
    file.resourceState = TRANSIENT_RESOURCE_STATE
    qrObjectKey.value = result.key
    if (!file.name) {
      file.name = getFileNameFromUrl(file.rawUrl)
    }
    syncQrValue([file])
    onFinish()
  } catch (error) {
    syncQrValue(qrFileList.value)
    onError()
    if (!error?.code) {
      $message.error(error.message || '上传失败')
    }
  } finally {
    uploadingQr.value = false
  }
}

function handleQrFileListChange(fileList) {
  const removedFiles = findRemovedUploadFiles(qrFileList.value, fileList)
  if (!fileList.length) {
    qrObjectKey.value = ''
  }
  syncQrValue(fileList)
  deleteMediaKeys(collectTransientResourceKeys(removedFiles))
}

function handleSave() {
  if (uploadingQr.value) {
    $message.warning('二维码图片上传中，请稍后保存')
    return
  }
  modalForm.value.qr_image_url = qrObjectKey.value
  saveContact(() => {
    qrFileList.value = markUploadFilesPersisted(qrFileList.value)
  })
}

const rules = {
  platform: {
    required: true,
    message: '请选择平台',
    trigger: ['change', 'blur'],
  },
  display_name: {
    required: true,
    message: '请输入展示名称',
    trigger: ['input', 'blur'],
  },
}

onMounted(() => {
  $table.value?.handleSearch()
})

watch(modalVisible, (visible, wasVisible) => {
  if (visible || !wasVisible) return
  deleteMediaKeys(collectTransientResourceKeys(qrFileList.value))
})

onBeforeUnmount(() => {
  deleteMediaKeys(collectTransientResourceKeys(qrFileList.value))
})

const columns = computed(() => [
  {
    title: '平台',
    key: 'platform',
    width: 100,
    ellipsis: { tooltip: true },
  },
  {
    title: '展示名称',
    key: 'display_name',
    width: 200,
    ellipsis: { tooltip: true },
  },
  {
    title: '联系类型',
    key: 'contact_type',
    width: 100,
    render(row) {
      return row.contact_type
        ? h(NTag, { type: 'info' }, { default: () => row.contact_type })
        : h('span', { style: 'color: var(--n-text-color-disabled);' }, '-')
    },
  },
  {
    title: '联系内容',
    key: 'contact_value',
    width: 200,
    ellipsis: { tooltip: true },
  },
  {
    title: '二维码',
    key: 'qr_image_url',
    width: 120,
    render(row) {
      const qrImagePreviewUrl = getQrPreviewUrl(row)
      if (!qrImagePreviewUrl) {
        return h('span', { style: 'color: var(--n-text-color-disabled);' }, '-')
      }
      return h(NImage, {
        width: 56,
        src: qrImagePreviewUrl,
        objectFit: 'cover',
      })
    },
  },
  {
    title: '排序',
    key: 'order',
    width: 100,
    sorter: true,
    sortOrder: sorter.value.columnKey === 'order' ? sorter.value.order : false,
    customNextSortOrder,
    render(row) {
      return h(NTag, { type: 'default' }, { default: () => row.order ?? '未设置' })
    },
  },
  {
    title: '启用状态',
    key: 'is_active',
    width: 100,
    render(row) {
      return withDirectives(
        h(NSwitch, {
          size: 'small',
          rubberBand: false,
          value: !!row.is_active,
          loading: statusUpdatingIds.value.includes(row.id),
          onUpdateValue: (value) => handleStatusSwitch(row, value),
        }),
        [[vPermission, 'post/api/v1/contact/update']]
      )
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
              onClick: () => handleEdit(row),
            },
            {
              default: () => '编辑',
            }
          ),
          [[vPermission, 'post/api/v1/contact/update']]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ id: row.id }),
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
                [[vPermission, 'delete/api/v1/contact/delete']]
              ),
            default: () => h('div', {}, '确定删除该联系方式吗?'),
          }
        ),
      ])
    },
  },
])

function handleStatusSwitch(row, value) {
  if (value === !!row.is_active) return

  const actionText = value ? '启用' : '停用'
  $dialog.confirm({
    title: '确认状态变更',
    content: `确定要${actionText}该联系方式吗？`,
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
  const payload = {
    ...row,
    is_active: nextValue,
  }
  await api.updateContact(payload)
  $message.success(payload.is_active ? '联系方式已启用' : '联系方式已停用')
  $table.value?.handleSearch()
}
</script>

<template>
  <CommonPage show-footer title="联系方式列表">
    <template #action>
      <NButton v-permission="'post/api/v1/contact/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建联系方式
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:sorter="sorter"
      :columns="columns"
      :get-data="getContactTableData"
      :scroll-x="1320"
    >
      <template #queryBar>
        <QueryBarItem label="关键字" :label-width="50">
          <NInput
            v-model:value="queryItems.keyword"
            clearable
            type="text"
            placeholder="搜索平台、名称或联系内容"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="类型" :label-width="40">
          <NSelect
            v-model:value="queryItems.contact_type"
            clearable
            :options="contactTypeFilterOptions"
            placeholder="请选择类型"
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
        <NFormItem label="平台" path="platform">
          <NSelect
            v-model:value="modalForm.platform"
            :options="platformOptions"
            placeholder="请选择平台"
          />
        </NFormItem>
        <NFormItem label="展示名称" path="display_name">
          <NInput v-model:value="modalForm.display_name" clearable placeholder="请输入展示名称" />
        </NFormItem>
        <NFormItem label="联系类型" path="contact_type">
          <NSelect
            v-model:value="modalForm.contact_type"
            clearable
            :options="contactTypeOptions"
            placeholder="请选择联系类型"
          />
        </NFormItem>
        <NFormItem label="联系内容" path="contact_value">
          <NInput v-model:value="modalForm.contact_value" clearable placeholder="请输入联系内容" />
        </NFormItem>
        <NFormItem label="二维码图片" path="qr_image_url">
          <NUpload
            v-model:file-list="qrFileList"
            accept="image/*"
            :custom-request="handleQrUpload"
            list-type="image-card"
            :max="1"
            @update:file-list="handleQrFileListChange"
          >
            <NIcon v-if="qrFileList.length < 1" size="40">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
                <path
                  d="M368.5 240H272v-96.5c0-8.8-7.2-16-16-16s-16 7.2-16 16V240h-96.5c-8.8 0-16 7.2-16 16 0 4.4 1.8 8.4 4.7 11.3 2.9 2.9 6.9 4.7 11.3 4.7H240v96.5c0 4.4 1.8 8.4 4.7 11.3 2.9 2.9 6.9 4.7 11.3 4.7 8.8 0 16-7.2 16-16V272h96.5c8.8 0 16-7.2 16-16s-7.2-16-16-16z"
                />
              </svg>
            </NIcon>
          </NUpload>
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
        <NFormItem label="启用状态" path="is_active">
          <NSwitch v-model:value="modalForm.is_active" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
