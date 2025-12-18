import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layout/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout, // 使用主布局
      redirect: '/home',
      children: [
        {
          path: 'home',
          name: 'Home',
          component: () => import('../views/home/index.vue'),
          meta: { title: '首页概览' }
        },
        {
          path: 'plan',
          name: 'Plan',
          component: () => import('../views/plan/index.vue'),
          meta: { title: '学习路径' } // 对应任务书“学习路径生成”
        }
      ]
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/login/index.vue')
    }
  ]
})

export default router