<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2 style="text-align: center">公考进阶系统登录</h2>
      <el-form label-position="top">
        <el-form-item label="学号/账号">
          <el-input placeholder="请输入学号" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-button type="primary" style="width: 100%">登录</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #2d3a4b;
}
.login-card { width: 400px; }
</style>