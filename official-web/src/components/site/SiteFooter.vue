<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import { fetchCatalogCategories } from '../../services/catalog'
import { fetchActiveContacts } from '../../services/contacts'

const isSmallScreen = ref(false);
const categories = ref([])
const contacts = ref([])
const contactPopoverTrigger = computed(() =>
  isSmallScreen.value ? "click" : "hover",
);

let mediaQuery;

function categoryLink(category) {
  return { path: "/sym", query: { category } };
}

function updateSmallScreenState(event) {
  isSmallScreen.value = event.matches;
}

onMounted(() => {
  mediaQuery = window.matchMedia("(max-width: 900px)");
  isSmallScreen.value = mediaQuery.matches;

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
    mediaQuery.addEventListener("change", updateSmallScreenState);
    return;
  }

  mediaQuery.addListener(updateSmallScreenState);
});

onBeforeUnmount(() => {
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
  <footer class="site-footer">
    <div class="page-container site-footer__grid">
      <section class="site-footer__brand">
        <h3>About</h3>
        <p>I am very happy to share the things I like with you.</p>
        <p>
          If you want to communicate with me, you can contact me through the
          methods.
        </p>
      </section>
      <section class="site-footer__contact">
        <h3>Contact</h3>
        <p v-if="!contacts.length" class="site-footer__empty">No contact channels available.</p>
        <a-popover
          v-for="item in contacts"
          :key="item.id || item.platform"
          :trigger="contactPopoverTrigger"
          placement="right"
          overlay-class-name="contact-popover"
        >
          <template #content>
            <div class="contact-popover__body">
              <div class="contact-popover__title">{{ item.display_name }}</div>
              <div class="site-footer__popover-content">{{ item.contact_value || item.link_url }}</div>
              <a-image :width="150" :preview="false" :src="item.qr_image_url" />
            </div>
          </template>

          <span class="site-footer__contact-trigger">
            <div class="site-footer__contact-item">
              <a :href="item.link_url || '#'" class="site-footer__link">{{ item.display_name }}</a>
            </div>
          </span>
        </a-popover>
      </section>
      <section>
        <h3>Categories</h3>
        <ul>
          <li v-for="category in categories" :key="category.key"><RouterLink :to="categoryLink(category.key)" class="site-footer__link">{{ category.name }}</RouterLink></li>
        </ul>
      </section>
    </div>
    <div class="page-container site-footer__bottom">
      <span>This website is for learning and collection purposes, with no commercial use.</span>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  background: #050505;
  color: #f6f2ea;
}

.site-footer__grid {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 46px;
  padding: 36px 24px 20px;
}

.site-footer__grid > section {
  flex: 0 0 240px;
  width: 240px;
  max-width: 100%;
}

.site-footer h3 {
  margin: 0 0 18px;
  font-size: 18px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.site-footer p,
.site-footer li,
.site-footer span,
.site-footer a {
  color: rgba(246, 242, 234, 0.78);
  font-size: 12px;
  line-height: 1.8;
}

.site-footer__brand p {
  max-width: 260px;
}

.site-footer__empty {
  margin: 0;
}

.site-footer ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.site-footer__link {
  display: inline-block;
  cursor: pointer;
  transition: color 0.2s ease;
}

.site-footer__link:hover {
  color: #ffffff !important;
}

.site-footer__contact {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.site-footer__contact-trigger {
  display: block;
  width: fit-content;
}

.site-footer__contact-item {
  width: fit-content;
}

.site-footer__popover-content {
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

.site-footer__socials {
  display: flex;
  gap: 12px;
  margin-top: 22px;
}

.site-footer__socials span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  color: #f6f2ea;
  font-size: 12px;
}

.site-footer__bottom {
  text-align: center;
  padding: 0 24px 16px;
  span {
    color: #333232;
  }
}

@media (max-width: 900px) {
  .site-footer__grid {
    flex-direction: column;
    gap: 24px;
    padding: 28px 16px 16px;
  }

  .site-footer__grid > section {
    flex-basis: auto;
    width: 100%;
  }

  .site-footer__bottom {
    padding: 0 16px 14px;
  }
}
</style>
