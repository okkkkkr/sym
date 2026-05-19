<script setup>
import { computed, h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NModal,
  NDrawer,
  NDrawerContent,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NPopconfirm,
  NSelect,
  NSwitch,
  NTag,
  NTransfer,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import ProductRelationModal from '@/components/product/ProductRelationModal.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import BatchDeleteModal from '@/components/table/BatchDeleteModal.vue'
import BatchExportModal from '@/components/table/BatchExportModal.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { formatDate } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

defineOptions({ name: '分类管理' })

const $table = ref(null)
const queryItems = ref({})
const sorter = ref({ columnKey: 'updated_at', order: 'descend' })
const checkedRowKeys = ref([])
const batchDeleteModalVisible = ref(false)
const batchExportModalVisible = ref(false)
const vPermission = resolveDirective('permission')
const statusUpdatingIds = ref([])
const exportLoading = ref(false)
const hotDrawerVisible = ref(false)
const hotConfigLoading = ref(false)
const hotSaving = ref(false)
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
const hotForm = ref({
  id: null,
  category_name: '',
  hot_brand_ids: [],
  hot_tag_ids: [],
})
const hotBrandOptions = ref([])
const hotTagOptions = ref([])
const actionCellStyle = 'display: flex; justify-content: center; align-items: center; gap: 8px; flex-wrap: nowrap; white-space: nowrap;'

const initForm = {
  name: '',
  desc: '',
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
  name: '分类',
  initForm,
  doCreate: api.createCategory,
  doUpdate: api.updateCategory,
  doDelete: api.deleteCategory,
  refresh: () => $table.value?.handleSearch(),
})

onMounted(() => {
  $table.value?.handleSearch()
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

function getCategoryTableData(params = {}) {
  const { is_active, ...rest } = params
  const normalizedStatus = normalizeBooleanFilter(is_active)
  return api.getCategoryList({
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
    message: '请输入分类名称',
    trigger: ['input', 'blur'],
  },
}

function openProductRelationModal(row) {
  relationModalTitle.value = `${row.name} 关联好物`
  relationModalFilters.value = { category_id: row.id }
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
    title: '分类名称',
    key: 'name',
    width: 140,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '分类描述',
    key: 'desc',
    width: 220,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '关联好物数',
    key: 'product_count',
    width: 120,
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
    title: '排序',
    key: 'order',
    align: 'center',
    sorter: true,
    sortOrder: sorter.value.columnKey === 'order' ? sorter.value.order : false,
    customNextSortOrder,
  },
  {
    title: '启用状态',
    key: 'is_active',
    width: 90,
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
        [[vPermission, 'post/api/v1/category/update']]
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
    width: 280,
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
              onClick: () => openHotDrawer(row),
            },
            {
              default: () => '热门管理',
            }
          ),
          [[vPermission, 'post/api/v1/category/hot-config']]
        ),
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
          [[vPermission, 'post/api/v1/category/inherit']]
        ),
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
          [[vPermission, 'post/api/v1/category/update']]
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
                [[vPermission, 'delete/api/v1/category/delete']]
              ),
            default: () => h('div', {}, '确定删除该分类吗?'),
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
    content: `确定要${actionText}该分类吗？`,
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
  await api.updateCategory(payload)
  $message.success(payload.is_active ? '分类已启用' : '分类已停用')
  $table.value?.handleSearch()
}

async function openHotDrawer(row) {
  hotDrawerVisible.value = true
  hotConfigLoading.value = true
  try {
    const res = await api.getCategoryHotConfig({ id: row.id })
    const data = res.data || {}
    hotForm.value = {
      id: row.id,
      category_name: row.name,
      hot_brand_ids: data.hot_brand_ids || [],
      hot_tag_ids: data.hot_tag_ids || [],
    }
    hotBrandOptions.value = (data.brands || []).map((item) => ({ label: item.name, value: item.id }))
    hotTagOptions.value = (data.tags || []).map((item) => ({ label: item.name, value: item.id }))
  } finally {
    hotConfigLoading.value = false
  }
}

async function saveHotConfig() {
  hotSaving.value = true
  try {
    await api.updateCategoryHotConfig({
      id: hotForm.value.id,
      hot_brand_ids: hotForm.value.hot_brand_ids,
      hot_tag_ids: hotForm.value.hot_tag_ids,
    })
    $message.success('热门配置已更新')
    hotDrawerVisible.value = false
    $table.value?.handleSearch()
  } finally {
    hotSaving.value = false
  }
}

async function openInheritModal(row) {
  const { data } = await api.getCategoryList({ page: 1, page_size: 999 })
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
    $message.error('请选择目标分类')
    return
  }

  $dialog.confirm({
    title: '确认内容继承',
    content: `确定将 ${inheritForm.value.source_name} 的内容转移给目标分类吗？该操作为转移不是复制，提交后源分类将不再保留已转移的品牌归属、热门品牌、热门标签和好物。`,
    positiveText: '确认继承',
    negativeText: '取消',
    onPositiveClick: async () => {
      inheritSubmitting.value = true
      try {
        const res = await api.inheritCategoryContent({
          source_id: inheritForm.value.source_id,
          target_id: inheritForm.value.target_id,
        })
        const result = res.data || {}
        $message.success(
          `内容继承完成，已转移 ${result.transferred_product_count ?? 0} 个好物、${result.transferred_brand_count ?? 0} 个品牌归属`
        )
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
      successMessage: (response) => `成功删除 ${response.data?.deleted ?? 0} 个分类`,
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
    await api.exportCategory({
      scope,
      ids: scope === 'selected' ? [...checkedRowKeys.value] : [],
      filters: scope === 'filtered' ? { ...queryItems.value } : {},
    })
    $message.success('分类导出成功')
    batchExportModalVisible.value = false
  } finally {
    exportLoading.value = false
  }
}
</script>

<template>
  <CommonPage show-footer title="分类列表">
    <template #action>
      <NButton v-permission="'post/api/v1/category/export'" type="default" :loading="exportLoading" @click="openBatchExportModal">
        <TheIcon icon="mdi:file-export-outline" :size="18" class="mr-5" />批量导出
      </NButton>
      <NButton v-permission="'delete/api/v1/category/delete'" type="error" secondary :loading="modalLoading" @click="openBatchDeleteModal">
        <TheIcon icon="material-symbols:delete-outline" :size="18" class="mr-5" />批量删除
      </NButton>
      <NButton v-permission="'post/api/v1/category/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建分类
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:sorter="sorter"
      v-model:checked-row-keys="checkedRowKeys"
      :columns="columns"
      :get-data="getCategoryTableData"
      @on-data-change="clearSelection"
    >
      <template #queryBar>
        <QueryBarItem label="分类名" :label-width="50">
          <NInput
            v-model:value="queryItems.name"
            clearable
            type="text"
            placeholder="请输入分类名称"
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
        :label-width="80"
        :model="modalForm"
        :rules="rules"
      >
        <NFormItem label="分类名称" path="name">
          <NInput v-model:value="modalForm.name" clearable placeholder="请输入分类名称" />
        </NFormItem>
        <NFormItem label="分类描述" path="desc">
          <NInput v-model:value="modalForm.desc" clearable placeholder="请输入分类描述" />
        </NFormItem>
        <NFormItem label="排序" path="order">
          <NInputNumber v-model:value="modalForm.order" clearable :min="0" style="width: 100%" />
        </NFormItem>
        <NFormItem label="启用状态" path="is_active">
          <NSwitch v-model:value="modalForm.is_active" />
        </NFormItem>
      </NForm>
    </CrudModal>

    <NDrawer v-model:show="hotDrawerVisible" placement="right" :width="560">
      <NDrawerContent :title="`${hotForm.category_name || ''} 热门管理`" closable>
        <div v-if="hotConfigLoading" class="py-16 text-center">加载中...</div>
        <template v-else>
          <div class="mb-20">
            <div class="mb-12 text-14 font-600">热门品牌</div>
            <NTransfer
              v-model:value="hotForm.hot_brand_ids"
              source-filterable
              target-filterable
              :options="hotBrandOptions"
            />
          </div>
          <div>
            <div class="mb-12 text-14 font-600">热门标签</div>
            <NTransfer
              v-model:value="hotForm.hot_tag_ids"
              source-filterable
              target-filterable
              :options="hotTagOptions"
            />
          </div>
        </template>
        <template #footer>
          <div style="display: flex; justify-content: flex-end; gap: 12px">
            <NButton @click="hotDrawerVisible = false">取消</NButton>
            <NButton
              v-permission="'post/api/v1/category/hot-config'"
              type="primary"
              :loading="hotSaving"
              @click="saveHotConfig"
            >
              保存
            </NButton>
          </div>
        </template>
      </NDrawerContent>
    </NDrawer>

    <NModal
      v-model:show="inheritModalVisible"
      preset="card"
      title="分类内容继承"
      style="width: 520px"
      :mask-closable="false"
    >
      <NForm label-placement="left" label-align="left" :label-width="92" :model="inheritForm">
        <NFormItem label="源分类">
          <NInput :value="inheritForm.source_name" disabled />
        </NFormItem>
        <NFormItem label="目标分类">
          <NSelect
            v-model:value="inheritForm.target_id"
            :options="inheritTargetOptions"
            filterable
            clearable
            placeholder="请选择需要继承内容的目标分类"
          />
        </NFormItem>
      </NForm>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 12px">
          <NButton @click="inheritModalVisible = false">取消</NButton>
          <NButton
            v-permission="'post/api/v1/category/inherit'"
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
      title="批量删除分类"
      :checked-count="checkedRowKeys.length"
      :has-active-filters="hasActiveFilters"
      :loading="modalLoading"
      @confirm="handleBatchDelete"
    />
    <BatchExportModal
      v-model:show="batchExportModalVisible"
      title="批量导出分类"
      :checked-count="checkedRowKeys.length"
      :has-active-filters="hasActiveFilters"
      :loading="exportLoading"
      @confirm="handleBatchExport"
    />
  </CommonPage>
</template>