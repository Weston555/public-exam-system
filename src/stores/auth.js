import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const role = ref(localStorage.getItem('role') || '') // 'student' | 'admin'
  const username = ref(localStorage.getItem('username') || '')

  const isAuthenticated = computed(() => !!token.value)

  const router = useRouter()

  function login({ account, password, userRole }) {
    // TODO: 这里后续可替换为真实后端接口调用
    if (!account || !password) {
      throw new Error('账号和密码不能为空')
    }

    token.value = 'mock-token'
    role.value = userRole
    username.value = account

    localStorage.setItem('token', token.value)
    localStorage.setItem('role', role.value)
    localStorage.setItem('username', username.value)

    // 根据角色跳转不同端
    if (userRole === 'admin') {
      router.push('/admin')
    } else {
      router.push('/home')
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
    logout
  }
})


