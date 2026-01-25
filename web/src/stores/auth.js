import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import router from '../router'

// 在store外部创建axios实例，确保始终可用
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 10000
})

// DEMO 模式开关（在 .env.development 中设置 VITE_DEMO_MODE=true）
const DEMO_MODE = (import.meta.env.VITE_DEMO_MODE === 'true') || false

if (DEMO_MODE) {
  // 延迟加载 mock 处理，避免在非浏览器环境报错
  import('../mock/apiMock').then(({ handleMock }) => {
    // 请求拦截：当为 demo 模式时，直接在 response interceptor 上处理 mock
    api.interceptors.request.use((config) => {
      // 标记为 demo 以便 response 拦截器识别
      config.__isDemo = true
      return config
    })

    api.interceptors.response.use(
      (resp) => resp,
      (error) => {
        // 如果是本库发起的 demo 请求，转换为 mock 响应
        const cfg = error.config || {}
        if (cfg.__isDemo) {
          try {
            const mockData = handleMock(cfg)
            return Promise.resolve({ data: mockData, status: 200, config: cfg })
          } catch (e) {
            return Promise.resolve({ data: {}, status: 200, config: cfg })
          }
        }
        return Promise.reject(error)
      }
    )
  })
}
export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const role = ref(localStorage.getItem('role') || '') // 'student' | 'admin'
  const username = ref(localStorage.getItem('username') || '')

  const isAuthenticated = computed(() => !!token.value)

  // 设置axios请求拦截器
  api.interceptors.request.use(
    (config) => {
      if (token.value) {
        config.headers.Authorization = `Bearer ${token.value}`
      }
      return config
    },
    (error) => Promise.reject(error)
  )

  async function login({ account, password, userRole }) {
    try {
      // 将前端选中的角色传给后端，后端会根据该字段创建/更新对应角色的账号
      const response = await api.post('/auth/login', {
        username: account,
        password: password,
        role: userRole ? userRole.toUpperCase() : undefined
      })

      token.value = response.data.access_token
      role.value = response.data.role
      username.value = account

      localStorage.setItem('token', token.value)
      localStorage.setItem('role', role.value)
      localStorage.setItem('username', username.value)

      // 根据角色跳转
      if (role.value === 'admin') {
        router.push('/admin')
      } else {
        router.push('/home')
      }
    } catch (error) {
      if (error.response) {
        throw new Error(error.response.data.detail || '登录失败')
      } else {
        throw new Error('网络错误，请重试')
      }
    }
  }

// 如果在演示模式下，绕过登录：自动写入假 token/role 到 store/localStorage
if (DEMO_MODE) {
  const demoToken = localStorage.getItem('token') || ('demo-token-' + Date.now())
  token.value = demoToken
  role.value = localStorage.getItem('role') || 'student'
  username.value = localStorage.getItem('username') || 'demo_user'
  localStorage.setItem('token', token.value)
  localStorage.setItem('role', role.value)
  localStorage.setItem('username', username.value)
}

  async function register({ username, password, role: userRole }) {
    try {
      await api.post('/auth/register', {
        username,
        password,
        role: userRole.toUpperCase()
      })

      // 注册成功后自动登录
      await login({ account: username, password, userRole })
    } catch (error) {
      if (error.response) {
        throw new Error(error.response.data.detail || '注册失败')
      } else {
        throw new Error('网络错误，请重试')
      }
    }
  }

  function logout() {
    token.value = ''
    role.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('username')
    router.push('/login')
  }

  return {
    token,
    role,
    username,
    isAuthenticated,
    login,
    register,
    logout,
    api // 导出api实例供其他地方使用
  }
})


