<script setup>
import { computed, h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NInputNumber, NPopconfirm, NSelect, NSwitch, NTag } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { formatDate } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

defineOptions({ name: '横幅管理' })

const $table = ref(null)
const queryItems = ref({})
const sorter = ref({ columnKey: 'updated_at', order: 'descend' })
const vPermission = resolveDirective('permission')
const statusUpdatingIds = ref([])
const actionCellStyle = 'display: flex; justify-content: center; align-items: center; gap: 8px; flex-wrap: wrap;'

const initForm = {
  content: '',
  note: '',
  priority: null,
  link_url: '',
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
  name: '横幅',
  initForm,
  doCreate: api.createBanner,
  doUpdate: api.updateBanner,
  doDelete: api.deleteBanner,
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

function getBannerTableData(params = {}) {
  const { keyword, note, is_active, ...rest } = params
  const normalizedStatus = normalizeBooleanFilter(is_active)
  return api.getBannerList({
    ...rest,
    ...(keyword ? { content: keyword } : {}),
    ...(note ? { note } : {}),
    ...(normalizedStatus === undefined ? {} : { is_active: normalizedStatus }),
  })
}

function customNextSortOrder(order) {
  if (!order) return 'descend'
  if (order === 'descend') return 'ascend'
  return false
}

const rules = {
  content: {
    required: true,
    message: '请输入横幅内容',
    trigger: ['input', 'blur'],
  },
}

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = computed(() => [
  {
    title: '横幅内容',
    key: 'content',
    width: 200,
    ellipsis: { tooltip: true },
  },
  {
    title: '备注',
    key: 'note',
    width: 200,
    ellipsis: { tooltip: true },
    render(row) {
      return h('span', row.note || '-')
    },
  },
  {
    title: '排序',
    key: 'priority',
    width: 100,
    sorter: true,
    sortOrder: sorter.value.columnKey === 'priority' ? sorter.value.order : false,
    customNextSortOrder,
    render(row) {
      return h(NTag, { type: 'info' }, { default: () => (row.priority ?? '未设置') })
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
      return h(NTag, { type: 'warning' }, { default: () => String(row.click_count ?? 0) })
    },
  },
  {
    title: '跳转路径',
    key: 'link_url',
    width: 200,
    ellipsis: { tooltip: true },
    render(row) {
      return h('span', row.link_url || '-')
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
        [[vPermission, 'post/api/v1/banner/update']]
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
              onClick: () => handleEdit({ ...row }),
            },
            {
              default: () => '编辑',
            }
          ),
          [[vPermission, 'post/api/v1/banner/update']]
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
                [[vPermission, 'delete/api/v1/banner/delete']]
              ),
            default: () => h('div', {}, '确定删除该横幅吗?'),
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
    content: `确定要${actionText}该横幅吗？`,
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
  await api.updateBanner(payload)
  $message.success(payload.is_active ? '横幅已启用' : '横幅已停用')
  $table.value?.handleSearch()
}
</script>

<template>
  <CommonPage show-footer title="横幅列表">
    <template #action>
      <NButton v-permission="'post/api/v1/banner/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建横幅
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:sorter="sorter"
      :columns="columns"
      :get-data="getBannerTableData"
      :scroll-x="1320"
    >
      <template #queryBar>
        <QueryBarItem label="关键字" :label-width="50">
          <NInput
            v-model:value="queryItems.keyword"
            clearable
            type="text"
            placeholder="搜索横幅内容"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="备注" :label-width="40">
          <NInput
            v-model:value="queryItems.note"
            clearable
            type="text"
            placeholder="搜索活动备注"
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
        :label-width="90"
        :model="modalForm"
        :rules="rules"
      >
        <NFormItem label="横幅内容" path="content">
          <NInput v-model:value="modalForm.content" maxlength="255" show-count placeholder="请输入横幅内容" />
        </NFormItem>
        <NFormItem label="活动备注" path="note">
          <NInput v-model:value="modalForm.note" maxlength="255" show-count placeholder="请输入备注，便于标记活动" />
        </NFormItem>
        <NFormItem label="排序" path="priority">
          <NInputNumber
            v-model:value="modalForm.priority"
            class="w-full"
            clearable
            :min="1"
            placeholder="从 1 开始，留空表示未设置"
          />
        </NFormItem>
        <NFormItem label="跳转路径" path="link_url">
          <NInput v-model:value="modalForm.link_url" placeholder="请输入站内路径或完整链接" />
        </NFormItem>
        <NFormItem label="是否启用" path="is_active">
          <NSwitch v-model:value="modalForm.is_active" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
