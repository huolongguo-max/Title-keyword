import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

// 懒加载页面视图
const UploadView = () => import('@/views/UploadView.vue')
const KeywordsView = () => import('@/views/KeywordsView.vue')
const RiskView = () => import('@/views/RiskView.vue')
const GenerateView = () => import('@/views/GenerateView.vue')
const OptimizeView = () => import('@/views/OptimizeView.vue')

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/upload',
  },
  {
    path: '/upload',
    name: 'upload',
    component: UploadView,
    meta: { title: '上传解析' },
  },
  {
    path: '/keywords',
    name: 'keywords',
    component: KeywordsView,
    meta: { title: '词池分类' },
  },
  {
    path: '/risk',
    name: 'risk',
    component: RiskView,
    meta: { title: '风险检测' },
  },
  {
    path: '/generate',
    name: 'generate',
    component: GenerateView,
    meta: { title: '标题生成' },
  },
  {
    path: '/optimize',
    name: 'optimize',
    component: OptimizeView,
    meta: { title: '批量优化' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
