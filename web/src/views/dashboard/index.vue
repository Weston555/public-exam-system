<template>
  <el-card class="dashboard-card">
    <template #header>
      <div class="header-row">
        <h3>学习仪表板</h3>
        <el-text type="info">查看学习进度与成绩趋势</el-text>
      </div>
    </template>

    <div class="metrics">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card>
            <div class="metric-title">计划完成率</div>
            <div class="metric-value">{{ overview.plan_completion_rate }}%</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card>
            <div class="metric-title">平均掌握度</div>
            <div class="metric-value">{{ overview.avg_mastery }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card>
            <div class="metric-title">到期错题</div>
            <div class="metric-value">{{ overview.wrong_due_count }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card>
            <div class="metric-title">最近成绩</div>
            <div class="metric-value">{{ overview.last_score ?? '-' }}</div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div class="charts">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card>
            <v-chart :option="scoreOption" autoresize style="height:300px" v-if="scoreOption"></v-chart>
            <div v-else>暂无成绩数据</div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <v-chart :option="masteryOption" autoresize style="height:300px" v-if="masteryOption"></v-chart>
            <div v-else>暂无掌握度数据</div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { use } from 'echarts/core'
import VChart from 'vue-echarts'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'

use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

const authStore = useAuthStore()
const overview = ref({ plan_completion_rate: 0, avg_mastery: 0, wrong_due_count: 0, last_score: null })
const scoreOption = ref(null)
const masteryOption = ref(null)

const loadOverview = async () => {
  try {
    const res = await authStore.api.get('/analytics/student/overview')
    overview.value = res.data
  } catch (e) {}
}

const loadScoreTrend = async () => {
  try {
    const res = await authStore.api.get('/analytics/student/score-trend?limit=10')
    const items = res.data.items || []
    if (items.length) {
      scoreOption.value = {
        title: { text: '成绩趋势' },
        tooltip: {},
        xAxis: { type: 'category', data: items.map(i => i.submitted_at) },
        yAxis: { type: 'value' },
        series: [{ data: items.map(i => i.total_score), type: 'line', smooth: true }]
      }
    }
  } catch (e) {}
}

const loadMasteryTop = async () => {
  try {
    const res = await authStore.api.get('/analytics/student/mastery-top?limit=10')
    const items = res.data.items || []
    if (items.length) {
      masteryOption.value = {
        title: { text: '薄弱知识点' },
        tooltip: {},
        xAxis: { type: 'category', data: items.map(i => i.name) },
        yAxis: { type: 'value' },
        series: [{ data: items.map(i => i.mastery), type: 'bar' }]
      }
    }
  } catch (e) {}
}

onMounted(async () => {
  await loadOverview()
  await loadScoreTrend()
  await loadMasteryTop()
})
</script>

<style scoped>
.dashboard-card { max-width: 1000px; margin: 20px auto; }
.metric-title { color: #606266; font-size: 14px; }
.metric-value { font-size: 28px; font-weight: 700; margin-top: 8px; }
</style>


