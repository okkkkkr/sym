<script setup>
import { computed, h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NModal,
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

import { formatDate, getToken, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

defineOptions({ name: '品牌管理' })

const $table = ref(null)
const fileInputRef = ref(null)
const queryItems = ref({})
const sorter = ref({ columnKey: 'updated_at', order: 'descend' })
const checkedRowKeys = ref([])
const batchDeleteModalVisible = ref(false)
const batchExportModalVisible = ref(false)
const vPermission = resolveDirective('permission')
const categoryOptions = ref([])
const statusUpdatingIds = ref([])
const importLoading = ref(false)
const exportLoading = ref(false)
const inheritModalVisible = ref(false)
const inheritSubmitting = ref(false)
const inheritTargetOptions = ref([])
const inheritForm = ref({
  source_id: null,
  source_name: '',
  target_id: null,
})
const relationModalVisible = ref(false)
const relationModalTitle = ref('关联好物')
const relationModalFilters = ref({})
const actionCellStyle = 'display: flex; justify-content: center; align-items: center; gap: 8px; flex-wrap: nowrap; white-space: nowrap;'

const initForm = {
  category_ids: [],
  name: '',
  desc: '',
  search_count: 0,
  order: 0,
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
  name: '品牌',
  initForm,
  doCreate: api.createBrand,
  doUpdate: api.updateBrand,
  doDelete: api.deleteBrand,
  refresh: () => $table.value?.handleSearch(),
})

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

function getBrandTableData(params = {}) {
  const { is_active, ...rest } = params
  const normalizedStatus = normalizeBooleanFilter(is_active)
  return api.getBrandList({
    ...rest,
    ...(normalizedStatus === undefined ? {} : { is_active: normalizedStatus }),
  })
}

function customNextSortOrder(order) {
  if (!order) return 'descend'
  if (order === 'descend') return 'ascend'
  return false
}

const rules = {
  name: {
    required: true,
    message: '请输入品牌名称',
    trigger: ['input', 'blur'],
  },
}

async function loadCategories() {
  const { data } = await api.getCategoryList({ page: 1, page_size: 999, is_active: true })
  categoryOptions.value = data.map((item) => ({ label: item.name, value: item.id }))
  if (categoryOptions.value.length > 0) {
    initForm.category_ids = [categoryOptions.value[0].value]
  }
  if ((!modalForm.value.category_ids || modalForm.value.category_ids.length === 0) && categoryOptions.value.length > 0) {
    modalForm.value.category_ids = [categoryOptions.value[0].value]
  }
}

onMounted(async () => {
  await loadCategories()
  $table.value?.handleSearch()
})

function openAddModal() {
  handleAdd()
  if ((!modalForm.value.category_ids || modalForm.value.category_ids.length === 0) && categoryOptions.value.length > 0) {
    modalForm.value.category_ids = [categoryOptions.value[0].value]
  }
}

function handleBrandSave() {
  if ((!modalForm.value.category_ids || modalForm.value.category_ids.length === 0) && categoryOptions.value.length > 0) {
    modalForm.value.category_ids = [categoryOptions.value[0].value]
  }
  if (!modalForm.value.category_ids?.length) {
    $message.error('请选择所属分类')
    return
  }
  handleSave()
}

function openProductRelationModal(row) {
  relationModalTitle.value = `${row.name} 关联好物`
  relationModalFilters.value = { brand_id: row.id }
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
    title: '品牌名称',
    key: 'name',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '所属分类',
    key: 'categories',
    align: 'center',
    render(row) {
      const categoryNames = (row.categories || []).map((item) => item.name).filter(Boolean)
      if (!categoryNames.length) {
        return h('span', '-')
      }
      return h(
        'div',
        { style: 'display: flex; flex-direction: column; align-items: center; gap: 4px;' },
        categoryNames.map((name) => h('span', name))
      )
    },
  },
  {
    title: '品牌描述',
    key: 'desc',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '关联好物数',
    key: 'product_count',
    align: 'center',
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
    title: '启用状态',
    key: 'is_active',
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
        [[vPermission, 'post/api/v1/brand/update']]
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
    width: 200,
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
              onClick: () => openInheritModal(row),
            },
            {
              default: () => '内容继承',
            }
          ),
          [[vPermission, 'post/api/v1/brand/inherit']]
        ),
        withDirectives(
          h(
            NButton,
            {
              size: 'tiny',
              quaternary: true,
              type: 'info',
              onClick: () => {
                handleEdit({ ...row, category_ids: [...(row.category_ids || [])] })
              },
            },
            {
              default: () => '编辑',
            }
          ),
          [[vPermission, 'post/api/v1/brand/update']]
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
                [[vPermission, 'delete/api/v1/brand/delete']]
              ),
            default: () => h('div', {}, '确定删除该品牌吗?'),
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
    content: `确定要${actionText}该品牌吗？`,
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
    category_ids: [...(row.category_ids || [])],
    is_active: nextValue,
  }
  await api.updateBrand(payload)
  $message.success(payload.is_active ? '品牌已启用' : '品牌已停用')
  $table.value?.handleSearch()
}

async function downloadTemplate() {
  const response = await fetch(`${import.meta.env.VITE_BASE_API}/brand/template`, {
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
  link.download = 'brand-import-template.xlsx'
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
    const res = await api.importBrands(formData)
    $message.success(`导入成功，本次新增 ${res.data?.created ?? 0} 条品牌`)
    $table.value?.handleSearch()
  } finally {
    importLoading.value = false
    event.target.value = ''
  }
}

async function openInheritModal(row) {
  const { data } = await api.getBrandList({ page: 1, page_size: 999 })
  inheritTargetOptions.value = (data || [])
    .filter((item) => item.id !== row.id)
    .map((item) => ({ label: item.name, value: item.id }))
  inheritForm.value = {
    source_id: row.id,
    source_name: row.name,
    target_id: null,
  }
  inheritModalVisible.value = true
}

async function submitInherit() {
  if (!inheritForm.value.target_id) {
    $message.error('请选择目标品牌')
    return
  }

  $dialog.confirm({
    title: '确认内容继承',
    content: `确定将 ${inheritForm.value.source_name} 的内容转移给目标品牌吗？该操作为转移不是复制，提交后源品牌将不再保留已转移的好物。`,
    positiveText: '确认继承',
    negativeText: '取消',
    onPositiveClick: async () => {
      inheritSubmitting.value = true
      try {
        const res = await api.inheritBrandContent({
          source_id: inheritForm.value.source_id,
          target_id: inheritForm.value.target_id,
        })
        const result = res.data || {}
        $message.success(`内容继承完成，已转移 ${result.transferred_product_count ?? 0} 个好物`)
        inheritModalVisible.value = false
        $table.value?.handleSearch()
      } finally {
        inheritSubmitting.value = false
      }
    },
  })
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
      successMessage: (response) => `成功删除 ${response.data?.deleted ?? 0} 个品牌`,
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
    await api.exportBrand({
      scope,
      ids: scope === 'selected' ? [...checkedRowKeys.value] : [],
      filters: scope === 'filtered' ? { ...queryItems.value } : {},
    })
    $message.success('品牌导出成功')
    batchExportModalVisible.value = false
  } finally {
    exportLoading.value = false
  }
}
</script>

<template>
  <CommonPage show-footer title="品牌列表">
    <template #action>
      <input ref="fileInputRef" type="file" accept=".xlsx" style="display: none" @change="handleFileChange" />
      <NButton type="default" :loading="importLoading" @click="downloadTemplate">
        <TheIcon icon="mdi:download-box-outline" :size="18" class="mr-5" />下载导入模板
      </NButton>
      <NButton v-permission="'post/api/v1/brand/import'" type="default" :loading="importLoading" @click="triggerImport">
        <TheIcon icon="material-symbols:upload-file-outline" :size="18" class="mr-5" />批量导入
      </NButton>
      <NButton v-permission="'post/api/v1/brand/export'" type="default" :loading="exportLoading" @click="openBatchExportModal">
        <TheIcon icon="mdi:file-export-outline" :size="18" class="mr-5" />批量导出
      </NButton>
      <NButton v-permission="'delete/api/v1/brand/delete'" type="error" secondary :loading="modalLoading" @click="openBatchDeleteModal">
        <TheIcon icon="material-symbols:delete-outline" :size="18" class="mr-5" />批量删除
      </NButton>
      <NButton v-permission="'post/api/v1/brand/create'" type="primary" @click="openAddModal">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建品牌
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:sorter="sorter"
      v-model:checked-row-keys="checkedRowKeys"
      :columns="columns"
      :get-data="getBrandTableData"
      :scroll-x="1100"
      @on-data-change="clearSelection"
    >
      <template #queryBar>
        <QueryBarItem label="品牌名" :label-width="50">
          <NInput
            v-model:value="queryItems.name"
            clearable
            type="text"
            placeholder="请输入品牌名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="分类" :label-width="40">
          <NSelect
            v-model:value="queryItems.category_id"
            clearable
            :options="categoryOptions"
            placeholder="请选择分类"
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
      @save="handleBrandSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="90"
        :model="modalForm"
        :rules="rules"
      >
        <NFormItem label="所属分类">
          <NSelect
            v-model:value="modalForm.category_ids"
            multiple
            :options="categoryOptions"
            placeholder="请选择所属分类"
          />
        </NFormItem>
        <NFormItem label="品牌名称" path="name">
          <NInput v-model:value="modalForm.name" clearable placeholder="请输入品牌名称" />
        </NFormItem>
        <NFormItem label="品牌描述" path="desc">
          <NInput v-model:value="modalForm.desc" clearable placeholder="请输入品牌描述" />
        </NFormItem>
        <NFormItem label="检索次数" path="search_count">
          <NInputNumber v-model:value="modalForm.search_count" clearable :min="0" style="width: 100%" />
        </NFormItem>
        <NFormItem label="排序" path="order">
          <NInputNumber v-model:value="modalForm.order" clearable :min="0" style="width: 100%" />
        </NFormItem>
        <NFormItem label="启用状态" path="is_active">
          <NSwitch v-model:value="modalForm.is_active" />
        </NFormItem>
      </NForm>
    </CrudModal>

    <NModal
      v-model:show="inheritModalVisible"
      preset="card"
      title="品牌内容继承"
      style="width: 520px"
      :mask-closable="false"
    >
      <NForm label-placement="left" label-align="left" :label-width="92" :model="inheritForm">
        <NFormItem label="源品牌">
          <NInput :value="inheritForm.source_name" disabled />
        </NFormItem>
        <NFormItem label="目标品牌">
          <NSelect
            v-model:value="inheritForm.target_id"
            :options="inheritTargetOptions"
            filterable
            clearable
            placeholder="请选择需要继承内容的目标品牌"
          />
        </NFormItem>
      </NForm>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 12px">
          <NButton @click="inheritModalVisible = false">取消</NButton>
          <NButton
            v-permission="'post/api/v1/brand/inherit'"
            type="primary"
            :loading="inheritSubmitting"
            @click="submitInherit"
          >
            确认继承
          </NButton>
        </div>
      </template>
    </NModal>

    <ProductRelationModal
      v-model:show="relationModalVisible"
      :title="relationModalTitle"
      :filters="relationModalFilters"
    />
    <BatchDeleteModal
      v-model:show="batchDeleteModalVisible"
      title="批量删除品牌"
      :checked-count="checkedRowKeys.length"
      :has-active-filters="hasActiveFilters"
      :loading="modalLoading"
      @confirm="handleBatchDelete"
    />
    <BatchExportModal
      v-model:show="batchExportModalVisible"
      title="批量导出品牌"
      :checked-count="checkedRowKeys.length"
      :has-active-filters="hasActiveFilters"
      :loading="exportLoading"
      @confirm="handleBatchExport"
    />
  </CommonPage>
</template>