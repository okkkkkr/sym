<script setup>
import { computed, markRaw, onBeforeUnmount, onMounted, ref } from 'vue'
import { FacebookOutlined, LinkOutlined, MailOutlined, PhoneOutlined, WechatOutlined, WhatsAppOutlined } from '@ant-design/icons-vue'
import { RouterLink, useRoute } from 'vue-router'

import { useSiteConfig } from '../../composables/useSiteConfig'
import { fetchCatalogCategories, resolveCategoryKey } from '../../services/catalog'
import { fetchActiveContacts, reportContactClick } from '../../services/contacts'

const route = useRoute()
const isSmallScreen = ref(false)
const categories = ref([])
const contacts = ref([])
const { siteConfig, loadSiteConfig } = useSiteConfig()

const contactPopoverTrigger = computed(() => (isSmallScreen.value ? 'click' : 'hover'))
const navContacts = computed(() => contacts.value.slice(0, 2))
const logoImage = computed(() => siteConfig.value.logo_url)

let mediaQuery

const contactIconMap = {
  facebook: markRaw(FacebookOutlined),
  whatsapp: markRaw(WhatsAppOutlined),
  wechat: markRaw(WechatOutlined),
  email: markRaw(MailOutlined),
  phone: markRaw(PhoneOutlined),
}

const currentCategory = computed(() => {
  return resolveCategoryKey(categories.value, route.query.category)
})

const primaryCategories = computed(() => {
  if (!isSmallScreen.value) {
    return categories.value
  }

  return categories.value.slice(0, 2)
})

const overflowCategories = computed(() => {
  if (!isSmallScreen.value) {
    return []
  }

  return categories.value.slice(2)
})

const selectedKeys = computed(() => (route.path === '/sym' ? [currentCategory.value] : []))

function categoryLink(categoryKey) {
  return { path: '/sym', query: { category: categoryKey } }
}

function isActiveCategory(categoryKey) {
  return route.path === '/sym' && currentCategory.value === categoryKey
}

function updateSmallScreenState(event) {
  isSmallScreen.value = event.matches
}

function resolveContactIcon(item) {
  const key = String(item.platform || item.contact_type || '').toLowerCase()
  return contactIconMap[key] || markRaw(LinkOutlined)
}

function handleContactClick(item) {
  reportContactClick(item?.id)
}

onMounted(() => {
  mediaQuery = window.matchMedia('(max-width: 767px)')
  isSmallScreen.value = mediaQuery.matches

  loadSiteConfig().catch(() => {})

  fetchCatalogCategories()
    .then((data) => {
      categories.value = data
    })
    .catch(() => {
      categories.value = []
    })

  fetchActiveContacts()
    .then((data) => {
      contacts.value = data
    })
    .catch(() => {
      contacts.value = []
    })

  if (mediaQuery.addEventListener) {
    mediaQuery.addEventListener('change', updateSmallScreenState)
    return
  }

  mediaQuery.addListener(updateSmallScreenState)
})

onBeforeUnmount(() => {
  if (!mediaQuery) {
    return
  }

  if (mediaQuery.removeEventListener) {
    mediaQuery.removeEventListener('change', updateSmallScreenState)
    return
  }

  mediaQuery.removeListener(updateSmallScreenState)
})

</script>

<template>
  <header class="main-nav">
    <div class="page-container main-nav__inner">
      <RouterLink to="/" class="main-nav__brand">
        <span class="main-nav__logo" aria-hidden="true">
          <img
            v-if="logoImage"
            :src="logoImage"
            alt=""
            class="main-nav__logo-face main-nav__logo-face--front main-nav__logo-image"
          />
        </span>
      </RouterLink>

      <a-menu mode="horizontal" :selected-keys="selectedKeys" trigger-sub-menu-action="click" class="main-nav__menu">
        <a-menu-item v-for="category in primaryCategories" :key="category.key">
          <RouterLink :to="categoryLink(category.key)" active-class="main-nav__route-state" exact-active-class="main-nav__route-state" class="main-nav__menu-link" :class="{ 'is-active': isActiveCategory(category.key) }">{{ category.name }}</RouterLink>
        </a-menu-item>
        <a-sub-menu v-if="overflowCategories.length" key="more" popup-class-name="main-nav__submenu-popup">
          <template #title>...</template>
          <a-menu-item v-for="category in overflowCategories" :key="category.key">
            <RouterLink
              :to="categoryLink(category.key)"
              active-class="main-nav__route-state"
              exact-active-class="main-nav__route-state"
              class="main-nav__menu-link"
              :class="{ 'is-active': isActiveCategory(category.key) }"
            >{{ category.name }}</RouterLink>
          </a-menu-item>
        </a-sub-menu>
      </a-menu>

      <div class="main-nav__contact" aria-label="Contact links">
        <a-popover
          v-for="item in navContacts"
          :key="item.id || item.platform"
          :trigger="contactPopoverTrigger"
          placement="bottomRight"
          overlay-class-name="contact-popover"
        >
          <template #content>
            <div class="contact-popover__body">
              <div class="contact-popover__title">{{ item.display_name }}</div>
              <div class="contact-popover__meta">{{ item.contact_value || item.link_url }}</div>
              <a-image :width="150" :preview="false" :src="item.qr_image_url" />
            </div>
          </template>

          <span class="main-nav__contact-trigger" @click="handleContactClick(item)">
            <component :is="resolveContactIcon(item)" class="main-nav__contact-icon" />
          </span>
        </a-popover>
      </div>
    </div>
  </header>
</template>

<style scoped>
.main-nav {
  background: #f7f5ef;
}

.main-nav__inner {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 24px;
  padding: 16px 24px 12px;
  border-bottom: 2px solid #242424;
}

.main-nav__brand {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #111111;
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 0.08em;
  perspective: 900px;
}

.main-nav__logo {
  position: relative;
  width: 40px;
  height: 40px;
  overflow: hidden;
  border-radius: 50%;
}

.main-nav__logo-face {
  position: absolute;
  inset: 0;
  transform-origin: center;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

.main-nav__logo-face--front {
  transform: rotateY(0deg) translateZ(1px);
}

.main-nav__logo-face--back {
  transform: rotateY(180deg) translateZ(1px);
}

.main-nav__logo-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.main-nav__logo-image--back {
  transform: scaleX(-1);
}

.main-nav__menu {
  justify-self: center;
  width: 100%;
  min-width: 0;
  background: transparent;
  border-bottom: 0;
}

:deep(.main-nav__menu .ant-menu-overflow) {
  justify-content: center;
}

:deep(.main-nav__menu .ant-menu-item) {
  padding-inline: 14px;
  font-size: 12px;
  color: #2a2a2a !important;
  text-align: center;
  cursor: pointer;
  transition: color 0.2s ease;
}

:deep(.main-nav__menu .ant-menu-item a) {
  color: inherit !important;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s ease, font-weight 0.2s ease;
}

:deep(.main-nav__menu-link) {
  font-size: 12px;
  color: #2a2a2a !important;
  font-weight: 500;
}

:deep(.main-nav__menu-link:hover) {
  color: #000000 !important;
}

:deep(.main-nav__menu-link.is-active) {
  font-size: 14px;
  color: #000000 !important;
  font-weight: 700;
}

:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-item::after),
:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-overflow-item::after),
:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-submenu::after) {
  display: none;
}

:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-item-selected),
:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-item-active),
:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-item:hover) {
  color: #000000 !important;
  background: transparent;
}

:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-item-selected),
:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-item-selected a) {
  color: #000000 !important;
  font-weight: 700;
}

:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-item:hover),
:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-item:hover a),
:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-item-active),
:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-item-active a),
:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-submenu:hover),
:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-submenu-active),
:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-submenu-open) {
  color: #000000 !important;
}

:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-submenu) {
  padding-inline: 14px;
  font-size: 12px;
  color: #2a2a2a !important;
}

:deep(.main-nav__menu.ant-menu-horizontal > .ant-menu-submenu .ant-menu-submenu-title) {
  padding-inline: 0;
  font-weight: 500;
}

:deep(.main-nav__submenu-popup .ant-menu) {
  min-width: 132px;
}

:deep(.main-nav__submenu-popup .ant-menu-item) {
  font-size: 12px;
}

.main-nav__contact {
  justify-self: end;
  display: inline-flex;
  align-items: center;
  gap: 20px;
  color: #111111;
}

.main-nav__contact-icon {
  font-size: 24px;
  cursor: pointer;
  transition: color 0.2s ease, transform 0.2s ease;
}

.main-nav__contact-icon:hover {
  color: #000000;
  transform: translateY(-1px);
}

.main-nav__contact-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.main-nav__popover-content {
  margin: 0;
  max-width: 180px;
  color: #444444;
  font-size: 12px;
  line-height: 1.5;
}

:deep(.contact-popover .ant-popover-inner) {
  min-width: 0;
  width: max-content;
}

:deep(.contact-popover .ant-popover-inner-content) {
  display: flex;
  justify-content: center;
  width: max-content;
}

:deep(.contact-popover__body) {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  width: max-content;
}

:deep(.contact-popover__title) {
  color: #111111;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 12px;
}

:deep(.contact-popover__meta) {
  max-width: 180px;
  color: #555555;
  font-size: 12px;
  line-height: 1.6;
}

</style>
