<script setup>
import { onMounted, ref } from 'vue'
import { NButton, NForm, NFormItem, NInput, NSpin } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import api from '@/api'

defineOptions({ name: '站点配置' })

const formRef = ref(null)
const loading = ref(false)
const saving = ref(false)
const form = ref(createInitialForm())

const rules = {
  share_base_url: {
    validator(_, value) {
      if (!value) {
        return true
      }
      try {
        const parsed = new URL(value)
        return ['http:', 'https:'].includes(parsed.protocol)
      } catch {
        return new Error('请输入完整的 http(s) 分享域名 URL')
      }
    },
    trigger: ['input', 'blur'],
  },
}

function createInitialForm() {
  return {
    logo_url: '',
    about_title: '',
    about_text: '',
    footer_disclaimer: '',
    share_base_url: '',
  }
}

function applySiteConfig(data = {}) {
  form.value = {
    logo_url: data.logo_url || '',
    about_title: data.about_title || '',
    about_text: Array.isArray(data.about_lines) ? data.about_lines.join('\n') : '',
    footer_disclaimer: data.footer_disclaimer || '',
    share_base_url: data.share_base_url || '',
  }
}

function buildPayload() {
  return {
    logo_url: form.value.logo_url.trim(),
    about_title: form.value.about_title.trim(),
    about_lines: form.value.about_text.split('\n').map((item) => item.trim()).filter(Boolean),
    footer_disclaimer: form.value.footer_disclaimer.trim(),
    share_base_url: form.value.share_base_url.trim(),
  }
}

async function loadSiteConfig() {
  loading.value = true
  try {
    const response = await api.getSiteConfig()
    applySiteConfig(response.data || {})
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    const response = await api.updateSiteConfig(buildPayload())
    applySiteConfig(response.data || {})
    $message.success('站点配置已保存')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadSiteConfig()
})
</script>

<template>
  <CommonPage show-footer title="站点配置">
    <template #action>
      <NButton
        v-permission="'post/api/v1/site-config/update'"
        type="primary"
        :loading="saving"
        @click="handleSave"
      >
        保存配置
      </NButton>
    </template>

    <NSpin :show="loading">
      <NForm
        ref="formRef"
        label-placement="left"
        :label-width="120"
        :model="form"
        :rules="rules"
      >
        <NFormItem label="Logo URL" path="logo_url">
          <NInput
            v-model:value="form.logo_url"
            maxlength="500"
            show-count
            placeholder="https://example.com/logo.png"
          />
        </NFormItem>

        <NFormItem label="About 标题" path="about_title">
          <NInput
            v-model:value="form.about_title"
            maxlength="100"
            show-count
            placeholder="例如 About"
          />
        </NFormItem>

        <NFormItem label="About 文案" path="about_text">
          <NInput
            v-model:value="form.about_text"
            type="textarea"
            :autosize="{ minRows: 4, maxRows: 8 }"
            placeholder="每行一段文案"
          />
        </NFormItem>

        <NFormItem label="底部声明" path="footer_disclaimer">
          <NInput
            v-model:value="form.footer_disclaimer"
            maxlength="500"
            show-count
            placeholder="例如 This website is for learning and collection purposes, with no commercial use."
          />
        </NFormItem>

        <NFormItem label="分享域名 URL" path="share_base_url">
          <NInput
            v-model:value="form.share_base_url"
            maxlength="500"
            show-count
            placeholder="https://example.com/sym"
          />
        </NFormItem>
      </NForm>
    </NSpin>
  </CommonPage>
</template>
