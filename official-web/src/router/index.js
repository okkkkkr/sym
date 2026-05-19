import { createRouter, createWebHistory } from 'vue-router'
import HomeLayout from '../layouts/HomeLayout.vue'
import SiteLayout from '../layouts/SiteLayout.vue'
import Home from '../pages/home.vue'
import Product from '../pages/product.vue'
import ProductDetail from '../pages/product/detail.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: HomeLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: Home,
        },
      ],
    },
    {
      path: '/',
      component: SiteLayout,
      children: [
        {
          path: 'sym',
          name: 'product',
          component: Product,
        },
        {
          path: 'sym/:productId',
          name: 'product-detail',
          component: ProductDetail,
        },
      ],
    },
  ],
})

export default router
