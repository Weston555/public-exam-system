import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layout/MainLayout.vue'
import AdminLayout from '../layout/AdminLayout.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout, // 学员端主布局
      redirect: '/home',
      children: [
        {
          path: 'home',
          name: 'Home',
          component: () => import('../views/dashboard/index.vue'),
          meta: { title: '首页概览', requiresAuth: true, role: 'student' }
        },
        {
          path: 'plan',
          name: 'Plan',
          component: () => import('../views/plan/index.vue'),
          meta: { title: '学习路径', requiresAuth: true, role: 'student' }
        },
        {
          path: 'diagnostic',
          name: 'Diagnostic',
          component: () => import('../views/diagnostic/index.vue'),
          meta: { title: '基线诊断', requiresAuth: true, role: 'student' }
        }
        ,
        {
          path: 'practice',
          name: 'Practice',
          component: () => import('../views/practice/index.vue'),
          meta: { title: '专项练习', requiresAuth: true, role: 'student' }
        }
        ,
        {
          path: 'wrong',
          name: 'Wrong',
          component: () => import('../views/wrong/index.vue'),
          meta: { title: '错题本', requiresAuth: true, role: 'student' }
        }
      ]
    },
    {
      path: '/admin',
      component: AdminLayout, // 管理员端布局
      meta: { requiresAuth: true, role: 'admin' },
      children: [
        {
          path: '',
          name: 'AdminDashboard',
          component: () => import('../views/admin/dashboard.vue'),
          meta: { title: '数据总览', requiresAuth: true, role: 'admin' }
        },
        {
          path: 'syllabus',
          name: 'AdminSyllabus',
          component: () => import('../views/admin/syllabus.vue'),
          meta: { title: '考试大纲管理', requiresAuth: true, role: 'admin' }
        },
        {
          path: 'knowledge',
          name: 'AdminKnowledge',
          component: () => import('../views/admin/knowledge.vue'),
          meta: { title: '知识点树管理', requiresAuth: true, role: 'admin' }
        },
        {
          path: 'questions',
          name: 'AdminQuestions',
          component: () => import('../views/admin/questions.vue'),
          meta: { title: '题库与资源', requiresAuth: true, role: 'admin' }
        },
        {
          path: 'strategy',
          name: 'AdminStrategy',
          component: () => import('../views/admin/strategy.vue'),
          meta: { title: '推荐策略配置', requiresAuth: true, role: 'admin' }
        },
        {
          path: 'users',
          name: 'AdminUsers',
          component: () => import('../views/admin/users.vue'),
          meta: { title: '用户与权限', requiresAuth: true, role: 'admin' }
        }
      ]
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/login/index.vue')
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('../views/register/index.vue')
    }
  ]
})

// 简单路由守卫：鉴权 + 角色控制
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (!to.meta.requiresAuth) {
    return next()
  }

  if (!authStore.isAuthenticated) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  if (to.meta.role && authStore.role !== to.meta.role) {
    // 角色不匹配时，根据当前角色重定向
    if (authStore.role === 'admin') {
      return next('/admin')
    }
    return next('/home')
  }

  next()
})

export default router