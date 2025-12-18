<template>
  <div class="register-container">
    <el-card class="register-card">
      <h2 class="register-title">公考进阶系统注册</h2>
      <el-form label-position="top" :model="form">
        <el-form-item label="账号">
          <el-input v-model="form.account" placeholder="建议使用学号或工号" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="form.confirmPassword" type="password" placeholder="请再次输入密码" show-password />
        </el-form-item>
        <el-form-item label="注册身份">
          <el-radio-group v-model="form.role">
            <el-radio-button label="student">学员</el-radio-button>
            <el-radio-button label="admin">管理员</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-button type="primary" style="width: 100%" @click="handleRegister">注册并登录</el-button>
        <div class="extra-row">
          <span>已有账号？</span>
          <el-button link type="primary" @click="goLogin">返回登录</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  account: '',
  password: '',
  confirmPassword: '',
  role: 'student'
})

const handleRegister = async () => {
  if (!form.account || !form.password) {
    ElMessage.warning('账号和密码不能为空')
    return
  }
  if (form.password !== form.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }

  // 这里先复用本地 login 逻辑，后续接入后端注册接口后再调整
  try {
    await authStore.login({
      account: form.account,
      password: form.password,
      userRole: form.role
    })
    ElMessage.success('注册成功，已自动登录')
  } catch (e) {
    ElMessage.error(e.message || '注册失败，请重试')
  }
}

const goLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: radial-gradient(circle at top, #67c23a, #1f2d3d);
}
.register-card {
  width: 420px;
}
.register-title {
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


