<script setup>
import { computed, h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NPopconfirm, NTag } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { useCRUD } from '@/composables'
import api from '@/api'

defineOptions({ name: '渠道管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const actionCellStyle =
  'display: flex; justify-content: center; align-items: center; gap: 8px; flex-wrap: wrap;'

const initForm = {
  platform_name: '',
  custom_name: '',
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
  name: '渠道',
  initForm,
  doCreate: api.createPlatform,
  doUpdate: api.updatePlatform,
  doDelete: api.deletePlatform,
  refresh: () => $table.value?.handleSearch(),
})

const rules = {
  platform_name: {
    required: true,
    message: '请输入渠道名称',
    trigger: ['input', 'blur'],
  },
  custom_name: [
    {
      required: true,
      message: '请输入自定义名称',
      trigger: ['input', 'blur'],
    },
    {
      pattern: /^[a-z0-9_-]+$/,
      message: '仅允许小写字母、数字、短横线和下划线',
      trigger: ['input', 'blur'],
    },
  ],
}

onMounted(() => {
  $table.value?.handleSearch()
})

async function copyShareUrl(row) {
  await navigator.clipboard.writeText(row.share_url)
  $message.success('推广链接已复制')
}

const columns = computed(() => [
  {
    title: '渠道名称',
    key: 'platform_name',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '自定义名称',
    key: 'custom_name',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '点击量',
    key: 'click_count',
    width: 100,
    align: 'center',
    render(row) {
      return h(NTag, { type: 'warning' }, { default: () => String(row.click_count || 0) })
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 220,
    align: 'center',
    fixed: 'right',
    render(row) {
      if (row.is_system) {
        return h(NTag, { type: 'default' }, { default: () => '系统默认渠道' })
      }
      return h('div', { style: actionCellStyle }, [
        h(
          NButton,
          {
            size: 'tiny',
            quaternary: true,
            type: 'primary',
            onClick: () => copyShareUrl(row),
          },
          { default: () => '复制链接' }
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
            { default: () => '编辑' }
          ),
          [[vPermission, 'post/api/v1/platform/update']]
        ),
        h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete({ id: row.id }) },
          {
            trigger: () =>
              withDirectives(
                h(
                  NButton,
                  { size: 'tiny', quaternary: true, type: 'error' },
                  { default: () => '删除' }
                ),
                [[vPermission, 'delete/api/v1/platform/delete']]
              ),
            default: () => h('div', {}, '确定删除该渠道吗?'),
          }
        ),
      ])
    },
  },
])
</script>

<template>
  <CommonPage show-footer title="渠道列表">
    <template #action>
      <NButton v-permission="'post/api/v1/platform/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建渠道
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getPlatformList"
    >
      <template #queryBar>
        <QueryBarItem label="关键字" :label-width="50">
          <NInput
            v-model:value="queryItems.keyword"
            clearable
            placeholder="搜索渠道名称或自定义名称"
            @keypress.enter="$table?.handleSearch()"
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
        :label-width="100"
        :model="modalForm"
        :rules="rules"
      >
        <NFormItem label="渠道名称" path="platform_name">
          <NInput
            v-model:value="modalForm.platform_name"
            maxlength="100"
            show-count
            placeholder="例如 Facebook"
          />
        </NFormItem>
        <NFormItem label="自定义名称" path="custom_name">
          <NInput
            v-model:value="modalForm.custom_name"
            maxlength="50"
            show-count
            placeholder="例如 fb"
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
