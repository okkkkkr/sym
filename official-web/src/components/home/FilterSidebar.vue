<script setup>
import { computed, ref, watch } from "vue";

const emit = defineEmits(["apply"]);

const props = defineProps({
  title: {
    type: String,
    default: "",
  },
  brands: {
    type: Array,
    default: () => [],
  },
  hotBrands: {
    type: Array,
    default: () => [],
  },
  hotTags: {
    type: Array,
    default: () => [],
  },
  keyword: {
    type: String,
    default: "",
  },
  selectedBrands: {
    type: Array,
    default: () => [],
  },
  selectedTags: {
    type: Array,
    default: () => [],
  },
});

const localKeyword = ref(props.keyword);
const localSelectedBrands = ref([...props.selectedBrands]);
const localSelectedTags = ref([...props.selectedTags]);

const brandOptions = computed(() =>
  props.brands.map((brand) => ({
    label: `${brand.name} (${brand.count})`,
    value: brand.id,
  })),
);

watch(
  () => props.keyword,
  (value) => {
    localKeyword.value = value;
  },
);

watch(
  () => props.selectedBrands,
  (value) => {
    localSelectedBrands.value = [...value];
  },
);

watch(
  () => props.selectedTags,
  (value) => {
    localSelectedTags.value = [...value];
  },
);

function applyFilters() {
  emit("apply", {
    keyword: localKeyword.value.trim(),
    brandIds: [...localSelectedBrands.value],
    tagIds: [...localSelectedTags.value],
  });
}

function toggleHotBrand(brandId) {
  const normalizedId = String(brandId);
  const selectedIds = localSelectedBrands.value.map((item) => String(item));

  if (selectedIds.includes(normalizedId)) {
    localSelectedBrands.value = localSelectedBrands.value.filter((item) => String(item) !== normalizedId);
  } else {
    localSelectedBrands.value = [...localSelectedBrands.value, normalizedId];
  }

  applyFilters();
}

function isHotBrandChecked(brandId) {
  return localSelectedBrands.value.some((item) => String(item) === String(brandId));
}

function toggleHotTag(tagId) {
  const normalizedId = String(tagId);
  const selectedIds = localSelectedTags.value.map((item) => String(item));

  if (selectedIds.includes(normalizedId)) {
    localSelectedTags.value = localSelectedTags.value.filter((item) => String(item) !== normalizedId);
  } else {
    localSelectedTags.value = [...localSelectedTags.value, normalizedId];
  }

  applyFilters();
}

function isHotTagChecked(tagId) {
  return localSelectedTags.value.some((item) => String(item) === String(tagId));
}

function resetFilters() {
  localKeyword.value = "";
  localSelectedBrands.value = [];
  localSelectedTags.value = [];
  applyFilters();
}
</script>

<template>
  <aside class="filter-sidebar">
    <section
      v-if="title"
      class="filter-sidebar__group filter-sidebar__group--title"
    >
      <h3>{{ title }}</h3>
    </section>

    <section class="filter-sidebar__group">
      <h4>Keyword</h4>
      <a-input
        v-model:value="localKeyword"
        class="filter-sidebar__keyword-input"
        placeholder="Search name, description or tag"
        allowClear
        @pressEnter="applyFilters"
      />
    </section>

    <section class="filter-sidebar__group">
      <h4>Brand</h4>
      <a-select
        v-model:value="localSelectedBrands"
        class="filter-sidebar__brand-select"
        mode="multiple"
        show-search
        allow-clear
        :options="brandOptions"
        option-filter-prop="label"
        placeholder="Select brands"
      />
    </section>

    <div class="filter-sidebar__actions">
      <a-button
        block
        class="filter-sidebar__reset-button"
        @click="resetFilters"
      >
        Reset
      </a-button>
      <a-button
        type="primary"
        block
        class="filter-sidebar__apply-button"
        @click="applyFilters"
      >
        Apply Filters
      </a-button>
    </div>

    <section v-if="hotTags.length" class="filter-sidebar__group">
      <h4>Hot Tag</h4>
      <div class="filter-sidebar__hot-tags">
        <a-checkable-tag
          v-for="tag in hotTags"
          :key="tag.id"
          :checked="isHotTagChecked(tag.id)"
          :class="{
            'filter-sidebar__hot-tag': true,
            'filter-sidebar__hot-tag--checked': isHotTagChecked(tag.id),
          }"
          @change="toggleHotTag(tag.id)"
        >
          {{ tag.name }}
        </a-checkable-tag>
      </div>
    </section>

    <section v-if="hotBrands.length" class="filter-sidebar__group filter-sidebar__group--hot-brand-bottom">
      <h4>Hot Brand</h4>
      <div class="filter-sidebar__hot-tags">
        <a-checkable-tag
          v-for="brand in hotBrands"
          :key="brand.id"
          :checked="isHotBrandChecked(brand.id)"
          :class="{
            'filter-sidebar__hot-tag': true,
            'filter-sidebar__hot-tag--checked': isHotBrandChecked(brand.id),
          }"
          @change="toggleHotBrand(brand.id)"
        >
          {{ brand.name }}
        </a-checkable-tag>
      </div>
    </section>
  </aside>
</template>

<style scoped>
.filter-sidebar {
  width: 100%;
}

.filter-sidebar__group {
  margin-bottom: 32px;
}

.filter-sidebar__group--title {
  margin-bottom: 18px;
}

.filter-sidebar__group h3 {
  margin: 0 0 16px;
  color: #111111;
  font-size: 22px;
  font-weight: 700;
}

.filter-sidebar__group h4 {
  margin: 0 0 12px;
  color: #4d4d4d;
  font-size: 16px;
  font-weight: 700;
}

.filter-sidebar__keyword-input {
  width: 100%;
}

.filter-sidebar__brand-select {
  width: 100%;
  display: block;
}

.filter-sidebar__hot-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-sidebar__hot-tag {
  margin-inline-end: 0;
  border-radius: 999px;
  border: 1px solid #cccccc;
}

.filter-sidebar__hot-tag--checked {
  border: 1px solid #1677ff;
;
}

.filter-sidebar__actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: -4px;
  margin-bottom: 28px;
}

.filter-sidebar__group--hot-brand-bottom {
  margin-bottom: 24px;
}

.filter-sidebar__reset-button,
.filter-sidebar__apply-button {
  font-size: 13px;
  font-weight: 700;
}

@media (max-width: 900px) {
  .filter-sidebar__actions {
    margin-bottom: 24px;
  }
}
</style>
