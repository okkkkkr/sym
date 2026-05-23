<script setup>
import { computed, h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NImage,
  NInput,
  NInputNumber,
  NPopconfirm,
  NSelect,
  NSwitch,
  NTag,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { formatDate } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

defineOptions({ name: '联系方式管理' })

const DEFAULT_QR_IMAGE_URL = 'https://os.alipayobjects.com/rmsportal/QBnOOoLaAfKPirc.png'

const $table = ref(null)
const queryItems = ref({})
const sorter = ref({ columnKey: 'updated_at', order: 'descend' })
const vPermission = resolveDirective('permission')
const statusUpdatingIds = ref([])
const actionCellStyle = 'display: flex; justify-content: center; align-items: center; gap: 8px; flex-wrap: wrap;'

const initForm = {
  platform: '',
  display_name: '',
  contact_type: null,
  contact_value: '',
  link_url: '',
  qr_image_url: '',
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

const rules = {
  platform: {
    required: true,
    message: '请输入平台标识',
    trigger: ['input', 'blur'],
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

const columns = computed(() => [
  {
    title: '平台',
    key: 'platform',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '展示名称',
    key: 'display_name',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '联系类型',
    key: 'contact_type',
    width: 110,
    align: 'center',
    render(row) {
      return row.contact_type
        ? h(NTag, { type: 'info' }, { default: () => row.contact_type })
        : h('span', { style: 'color: var(--n-text-color-disabled);' }, '-')
    },
  },
  {
    title: '联系内容',
    key: 'contact_value',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '二维码',
    key: 'qr_image_url',
    width: 110,
    align: 'center',
    render(row) {
      return h(NImage, {
        width: 56,
        src: row.qr_image_url || DEFAULT_QR_IMAGE_URL,
        objectFit: 'cover',
      })
    },
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
        [[vPermission, 'post/api/v1/contact/update']]
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
          <NInput v-model:value="modalForm.platform" clearable placeholder="请输入平台标识" />
        </NFormItem>
        <NFormItem label="展示名称" path="display_name">
          <NInput v-model:value="modalForm.display_name" clearable placeholder="请输入展示名称" />
        </NFormItem>
        <NFormItem label="联系类型" path="contact_type">
          <NSelect v-model:value="modalForm.contact_type" clearable :options="contactTypeOptions" placeholder="请选择联系类型" />
        </NFormItem>
        <NFormItem label="联系内容" path="contact_value">
          <NInput v-model:value="modalForm.contact_value" clearable placeholder="请输入联系内容" />
        </NFormItem>
        <NFormItem label="跳转链接" path="link_url">
          <NInput v-model:value="modalForm.link_url" clearable placeholder="请输入跳转链接" />
        </NFormItem>
        <NFormItem label="二维码链接" path="qr_image_url">
          <NInput v-model:value="modalForm.qr_image_url" clearable placeholder="请输入二维码图片地址" />
        </NFormItem>
        <NFormItem label="排序" path="order">
          <NInputNumber v-model:value="modalForm.order" clearable :min="0" style="width: 100%" />
        </NFormItem>
        <NFormItem label="启用状态" path="is_active">
          <NSwitch v-model:value="modalForm.is_active" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
