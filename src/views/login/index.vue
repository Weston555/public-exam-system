<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2 class="login-title">公考进阶系统登录</h2>
      <el-form label-position="top" :model="form" @keyup.enter="handleLogin">
        <el-form-item label="账号">
          <el-input v-model="form.account" placeholder="请输入学号或管理员账号" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="登录身份">
          <el-radio-group v-model="form.role">
            <el-radio-button label="student">学员</el-radio-button>
            <el-radio-button label="admin">管理员</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-button type="primary" style="width: 100%" @click="handleLogin">登录</el-button>
        <div class="extra-row">
          <span>还没有账号？</span>
          <el-button link type="primary" @click="goRegister">前往注册</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = reactive({
  account: '',
  password: '',
  role: 'student'
})

const handleLogin = async () => {
  try {
    await authStore.login({
      account: form.account,
      password: form.password,
      userRole: form.role
    })

    const redirect = route.query.redirect
    if (redirect) {
      router.push(String(redirect))
    }
  } catch (e) {
    ElMessage.error(e.message || '登录失败，请重试')
  }
}

const goRegister = () => {
  router.push('/register')
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: radial-gradient(circle at top, #3a8ee6, #1f2d3d);
}
.login-card {
  width: 400px;
}
.login-title {
  text-align: center;
  margin-bottom: 12px;
}
.extra-row {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  font-size: 13px;
  color: #909399;
}
</style>