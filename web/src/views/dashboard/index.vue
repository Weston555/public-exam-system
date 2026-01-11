<template>
  <div class="dashboard-view">
    <BannerCarousel />

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

      <!-- 行测五模块掌握度雷达图 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
          <el-card>
            <template #header>
              <div class="header-row">
                <h4>行测五模块掌握度雷达图</h4>
                <el-text type="info">展示行测五个模块的掌握情况</el-text>
              </div>
            </template>
            <v-chart :option="radarOption" autoresize style="height:400px" v-if="radarOption"></v-chart>
            <div v-else>暂无掌握度数据</div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth'
import BannerCarousel from '../../components/BannerCarousel.vue'
import { use } from 'echarts/core'
import VChart from 'vue-echarts'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, RadarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent, RadarComponent } from 'echarts/components'

use([CanvasRenderer, LineChart, BarChart, RadarChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, RadarComponent])

const authStore = useAuthStore()
const overview = ref({ plan_completion_rate: 0, avg_mastery: 0, wrong_due_count: 0, last_score: null })
const scoreOption = ref(null)
const masteryOption = ref(null)
const radarOption = ref(null)

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

const loadKnowledgeState = async () => {
  try {
    // 优先调用新的模块掌握度API
    let res = await authStore.api.get('/analytics/student/module-mastery?subject=XINGCE')
    let items = res.data.items || []

    if (!items.length) {
      // 如果新接口没有数据，fallback到旧接口
      console.warn('新模块掌握度接口无数据，尝试fallback到旧接口')
      res = await authStore.api.get('/analytics/student/knowledge-state?limit=6')
      items = res.data.items || []
    }

    if (items.length) {
      // 雷达图配置
      radarOption.value = {
        title: {
          text: '行测五模块掌握度雷达图',
          left: 'center'
        },
        tooltip: {
          trigger: 'item',
          formatter: function (params) {
            return `${params.name}: ${params.value}%`
          }
        },
        radar: {
          // 固定为5个模块维度
          indicator: [
            { name: '常识判断', max: 100 },
            { name: '言语理解与表达', max: 100 },
            { name: '数量关系', max: 100 },
            { name: '判断推理', max: 100 },
            { name: '资料分析', max: 100 }
          ],
          center: ['50%', '50%'],
          radius: '60%'
        },
        series: [{
          name: '掌握度',
          type: 'radar',
          data: [{
            value: items.length === 5 ? items.map(item => item.mastery) : [0, 0, 0, 0, 0], // 确保5个值
            name: '掌握度',
            areaStyle: {
              opacity: 0.3
            },
            lineStyle: {
              width: 2
            }
          }]
        }]
      }
    }
  } catch (e) {
    // 接口失败时显示错误提示
    ElMessage.error('获取模块掌握度数据失败')
    console.error('loadKnowledgeState error:', e)
  }
}

onMounted(async () => {
  await loadOverview()
  await loadScoreTrend()
  await loadMasteryTop()
  await loadKnowledgeState()
})
</script>

<style scoped>
.dashboard-view { max-width: 1000px; margin: 20px auto; }
.dashboard-card { margin: 0 auto; }
.metric-title { color: #606266; font-size: 14px; }
.metric-value { font-size: 28px; font-weight: 700; margin-top: 8px; }
</style>


