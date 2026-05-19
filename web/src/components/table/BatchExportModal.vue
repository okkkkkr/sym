<script setup>
import { computed, ref, watch } from 'vue'
import { NButton, NModal, NRadio, NRadioGroup, NSpace } from 'naive-ui'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '批量导出',
  },
  checkedCount: {
    type: Number,
    default: 0,
  },
  hasActiveFilters: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:show', 'confirm'])

const exportScope = ref('selected')

const modalVisible = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value),
})

const defaultScope = computed(() => {
  if (props.checkedCount > 0) return 'selected'
  if (props.hasActiveFilters) return 'filtered'
  return 'all'
})

watch(
  () => props.show,
  (value) => {
    if (value) {
      exportScope.value = defaultScope.value
    }
  }
)

function handleConfirm() {
  emit('confirm', exportScope.value)
}
</script>

<template>
  <NModal v-model:show="modalVisible" preset="card" :title="title" style="width: 480px" :mask-closable="false">
    <NRadioGroup v-model:value="exportScope">
      <NSpace :size="16" align="center" justify="space-between" :wrap="false">
        <NRadio value="selected" :disabled="checkedCount === 0">导出选中项（{{ checkedCount }}条）</NRadio>
        <NRadio value="filtered" :disabled="!hasActiveFilters">按筛选条件导出</NRadio>
        <NRadio value="all">导出全部</NRadio>
      </NSpace>
    </NRadioGroup>
    <template #footer>
      <div style="display: flex; justify-content: flex-end; gap: 12px">
        <NButton @click="modalVisible = false">取消</NButton>
        <NButton type="primary" :loading="loading" @click="handleConfirm">确认导出</NButton>
      </div>
    </template>
  </NModal>
</template>