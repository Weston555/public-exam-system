<template>
  <el-card class="banner-card" shadow="never">
    <el-carousel trigger="click" height="300px" :interval="5000">
      <el-carousel-item v-for="item in banners" :key="item.id">
        <div class="banner-box" :style="{ background: item.bg }">
          <div class="banner-text">
            <h1>{{ item.title }}</h1>
            <p>{{ item.desc }}</p>
            <el-button
              v-if="item.btn"
              type="primary"
              round
              @click="handleClick(item.action)"
            >
              {{ item.btn }}
            </el-button>
          </div>
        </div>
      </el-carousel-item>
    </el-carousel>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const banners = ref([
  {
    id: 1,
    title: '精准诊断，科学备考',
    desc: '基于知识点图谱的个性化路径规划',
    bg: 'linear-gradient(120deg, #84fab0 0%, #8fd3f4 100%)',
    btn: '立即诊断',
    action: 'diagnostic'
  },
  {
    id: 2,
    title: '海量真题，智能推送',
    desc: '覆盖行测、申论核心考点，难度自适应',
    bg: 'linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%)',
    btn: null,
    action: null
  },
  {
    id: 3,
    title: '可视化数据分析',
    desc: '全方位记录学习轨迹，看见每一分的成长',
    bg: 'linear-gradient(120deg, #fccb90 0%, #d57eeb 100%)',
    btn: '查看学习路径',
    action: 'plan'
  }
])

const handleClick = (action) => {
  if (!action) return
  if (action === 'diagnostic') router.push('/diagnostic')
  if (action === 'plan') router.push('/plan')
}
</script>

<style scoped>
.banner-card { border: none; padding: 0; margin-bottom: 16px; }
.banner-box {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.banner-text { text-align: center; padding: 0 12px; }
.banner-text h1 { font-size: 32px; margin-bottom: 10px; }
.banner-text p { font-size: 18px; margin-bottom: 20px; opacity: 0.9; }
</style>
