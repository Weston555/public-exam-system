<template>
  <div class="common-layout">
    <el-container class="layout-container">
      <el-aside width="220px" class="aside">
        <div class="logo-box">
          <el-icon class="logo-icon"><Platform /></el-icon>
          <span>公考进阶系统</span>
        </div>
        <el-menu
          default-active="/home"
          router
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          class="el-menu-vertical"
        >
          <el-menu-item index="/home">
            <el-icon><HomeFilled /></el-icon>
            <span>首页概览</span>
          </el-menu-item>
          <el-menu-item index="/plan">
            <el-icon><Guide /></el-icon>
            <span>学习路径推荐</span>
          </el-menu-item>
          <el-menu-item index="/practice">
            <el-icon><EditPen /></el-icon>
            <span>针对性练习</span>
          </el-menu-item>
          <el-menu-item index="/diagnostic">
            <el-icon><DataAnalysis /></el-icon>
            <span>基线诊断</span>
          </el-menu-item>
          <el-menu-item index="/wrong">
            <el-icon><DocumentDelete /></el-icon>
            <span>错题本</span>
          </el-menu-item>
          <el-menu-item index="/mock">
            <el-icon><Trophy /></el-icon>
            <span>模拟考试</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header class="header">
          <div class="breadcrumb">个性化学习路径推荐系统 - 学员端</div>
          <div class="user-area">
            <el-avatar :size="30" style="background: #409EFF">郭</el-avatar>
            <span class="username">郭东凯 (软件24230)</span>
          </div>
        </el-header>

        <el-main class="main-content">
          <router-view /> </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<style scoped>
.layout-container { height: 100vh; }
.aside { background-color: #304156; color: white; display: flex; flex-direction: column; }
.logo-box { height: 60px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; border-bottom: 1px solid #1f2d3d; }
.logo-icon { margin-right: 8px; }
.el-menu-vertical { border-right: none; }
.header { background-color: #fff; border-bottom: 1px solid #dcdfe6; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; }
.breadcrumb { font-size: 16px; font-weight: 500; color: #303133; }
.user-area { display: flex; align-items: center; cursor: pointer; }
.username { margin-left: 10px; font-size: 14px; color: #606266; }
.main-content { background-color: #f0f2f5; padding: 20px; }
</style>