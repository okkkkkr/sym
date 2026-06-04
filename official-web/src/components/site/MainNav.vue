<script setup>
import { computed, markRaw, onBeforeUnmount, onMounted, ref } from "vue";
import {
  FacebookOutlined,
  LinkOutlined,
  MailOutlined,
  PhoneOutlined,
  WechatOutlined,
  WhatsAppOutlined,
} from "@ant-design/icons-vue";
import { message } from "ant-design-vue";
import { RouterLink, useRoute } from "vue-router";

import { useContactPopoverTracking } from "../../composables/useContactPopoverTracking";
import { useSiteConfig } from "../../composables/useSiteConfig";
import {
  fetchCatalogCategories,
  resolveCategoryKey,
} from "../../services/catalog";
import { fetchActiveContacts } from "../../services/contacts";

const props = defineProps({
  showCategories: {
    type: Boolean,
    default: true,
  },
});

const route = useRoute();
const isSmallScreen = ref(false);
const categories = ref([]);
const contacts = ref([]);
const { siteConfig, loadSiteConfig } = useSiteConfig();
const { handleContactPopoverChange, disposeContactPopoverTracking } =
  useContactPopoverTracking(isSmallScreen);

const contactPopoverTrigger = computed(() =>
  isSmallScreen.value ? "click" : "hover",
);
const navContacts = computed(() => contacts.value.slice(0, 2));
const logoImage = computed(() => siteConfig.value.logo_url);
const shareButtonTitle = ref("复制当前链接");

let mediaQuery;
const PLATFORM_STORAGE_KEY = "sym-fast:platform";

const contactIconMap = {
  facebook: markRaw(FacebookOutlined),
  whatsapp: markRaw(WhatsAppOutlined),
  wechat: markRaw(WechatOutlined),
  email: markRaw(MailOutlined),
  phone: markRaw(PhoneOutlined),
};

const currentCategory = computed(() => {
  return resolveCategoryKey(categories.value, route.query.category);
});

const primaryCategories = computed(() => {
  if (!isSmallScreen.value) {
    return categories.value;
  }

  return categories.value.slice(0, 2);
});

const overflowCategories = computed(() => {
  if (!isSmallScreen.value) {
    return [];
  }

  return categories.value.slice(2);
});

const selectedKeys = computed(() =>
  route.path === "/sym" ? [currentCategory.value] : [],
);
const menuVisible = computed(
  () => props.showCategories && categories.value.length > 0,
);

function categoryLink(categoryKey) {
  return { path: "/sym", query: { category: categoryKey } };
}

function isActiveCategory(categoryKey) {
  return route.path === "/sym" && currentCategory.value === categoryKey;
}

function updateSmallScreenState(event) {
  isSmallScreen.value = event.matches;
}

function resolveContactIcon(item) {
  const key = String(item.platform || item.contact_type || "").toLowerCase();
  return contactIconMap[key] || markRaw(LinkOutlined);
}

async function handleShare() {
  const url = new URL(window.location.href);
  const platform = String(
    window.localStorage.getItem(PLATFORM_STORAGE_KEY) || "",
  ).trim();

  if (platform) {
    url.searchParams.set("plat", platform);
  }

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(url.toString());
    } else {
      const input = document.createElement("input");
      input.value = url.toString();
      input.setAttribute("readonly", "readonly");
      input.style.position = "absolute";
      input.style.left = "-9999px";
      document.body.appendChild(input);
      input.select();
      document.execCommand("copy");
      document.body.removeChild(input);
    }

    shareButtonTitle.value = "Link copied";
    message.success("Link copied");
    window.setTimeout(() => {
      shareButtonTitle.value = "复制当前链接";
    }, 1600);
  } catch (error) {
    shareButtonTitle.value = "复制失败";
    message.error("复制失败");
    window.setTimeout(() => {
      shareButtonTitle.value = "复制当前链接";
    }, 1600);
  }
}

onMounted(() => {
  mediaQuery = window.matchMedia("(max-width: 767px)");
  isSmallScreen.value = mediaQuery.matches;

  loadSiteConfig().catch(() => {});

  if (props.showCategories) {
    fetchCatalogCategories()
      .then((data) => {
        categories.value = data;
      })
      .catch(() => {
        categories.value = [];
      });
  }

  fetchActiveContacts()
    .then((data) => {
      contacts.value = data;
    })
    .catch(() => {
      contacts.value = [];
    });

  if (mediaQuery.addEventListener) {
    mediaQuery.addEventListener("change", updateSmallScreenState);
    return;
  }

  mediaQuery.addListener(updateSmallScreenState);
});

onBeforeUnmount(() => {
  disposeContactPopoverTracking();
  if (!mediaQuery) {
    return;
  }

  if (mediaQuery.removeEventListener) {
    mediaQuery.removeEventListener("change", updateSmallScreenState);
    return;
  }

  mediaQuery.removeListener(updateSmallScreenState);
});
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

      <a-menu
        v-if="menuVisible"
        mode="horizontal"
        :selected-keys="selectedKeys"
        trigger-sub-menu-action="click"
        class="main-nav__menu"
      >
        <a-menu-item v-for="category in primaryCategories" :key="category.key">
          <RouterLink
            :to="categoryLink(category.key)"
            active-class="main-nav__route-state"
            exact-active-class="main-nav__route-state"
            class="main-nav__menu-link"
            :class="{ 'is-active': isActiveCategory(category.key) }"
            >{{ category.name }}</RouterLink
          >
        </a-menu-item>
        <a-sub-menu
          v-if="overflowCategories.length"
          key="more"
          popup-class-name="main-nav__submenu-popup"
        >
          <template #title>...</template>
          <a-menu-item
            v-for="category in overflowCategories"
            :key="category.key"
          >
            <RouterLink
              :to="categoryLink(category.key)"
              active-class="main-nav__route-state"
              exact-active-class="main-nav__route-state"
              class="main-nav__menu-link"
              :class="{ 'is-active': isActiveCategory(category.key) }"
              >{{ category.name }}</RouterLink
            >
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
          @openChange="(open) => handleContactPopoverChange(item, open)"
        >
          <template #content>
            <div class="contact-popover__body">
              <div class="contact-popover__title">{{ item.display_name }}</div>
              <div class="contact-popover__meta">
                {{ item.contact_value || item.link_url }}
              </div>
              <a-image :width="150" :preview="false" :src="item.qr_image_url" />
            </div>
          </template>

          <span class="main-nav__contact-trigger">
            <component
              :is="resolveContactIcon(item)"
              class="main-nav__contact-icon"
            />
          </span>
        </a-popover>

        <button
          type="button"
          class="main-nav__share"
          :title="shareButtonTitle"
          :aria-label="shareButtonTitle"
          @click="handleShare"
        >
          <svg
            class="main-nav__share-icon"
            xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink"
            viewBox="0 0 576 512"
          >
            <path
              d="M568.482 177.448L424.479 313.433C409.3 327.768 384 317.14 384 295.985v-71.963c-144.575.97-205.566 35.113-164.775 171.353c4.483 14.973-12.846 26.567-25.006 17.33C155.252 383.105 120 326.488 120 269.339c0-143.937 117.599-172.5 264-173.312V24.012c0-21.174 25.317-31.768 40.479-17.448l144.003 135.988c10.02 9.463 10.028 25.425 0 34.896zM384 379.128V448H64V128h50.916a11.99 11.99 0 0 0 8.648-3.693c14.953-15.568 32.237-27.89 51.014-37.676C185.708 80.83 181.584 64 169.033 64H48C21.49 64 0 85.49 0 112v352c0 26.51 21.49 48 48 48h352c26.51 0 48-21.49 48-48v-88.806c0-8.288-8.197-14.066-16.011-11.302a71.83 71.83 0 0 1-34.189 3.377c-7.27-1.046-13.8 4.514-13.8 11.859z"
              fill="currentColor"
            ></path>
          </svg>
        </button>
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

.main-nav__menu:empty {
  display: none;
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
  transition:
    color 0.2s ease,
    font-weight 0.2s ease;
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

:deep(
  .main-nav__menu.ant-menu-horizontal
    > .ant-menu-submenu
    .ant-menu-submenu-title
) {
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
  transition:
    color 0.2s ease,
    transform 0.2s ease;
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

.main-nav__share {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #111111;
  cursor: pointer;
}

.main-nav__share:hover {
  color: #000000;
}

.main-nav__share-icon {
  width: 24px;
  height: 24px;
  transition:
    color 0.2s ease,
    transform 0.2s ease;
}

.main-nav__share:hover .main-nav__share-icon {
  transform: translateY(-1px);
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

@media (max-width: 767px) {
  .main-nav__inner {
    gap: 12px;
  }

  .main-nav__contact {
    gap: 14px;
  }
}
</style>
