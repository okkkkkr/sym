<template>
  <div ref="tableRoot" v-bind="$attrs">
    <QueryBar v-if="$slots.queryBar" mb-30 @search="handleSearch" @reset="handleReset">
      <slot name="queryBar" />
    </QueryBar>

    <n-data-table
      :remote="remote"
      :loading="loading"
      :columns="columns"
      :data="tableData"
      :scroll-x="scrollX"
      :row-key="(row) => row[rowKey]"
      :checked-row-keys="checkedRowKeys"
      :pagination="isPagination ? pagination : false"
      @update:checked-row-keys="onChecked"
      @update:page="onPageChange"
      @update:sorter="onSorterChange"
    />
  </div>
</template>

<script setup>
const props = defineProps({
  /**
   * @remote true: 后端分页  false： 前端分页
   */
  remote: {
    type: Boolean,
    default: true,
  },
  /**
   * @remote 是否分页
   */
  isPagination: {
    type: Boolean,
    default: true,
  },
  scrollX: {
    type: Number,
    default: 450,
  },
  rowKey: {
    type: String,
    default: 'id',
  },
  checkedRowKeys: {
    type: Array,
    default() {
      return undefined
    },
  },
  columns: {
    type: Array,
    required: true,
  },
  /** queryBar中的参数 */
  queryItems: {
    type: Object,
    default() {
      return {}
    },
  },
  /** 补充参数（可选） */
  extraParams: {
    type: Object,
    default() {
      return {}
    },
  },
  sorter: {
    type: Object,
    default() {
      return {}
    },
  },
  /**
   * ! 约定接口入参出参
   * * 分页模式需约定分页接口入参
   *    @page_size 分页参数：一页展示多少条，默认10
   *    @page   分页参数：页码，默认1
   */
  getData: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits([
  'update:queryItems',
  'update:sorter',
  'update:checkedRowKeys',
  'onChecked',
  'onDataChange',
])
const loading = ref(false)
const tableRoot = ref(null)
const initQuery = { ...props.queryItems }
const tableData = ref([])

function normalizeSorter(sorter) {
  if (Array.isArray(sorter)) {
    return normalizeSorter(sorter[0])
  }

  if (!sorter || !sorter.columnKey || !sorter.order) {
    return {}
  }

  return {
    columnKey: sorter.columnKey,
    order: sorter.order,
  }
}

const currentSorter = ref(normalizeSorter(props.sorter))

const pagination = reactive({
  page: 1,
  page_size: 10,
  pageSizes: [10, 20, 50, 100],
  showSizePicker: true,
  prefix({ itemCount }) {
    return `共 ${itemCount} 条`
  },
  onChange: (page) => {
    pagination.page = page
  },
  onUpdatePageSize: async (pageSize) => {
    pagination.page_size = pageSize
    pagination.page = 1
    await handleQuery()
    scrollToTableTop()
  },
})

async function handleQuery() {
  try {
    loading.value = true
    let paginationParams = {}
    let sorterParams = {}
    // 如果非分页模式或者使用前端分页,则无需传分页参数
    if (props.isPagination && props.remote) {
      paginationParams = { page: pagination.page, page_size: pagination.page_size }
    }
    if (currentSorter.value.columnKey && currentSorter.value.order) {
      sorterParams = {
        sort_field: currentSorter.value.columnKey,
        sort_order: currentSorter.value.order === 'ascend' ? 'asc' : 'desc',
      }
    }
    const { data, total } = await props.getData({
      ...props.queryItems,
      ...props.extraParams,
      ...paginationParams,
      ...sorterParams,
    })
    tableData.value = data
    pagination.itemCount = total || 0
  } catch (error) {
    tableData.value = []
    pagination.itemCount = 0
  } finally {
    emit('onDataChange', tableData.value)
    loading.value = false
  }
}
function handleSearch() {
  pagination.page = 1
  handleQuery()
}
async function handleReset() {
  const queryItems = { ...props.queryItems }
  for (const key in queryItems) {
    queryItems[key] = null
  }
  emit('update:queryItems', { ...queryItems, ...initQuery })
  await nextTick()
  pagination.page = 1
  handleQuery()
}
async function onPageChange(currentPage) {
  pagination.page = currentPage
  if (props.remote) {
    await handleQuery()
  }
  scrollToTableTop()
}

async function scrollToTableTop() {
  await nextTick()
  tableRoot.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
function onChecked(rowKeys) {
  if (props.columns.some((item) => item.type === 'selection')) {
    emit('update:checkedRowKeys', rowKeys)
    emit('onChecked', rowKeys)
  }
}

function onSorterChange(sorter) {
  currentSorter.value = normalizeSorter(sorter)
  emit('update:sorter', currentSorter.value)
  pagination.page = 1
  if (props.remote) {
    handleQuery()
  }
}

defineExpose({
  handleSearch,
  handleReset,
  tableData,
})
</script>
