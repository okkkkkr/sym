<template>
  <div class="home-page">
    <section class="home-page__hero page-container">
      <span class="home-page__eyebrow">Home</span>
      <h1>SYM Storefront</h1>
      <p>
        This placeholder home page is preserved as the standalone entry for the site.
        Product category browsing now lives under the dedicated /sym listing page.
      </p>
      <a-button type="primary" size="large" href="/sym">Open Product Listing</a-button>
    </section>
  </div>
</template>

<style scoped>
.home-page__hero {
  padding: 80px 24px 0;
}

.home-page__eyebrow {
  display: inline-block;
  margin-bottom: 16px;
  color: #6b645d;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.home-page__hero h1 {
  margin: 0 0 16px;
  color: #0e0e0e;
  font-size: clamp(40px, 6vw, 72px);
  font-weight: 900;
}

.home-page__hero p {
  max-width: 620px;
  margin-bottom: 28px;
  color: #2a2a2a;
  font-size: 16px;
  line-height: 1.8;
}

@media (max-width: 900px) {
  .home-page__hero {
    padding: 56px 24px 0;
  }
}
</style>
