<script setup>
import { computed, onMounted, ref } from 'vue'
import { NButton, NForm, NFormItem, NIcon, NInput, NSpin, NUpload } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import api from '@/api'

defineOptions({ name: '站点配置' })

let logoFileSeed = 0

const formRef = ref(null)
const loading = ref(false)
const saving = ref(false)
const uploadingLogo = ref(false)
const form = ref(createInitialForm())
const logoFileList = ref([])
const initialPayload = ref(JSON.stringify(createInitialPayload()))

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

const saveDisabled = computed(
  () =>
    loading.value ||
    saving.value ||
    uploadingLogo.value ||
    JSON.stringify(buildPayload()) === initialPayload.value
)

function createInitialForm() {
  return {
    logo_url: '',
    about_title: '',
    about_text: '',
    footer_disclaimer: '',
    share_base_url: '',
  }
}

function createInitialPayload() {
  return {
    logo_url: '',
    about_title: '',
    about_lines: [],
    footer_disclaimer: '',
    share_base_url: '',
  }
}

function getFileNameFromUrl(url) {
  const normalized = String(url || '').trim()
  if (!normalized) return 'logo'
  try {
    const parsed = new URL(normalized)
    return parsed.pathname.split('/').filter(Boolean).pop() || 'logo'
  } catch {
    return normalized.split('/').filter(Boolean).pop() || 'logo'
  }
}

function createLogoUploadFile(url, rawUrl = url) {
  if (!url) return null
  logoFileSeed += 1
  return {
    id: `logo-${logoFileSeed}`,
    name: getFileNameFromUrl(rawUrl || url),
    status: 'finished',
    url,
    thumbnailUrl: url,
    rawUrl,
  }
}

function normalizeLogoFileList(fileList = []) {
  return fileList
    .map((file) => {
      if (!file) return null
      if (file.url || file.thumbnailUrl) {
        return {
          ...file,
          url: file.url || file.thumbnailUrl,
          thumbnailUrl: file.thumbnailUrl || file.url,
          rawUrl: file.rawUrl || file.url || file.thumbnailUrl || '',
        }
      }
      if (!file.file) return file
      const objectUrl = URL.createObjectURL(file.file)
      return { ...file, url: objectUrl, thumbnailUrl: objectUrl, rawUrl: file.rawUrl || '' }
    })
    .filter(Boolean)
}

function applySiteConfig(data = {}) {
  form.value = {
    logo_url: data.logo_storage_url || data.logo_url || '',
    about_title: data.about_title || '',
    about_text: Array.isArray(data.about_lines) ? data.about_lines.join('\n') : '',
    footer_disclaimer: data.footer_disclaimer || '',
    share_base_url: data.share_base_url || '',
  }
  logoFileList.value = data.logo_url
    ? [createLogoUploadFile(data.logo_url, data.logo_storage_url || data.logo_url)]
    : []
  initialPayload.value = JSON.stringify(buildPayload())
}

function buildPayload() {
  return {
    logo_url: form.value.logo_url.trim(),
    about_title: form.value.about_title.trim(),
    about_lines: form.value.about_text
      .split('\n')
      .map((item) => item.trim())
      .filter(Boolean),
    footer_disclaimer: form.value.footer_disclaimer.trim(),
    share_base_url: form.value.share_base_url.trim(),
  }
}

function syncLogoValue(fileList = []) {
  logoFileList.value = normalizeLogoFileList(fileList).slice(-1)
  form.value.logo_url = logoFileList.value[0]?.rawUrl || ''
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

async function handleLogoUpload({ file, onError, onFinish, onProgress }) {
  uploadingLogo.value = true
  try {
    if (!file?.file) {
      throw new Error('未找到待上传图片')
    }

    const credential = await api.getSiteConfigLogoUploadToken({
      file_name: file.name,
      content_type: file.type || '',
    })

    await new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      const formData = new FormData()

      xhr.open('POST', credential.data.upload_url, true)
      xhr.upload.onprogress = (event) => {
        if (!event.lengthComputable) return
        onProgress({ percent: Math.round((event.loaded / event.total) * 100) })
      }
      xhr.onerror = () => reject(new Error('上传到七牛失败'))
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve()
          return
        }
        reject(new Error('上传到七牛失败'))
      }

      formData.append('token', credential.data.upload_token)
      formData.append('key', credential.data.object_key)
      formData.append('file', file.file)
      xhr.send(formData)
    })

    file.url = credential.data.preview_url || credential.data.url
    file.thumbnailUrl = file.url
    file.rawUrl = credential.data.url
    if (!file.name) {
      file.name = getFileNameFromUrl(file.rawUrl)
    }
    syncLogoValue([file])
    onFinish()
  } catch (error) {
    syncLogoValue(logoFileList.value)
    onError()
    if (!error?.code) {
      $message.error(error.message || '上传失败')
    }
  } finally {
    uploadingLogo.value = false
  }
}

function handleLogoFileListChange(fileList) {
  syncLogoValue(fileList)
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
        :disabled="saveDisabled"
        @click="handleSave"
      >
        保存配置
      </NButton>
    </template>

    <NSpin :show="loading">
      <NForm ref="formRef" label-placement="left" :label-width="120" :model="form" :rules="rules">
        <NFormItem label="Logo" path="logo_url">
          <NUpload
            v-model:file-list="logoFileList"
            accept="image/*"
            :custom-request="handleLogoUpload"
            list-type="image-card"
            :max="1"
            @update:file-list="handleLogoFileListChange"
          >
            <NIcon v-if="logoFileList.length < 1" size="40">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
                <path
                  d="M368.5 240H272v-96.5c0-8.8-7.2-16-16-16s-16 7.2-16 16V240h-96.5c-8.8 0-16 7.2-16 16 0 4.4 1.8 8.4 4.7 11.3 2.9 2.9 6.9 4.7 11.3 4.7H240v96.5c0 4.4 1.8 8.4 4.7 11.3 2.9 2.9 6.9 4.7 11.3 4.7 8.8 0 16-7.2 16-16V272h96.5c8.8 0 16-7.2 16-16s-7.2-16-16-16z"
                />
              </svg>
            </NIcon>
          </NUpload>
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
