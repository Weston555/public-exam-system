<template>
  <div class="common-layout">
    <el-container class="layout-container">
      <el-aside width="220px" class="aside">
        <div class="logo-box">
          <el-icon class="logo-icon"><Management /></el-icon>
          <span>公考进阶 · 管理后台</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          router
          background-color="#001529"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          class="el-menu-vertical"
        >
          <el-menu-item index="/admin">
            <el-icon><DataBoard /></el-icon>
            <span>数据总览</span>
          </el-menu-item>
          <el-menu-item index="/admin/syllabus">
            <el-icon><Collection /></el-icon>
            <span>考试大纲管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/knowledge">
            <el-icon><List /></el-icon>
            <span>知识点树管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/questions">
            <el-icon><Edit /></el-icon>
            <span>题库与资源</span>
          </el-menu-item>
          <el-menu-item index="/admin/strategy">
            <el-icon><Setting /></el-icon>
            <span>推荐策略配置</span>
          </el-menu-item>
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <span>用户与权限</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header class="header">
          <div class="breadcrumb">个性化学习路径推荐系统 - 管理员端</div>
          <div class="user-area">
            <el-button type="text" @click="goStudent">
              <el-icon><SwitchButton /></el-icon>
              切换到学员端
            </el-button>
            <el-divider direction="vertical" />
            <el-button type="text" @click="handleLogout">
              <el-icon><CloseBold /></el-icon>
              退出登录
            </el-button>
          </div>
        </el-header>

        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

const handleLogout = () => {
  authStore.logout()
}

const goStudent = () => {
  router.push('/home')
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}
.aside {
  background-color: #001529;
  color: white;
  display: flex;
  flex-direction: column;
}
.logo-box {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid #0f2438;
}
.logo-icon {
  margin-right: 8px;
}
.el-menu-vertical {
  border-right: none;
}
.header {
  background-color: #fff;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}
.breadcrumb {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}
.user-area {
  display: flex;
  align-items: center;
}
.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>


