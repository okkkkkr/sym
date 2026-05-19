<script setup>
import { computed, h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NPopconfirm,
  NSelect,
  NSwitch,
  NTag,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import ProductRelationModal from '@/components/product/ProductRelationModal.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import BatchDeleteModal from '@/components/table/BatchDeleteModal.vue'
import BatchExportModal from '@/components/table/BatchExportModal.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { formatDate, getToken } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

defineOptions({ name: '标签管理' })

const $table = ref(null)
const fileInputRef = ref(null)
const queryItems = ref({})
const sorter = ref({ columnKey: 'updated_at', order: 'descend' })
const checkedRowKeys = ref([])
const batchDeleteModalVisible = ref(false)
const batchExportModalVisible = ref(false)
const vPermission = resolveDirective('permission')
const statusUpdatingIds = ref([])
const importLoading = ref(false)
const exportLoading = ref(false)
const relationModalVisible = ref(false)
const relationModalTitle = ref('关联好物')
const relationModalFilters = ref({})
const actionCellStyle = 'display: flex; justify-content: center; align-items: center; gap: 8px; flex-wrap: nowrap; white-space: nowrap;'

const initForm = {
  name: '',
  remark: '',
  search_count: 0,
  sort: 0,
  is_active: true,
}

const {
  modalVisible,
  modalTitle,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = useCRUD({
  name: '标签',
  initForm,
  doCreate: api.createTag,
  doUpdate: api.updateTag,
  doDelete: api.deleteTag,
  refresh: () => $table.value?.handleSearch(),
})

const statusOptions = [
  { label: '全部状态', value: 'all' },
  { label: '启用', value: 'true' },
  { label: '停用', value: 'false' },
]

const rules = {
  name: {
    required: true,
    message: '请输入标签名称',
    trigger: ['input', 'blur'],
  },
}

function normalizeBooleanFilter(value) {
  if (value === 'true') return true
  if (value === 'false') return false
  return undefined
}

function getTagTableData(params = {}) {
  const { is_active, ...rest } = params
  const normalizedStatus = normalizeBooleanFilter(is_active)
  return api.getTagList({
    ...rest,
    ...(normalizedStatus === undefined ? {} : { is_active: normalizedStatus }),
  })
}

function customNextSortOrder(order) {
  if (!order) return 'descend'
  if (order === 'descend') return 'ascend'
  return false
}

onMounted(() => {
  $table.value?.handleSearch()
})

function openAddModal() {
  handleAdd()
}

function openEditModal(row) {
  handleEdit(row)
}

function handleTagSave() {
  handleSave()
}

function openProductRelationModal(row) {
  relationModalTitle.value = `${row.name} 关联好物`
  relationModalFilters.value = { tag_id: row.id }
  relationModalVisible.value = true
}

const hasCheckedRows = computed(() => checkedRowKeys.value.length > 0)
const hasActiveFilters = computed(() => Object.values(queryItems.value).some(isEffectiveFilterValue))

function isEffectiveFilterValue(value) {
  if (Array.isArray(value)) return value.length > 0
  return value !== null && value !== undefined && value !== '' && value !== 'all'
}

const columns = computed(() => [
  {
    type: 'selection',
    width: 48,
    align: 'center',
    fixed: 'left',
  },
  {
    title: '标签名称',
    key: 'name',
    align: 'center',
    ellipsis: { tooltip: true },
    sorter: true,
    sortOrder: sorter.value.columnKey === 'name' ? sorter.value.order : false,
    customNextSortOrder,
  },
  {
    title: '备注',
    key: 'remark',
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h('span', row.remark || '-')
    },
  },
  {
    title: '检索次数',
    key: 'search_count',
    align: 'center',
    sorter: true,
    sortOrder: sorter.value.columnKey === 'search_count' ? sorter.value.order : false,
    customNextSortOrder,
    render(row) {
      return h(NTag, { type: 'info' }, { default: () => String(row.search_count ?? 0) })
    },
  },
  {
    title: '排序',
    key: 'sort',
    align: 'center',
    sorter: true,
    sortOrder: sorter.value.columnKey === 'sort' ? sorter.value.order : false,
    customNextSortOrder,
  },
  {
    title: '关联好物数',
    key: 'product_count',
    align: 'center',
    sorter: true,
    sortOrder: sorter.value.columnKey === 'product_count' ? sorter.value.order : false,
    customNextSortOrder,
    render(row) {
      return h(
        NTag,
        {
          type: row.product_count ? 'success' : 'default',
          style: 'cursor: pointer;',
          onClick: () => openProductRelationModal(row),
        },
        { default: () => String(row.product_count ?? 0) }
      )
    },
  },
  {
    title: '启用状态',
    key: 'is_active',
    width: 100,
    align: 'center',
    render(row) {
      return withDirectives(
        h(NSwitch, {
          size: 'small',
          rubberBand: false,
          value: !!row.is_active,
          loading: statusUpdatingIds.value.includes(row.id),
          onUpdateValue: (value) => handleStatusSwitch(row, value),
        }),
        [[vPermission, 'post/api/v1/tag/toggle']]
      )
    },
  },
  {
    title: '更新时间',
    key: 'updated_at',
    width: 180,
    align: 'center',
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
    width: 120,
    align: 'center',
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
          [[vPermission, 'post/api/v1/tag/update']]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ ids: [row.id] }),
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
                [[vPermission, 'delete/api/v1/tag/delete']]
              ),
            default: () => h('div', {}, '确定删除该标签吗?'),
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
    content: `确定要${actionText}该标签吗？`,
    confirm: async () => {
      statusUpdatingIds.value = [...statusUpdatingIds.value, row.id]
      try {
        await api.toggleTag({ id: row.id, is_active: value })
        $message.success(value ? '标签已启用' : '标签已停用')
        $table.value?.handleSearch()
      } finally {
        statusUpdatingIds.value = statusUpdatingIds.value.filter((id) => id !== row.id)
      }
    },
  })
}

async function downloadTemplate() {
  const response = await fetch(`${import.meta.env.VITE_BASE_API}/tag/template`, {
    headers: {
      token: getToken() || '',
    },
  })

  if (!response.ok) {
    $message.error('模板下载失败')
    return
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'tag-import-template.xlsx'
  link.click()
  window.URL.revokeObjectURL(url)
}

function triggerImport() {
  fileInputRef.value?.click()
}

async function handleFileChange(event) {
  const file = event.target.files?.[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)
  importLoading.value = true
  try {
    const res = await api.importTags(formData)
    $message.success(`导入成功，本次新增 ${res.data?.created ?? 0} 条标签`)
    $table.value?.handleSearch()
  } finally {
    importLoading.value = false
    event.target.value = ''
  }
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
  handleDelete(
    {
      scope,
      ids: scope === 'selected' ? [...checkedRowKeys.value] : [],
      filters: scope === 'filtered' ? { ...queryItems.value } : {},
    },
    {
      successMessage: (response) => `成功删除 ${response.data?.deleted ?? 0} 个标签`,
      onSuccess: () => {
        batchDeleteModalVisible.value = false
        clearSelection()
      },
    }
  )
}

async function handleBatchExport(scope) {
  exportLoading.value = true
  try {
    await api.exportTag({
      scope,
      ids: scope === 'selected' ? [...checkedRowKeys.value] : [],
      filters: scope === 'filtered' ? { ...queryItems.value } : {},
    })
    $message.success('标签导出成功')
    batchExportModalVisible.value = false
  } finally {
    exportLoading.value = false
  }
}
</script>

<template>
  <CommonPage show-footer title="标签列表">
    <template #action>
      <input ref="fileInputRef" type="file" accept=".xlsx" style="display: none" @change="handleFileChange" />
      <NButton type="default" :loading="importLoading" @click="downloadTemplate">
        <TheIcon icon="mdi:download-box-outline" :size="18" class="mr-5" />下载导入模板
      </NButton>
      <NButton v-permission="'post/api/v1/tag/import'" type="default" :loading="importLoading" @click="triggerImport">
        <TheIcon icon="material-symbols:upload-file-outline" :size="18" class="mr-5" />批量导入
      </NButton>
      <NButton v-permission="'post/api/v1/tag/export'" type="default" :loading="exportLoading" @click="openBatchExportModal">
        <TheIcon icon="mdi:file-export-outline" :size="18" class="mr-5" />批量导出
      </NButton>
      <NButton v-permission="'delete/api/v1/tag/delete'" type="error" secondary :loading="modalLoading" @click="openBatchDeleteModal">
        <TheIcon icon="material-symbols:delete-outline" :size="18" class="mr-5" />批量删除
      </NButton>
      <NButton v-permission="'post/api/v1/tag/create'" type="primary" @click="openAddModal">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建标签
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:sorter="sorter"
      v-model:checked-row-keys="checkedRowKeys"
      :columns="columns"
      :get-data="getTagTableData"
      :scroll-x="1200"
      @on-data-change="clearSelection"
    >
      <template #queryBar>
        <QueryBarItem label="标签名" :label-width="50">
          <NInput
            v-model:value="queryItems.name"
            clearable
            type="text"
            placeholder="请输入标签名称"
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

    <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleTagSave">
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="90"
        :model="modalForm"
        :rules="rules"
      >
        <NFormItem label="标签名称" path="name">
          <NInput v-model:value="modalForm.name" clearable placeholder="请输入标签名称" />
        </NFormItem>
        <NFormItem label="备注" path="remark">
          <NInput v-model:value="modalForm.remark" clearable placeholder="请输入备注" />
        </NFormItem>
        <NFormItem label="检索次数" path="search_count">
          <NInputNumber v-model:value="modalForm.search_count" clearable :min="0" style="width: 100%" />
        </NFormItem>
        <NFormItem label="排序" path="sort">
          <NInputNumber v-model:value="modalForm.sort" clearable :min="0" style="width: 100%" />
        </NFormItem>
        <NFormItem label="启用状态" path="is_active">
          <NSwitch v-model:value="modalForm.is_active" />
        </NFormItem>
      </NForm>
    </CrudModal>

    <ProductRelationModal
      v-model:show="relationModalVisible"
      :title="relationModalTitle"
      :filters="relationModalFilters"
    />
    <BatchDeleteModal
      v-model:show="batchDeleteModalVisible"
      title="批量删除标签"
      :checked-count="checkedRowKeys.length"
      :has-active-filters="hasActiveFilters"
      :loading="modalLoading"
      @confirm="handleBatchDelete"
    />
    <BatchExportModal
      v-model:show="batchExportModalVisible"
      title="批量导出标签"
      :checked-count="checkedRowKeys.length"
      :has-active-filters="hasActiveFilters"
      :loading="exportLoading"
      @confirm="handleBatchExport"
    />
  </CommonPage>
</template>