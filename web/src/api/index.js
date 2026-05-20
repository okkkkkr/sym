import { getToken, request } from '@/utils'

async function downloadScopedFile(path, data = {}, filename = 'export.xlsx') {
  const response = await fetch(`${import.meta.env.VITE_BASE_API}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      token: getToken() || '',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    let message = '文件下载失败'
    try {
      const result = await response.json()
      message = result?.detail || result?.msg || message
    } catch {
      // ignore json parse failure
    }
    throw new Error(message)
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

async function downloadScopedGetFile(path, filename = 'download.bin') {
  const response = await fetch(`${import.meta.env.VITE_BASE_API}${path}`, {
    method: 'GET',
    headers: {
      token: getToken() || '',
    },
  })

  if (!response.ok) {
    let message = '文件下载失败'
    try {
      const result = await response.json()
      message = result?.detail || result?.msg || message
    } catch {
      // ignore json parse failure
    }
    throw new Error(message)
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

export default {
  login: (data) => request.post('/base/access_token', data, { noNeedToken: true }),
  getUserInfo: () => request.get('/base/userinfo'),
  getUserMenu: () => request.get('/base/usermenu'),
  getUserApi: () => request.get('/base/userapi'),
  getDashboardOverview: () => request.get('/base/dashboard_overview'),
  // profile
  updatePassword: (data = {}) => request.post('/base/update_password', data),
  // users
  getUserList: (params = {}) => request.get('/user/list', { params }),
  getUserById: (params = {}) => request.get('/user/get', { params }),
  createUser: (data = {}) => request.post('/user/create', data),
  updateUser: (data = {}) => request.post('/user/update', data),
  deleteUser: (params = {}) => request.delete(`/user/delete`, { params }),
  resetPassword: (data = {}) => request.post(`/user/reset_password`, data),
  // role
  getRoleList: (params = {}) => request.get('/role/list', { params }),
  createRole: (data = {}) => request.post('/role/create', data),
  updateRole: (data = {}) => request.post('/role/update', data),
  deleteRole: (params = {}) => request.delete('/role/delete', { params }),
  updateRoleAuthorized: (data = {}) => request.post('/role/authorized', data),
  getRoleAuthorized: (params = {}) => request.get('/role/authorized', { params }),
  // menus
  getMenus: (params = {}) => request.get('/menu/list', { params }),
  createMenu: (data = {}) => request.post('/menu/create', data),
  updateMenu: (data = {}) => request.post('/menu/update', data),
  deleteMenu: (params = {}) => request.delete('/menu/delete', { params }),
  // apis
  getApis: (params = {}) => request.get('/api/list', { params }),
  createApi: (data = {}) => request.post('/api/create', data),
  updateApi: (data = {}) => request.post('/api/update', data),
  deleteApi: (params = {}) => request.delete('/api/delete', { params }),
  refreshApi: (data = {}) => request.post('/api/refresh', data),
  // depts
  getDepts: (params = {}) => request.get('/dept/list', { params }),
  createDept: (data = {}) => request.post('/dept/create', data),
  updateDept: (data = {}) => request.post('/dept/update', data),
  deleteDept: (params = {}) => request.delete('/dept/delete', { params }),
  // categories
  getCategoryList: (params = {}) => request.get('/category/list', { params }),
  getCategoryById: (params = {}) => request.get('/category/get', { params }),
  createCategory: (data = {}) => request.post('/category/create', data),
  updateCategory: (data = {}) => request.post('/category/update', data),
  deleteCategory: (data = {}) => request.delete('/category/delete', { data }),
  exportCategory: (data = {}) =>
    downloadScopedFile('/category/export', data, 'category-export.xlsx'),
  getCategoryHotConfig: (params = {}) => request.get('/category/hot-config', { params }),
  updateCategoryHotConfig: (data = {}) => request.post('/category/hot-config', data),
  // brands
  getBrandList: (params = {}) => request.get('/brand/list', { params }),
  getBrandById: (params = {}) => request.get('/brand/get', { params }),
  createBrand: (data = {}) => request.post('/brand/create', data),
  updateBrand: (data = {}) => request.post('/brand/update', data),
  deleteBrand: (data = {}) => request.delete('/brand/delete', { data }),
  exportBrand: (data = {}) => downloadScopedFile('/brand/export', data, 'brand-export.xlsx'),
  importBrands: (data) => request.post('/brand/import', data),
  // tags
  getTagList: (params = {}) => request.get('/tag/list', { params }),
  getTagById: (params = {}) => request.get('/tag/get', { params }),
  createTag: (data = {}) => request.post('/tag/create', data),
  updateTag: (data = {}) => request.post('/tag/update', data),
  toggleTag: (params = {}) => request.post('/tag/toggle', null, { params }),
  deleteTag: (data = {}) => request.delete('/tag/delete', { data }),
  exportTag: (data = {}) => downloadScopedFile('/tag/export', data, 'tag-export.xlsx'),
  importTags: (data) => request.post('/tag/import', data),
  // banners
  getBannerList: (params = {}) => request.get('/banner/list', { params }),
  getBannerById: (params = {}) => request.get('/banner/get', { params }),
  createBanner: (data = {}) => request.post('/banner/create', data),
  updateBanner: (data = {}) => request.post('/banner/update', data),
  deleteBanner: (params = {}) => request.delete('/banner/delete', { params }),
  // contacts
  getContactList: (params = {}) => request.get('/contact/list', { params }),
  getContactById: (params = {}) => request.get('/contact/get', { params }),
  createContact: (data = {}) => request.post('/contact/create', data),
  updateContact: (data = {}) => request.post('/contact/update', data),
  deleteContact: (params = {}) => request.delete('/contact/delete', { params }),
  getActiveBanners: (params = {}) => request.get('/base/banners', { params, noNeedToken: true }),
  getActiveContacts: (params = {}) => request.get('/base/contacts', { params, noNeedToken: true }),
  // products
  getProductList: (params = {}) => request.get('/product/list', { params }),
  getProductById: (params = {}) => request.get('/product/get', { params }),
  createProduct: (data = {}) => request.post('/product/create', data),
  updateProduct: (data = {}) => request.post('/product/update', data),
  deleteProduct: (data = {}) => request.delete('/product/delete', { data }),
  exportProduct: (data = {}) => downloadScopedFile('/product/export', data, 'product-export.xlsx'),
  initProductImportUpload: (data = {}) => request.post('/product/import/upload-init', data),
  uploadProductImportChunk: (data) => request.post('/product/import/upload-chunk', data),
  getProductImportUploadStatus: (params = {}) => request.get('/product/import/upload-status', { params }),
  completeProductImportUpload: (data = {}) => request.post('/product/import/upload-complete', data),
  getProductImportTasks: (params = {}) => request.get('/product/import/tasks', { params }),
  getProductImportTask: (params = {}) => request.get('/product/import/task', { params }),
  getProductImportTaskItems: (params = {}) => request.get('/product/import/task/items', { params }),
  cancelProductImportTask: (data = {}) => request.post('/product/import/task/cancel', data),
  retryProductImportTask: (data = {}) => request.post('/product/import/task/retry', data),
  downloadProductImportTemplate: () =>
    downloadScopedGetFile('/product/import/template', 'product-import-template.xlsx'),
  downloadProductImportExample: () =>
    downloadScopedGetFile('/product/import/example', 'product-import-example.zip'),
  downloadProductImportErrors: (taskId) =>
    downloadScopedGetFile(
      `/product/import/task/errors?task_id=${taskId}`,
      `product-import-errors-${taskId}.xlsx`
    ),
  getCatalog: (params = {}) => request.get('/base/catalog', { params, noNeedToken: true }),
  getCatalogProduct: (productId) =>
    request.get(`/base/catalog/products/${productId}`, { noNeedToken: true }),
  // auditlog
  getAuditLogList: (params = {}) => request.get('/auditlog/list', { params }),
  // stats
  getSiteVisitStatsList: (params = {}) => request.get('/stats/site-visit/list', { params }),
  getProductClickStatsList: (params = {}) => request.get('/stats/product-click/list', { params }),
  getBrandSearchStatsList: (params = {}) => request.get('/stats/brand-search/list', { params }),
  getBannerClickStatsList: (params = {}) => request.get('/stats/banner-click/list', { params }),
}
