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

    <!-- 学习概览统计卡片 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic
            title="计划完成率"
            :value="overview.plan_completion_rate"
            suffix="%"
            :value-style="{ color: '#409EFF' }"
          />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic
            title="平均掌握度"
            :value="overview.avg_mastery"
            :precision="2"
            suffix="%"
            :value-style="{ color: '#67C23A' }"
          />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic
            title="待复习错题"
            :value="overview.wrong_due_count"
            :value-style="{ color: '#E6A23C' }"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="chart-header">
              <h4>成绩趋势</h4>
              <el-text type="info" size="small">最近10次考试成绩</el-text>
            </div>
          </template>
          <v-chart :option="scoreTrendOption" autoresize style="height: 300px" v-if="scoreTrendOption"></v-chart>
          <div v-else class="no-data">暂无成绩数据</div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="chart-header">
              <h4>知识点掌握度雷达图</h4>
              <el-text type="info" size="small">最薄弱的6个知识点</el-text>
            </div>
          </template>
          <v-chart :option="radarOption" autoresize style="height: 300px" v-if="radarOption"></v-chart>
          <div v-else class="no-data">暂无掌握度数据</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { use } from 'echarts/core'
import VChart from 'vue-echarts'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, RadarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent, RadarComponent } from 'echarts/components'

// 注册 ECharts 组件
use([CanvasRenderer, LineChart, RadarChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, RadarComponent])

const authStore = useAuthStore()

// 数据状态
const overview = ref({
  plan_completion_rate: 0,
  avg_mastery: 0,
  wrong_due_count: 0,
  last_score: null
})
const scoreTrendOption = ref(null)
const radarOption = ref(null)

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

// 加载学习概览数据
const loadOverview = async () => {
  try {
    const response = await authStore.api.get('/analytics/student/overview')
    overview.value = response.data
  } catch (error) {
    console.error('加载概览数据失败:', error)
  }
}

// 加载成绩趋势数据
const loadScoreTrend = async () => {
  try {
    const response = await authStore.api.get('/analytics/student/score-trend?limit=10')
    const items = response.data.items || []
    if (items.length > 0) {
      scoreTrendOption.value = {
        title: {
          text: '成绩趋势',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: items.map(item => {
            const date = new Date(item.submitted_at)
            return date.toLocaleDateString('zh-CN', {
              month: 'short',
              day: 'numeric'
            })
          })
        },
        yAxis: {
          type: 'value',
          name: '分数'
        },
        series: [{
          name: '考试成绩',
          type: 'line',
          data: items.map(item => item.total_score),
          smooth: true,
          lineStyle: {
            width: 3
          },
          itemStyle: {
            color: '#409EFF'
          }
        }]
      }
    }
  } catch (error) {
    console.error('加载成绩趋势失败:', error)
  }
}

// 加载雷达图数据
const loadKnowledgeState = async () => {
  try {
    const response = await authStore.api.get('/analytics/student/knowledge-state?limit=6')
    const items = response.data.items || []
    if (items.length > 0) {
      radarOption.value = {
        title: {
          text: '知识点掌握度',
          left: 'center'
        },
        tooltip: {
          trigger: 'item',
          formatter: function (params) {
            return `${params.name}: ${params.value}%`
          }
        },
        radar: {
          indicator: items.map(item => ({
            name: item.name,
            max: 100
          })),
          center: ['50%', '50%'],
          radius: '60%'
        },
        series: [{
          name: '掌握度',
          type: 'radar',
          data: [{
            value: items.map(item => item.mastery),
            name: '掌握度',
            areaStyle: {
              opacity: 0.3,
              color: '#409EFF'
            },
            lineStyle: {
              width: 2,
              color: '#409EFF'
            },
            itemStyle: {
              color: '#409EFF'
            }
          }]
        }]
      }
    }
  } catch (error) {
    console.error('加载雷达图数据失败:', error)
  }
}

// 页面加载时获取所有数据
onMounted(async () => {
  await Promise.all([
    loadOverview(),
    loadScoreTrend(),
    loadKnowledgeState()
  ])
})
</script>

<style scoped>
.banner-card { border: none; padding: 0; }
.banner-box { height: 100%; display: flex; align-items: center; justify-content: center; color: #fff; text-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.banner-text { text-align: center; }
.banner-text h1 { font-size: 32px; margin-bottom: 10px; }
.banner-text p { font-size: 18px; margin-bottom: 20px; opacity: 0.9; }

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-header h4 {
  margin: 0;
  color: #303133;
}

.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
  color: #909399;
  font-size: 14px;
}

/* 统计卡片样式 */
:deep(.el-statistic__content) {
  font-size: 28px;
  font-weight: 600;
}

:deep(.el-statistic__title) {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}
</style>