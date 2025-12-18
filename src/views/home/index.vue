<template>
  <div class="home-view">
    <el-card class="banner-card" shadow="never">
      <el-carousel trigger="click" height="300px" :interval="5000">
        <el-carousel-item v-for="item in banners" :key="item.id">
          <div class="banner-box" :style="{ background: item.bg }">
            <div class="banner-text">
              <h1>{{ item.title }}</h1>
              <p>{{ item.desc }}</p>
              <el-button type="primary" round v-if="item.btn">{{ item.btn }}</el-button>
            </div>
          </div>
        </el-carousel-item>
      </el-carousel>
    </el-card>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <h3>👋 欢迎回来，开始今天的公考备考吧！</h3>
          <p>当前学习进度：<el-progress :percentage="30" /></p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// 轮播图数据
const banners = ref([
  { 
    id: 1, 
    title: '精准诊断，科学备考', 
    desc: '基于知识点图谱的个性化路径规划', 
    bg: 'linear-gradient(120deg, #84fab0 0%, #8fd3f4 100%)',
    btn: '立即诊断'
  },
  { 
    id: 2, 
    title: '海量真题，智能推送', 
    desc: '覆盖行测、申论核心考点，难度自适应', 
    bg: 'linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%)',
    btn: null
  },
  { 
    id: 3, 
    title: '可视化数据分析', 
    desc: '全方位记录学习轨迹，看见每一分的成长', 
    bg: 'linear-gradient(120deg, #fccb90 0%, #d57eeb 100%)',
    btn: '查看报表'
  }
])
</script>

<style scoped>
.banner-card { border: none; padding: 0; }
.banner-box { height: 100%; display: flex; align-items: center; justify-content: center; color: #fff; text-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.banner-text { text-align: center; }
.banner-text h1 { font-size: 32px; margin-bottom: 10px; }
.banner-text p { font-size: 18px; margin-bottom: 20px; opacity: 0.9; }
</style>