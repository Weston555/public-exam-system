<template>
  <div class="plan-page">
    <el-card class="plan-card">
      <template #header>
        <div class="card-header">
          <h3>个性化学习计划</h3>
          <el-text type="info">基于您的诊断结果和目标定制的学习路径</el-text>
        </div>
      </template>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-section">
        <el-skeleton :loading="loading" animated>
          <template #template>
            <el-skeleton-item variant="text" style="width: 200px; margin-bottom: 20px;" />
            <el-skeleton-item variant="rect" style="height: 100px;" />
          </template>
        </el-skeleton>
      </div>

      <!-- 无计划状态 -->
      <div v-else-if="!activePlan" class="no-plan-section">
        <el-empty description="暂无学习计划">
          <el-button type="primary" @click="generatePlan" :loading="generating">
            生成学习计划
          </el-button>
        </el-empty>
      </div>

      <!-- 学习计划内容 -->
      <div v-else class="plan-content">
        <!-- 计划概览 -->
        <div class="plan-overview">
          <el-row :gutter="20">
            <el-col :span="6">
              <el-statistic
                title="计划天数"
                :value="planDays"
                suffix="天"
                class="overview-stat"
              />
            </el-col>
            <el-col :span="6">
              <el-statistic
                title="每日学习"
                :value="activePlan.goal.daily_minutes"
                suffix="分钟"
                class="overview-stat"
              />
            </el-col>
            <el-col :span="6">
              <el-statistic
                title="目标分数"
                :value="activePlan.goal.target_score || '未设置'"
                class="overview-stat"
              />
            </el-col>
            <el-col :span="6">
              <el-statistic
                title="考试日期"
                :value="formatDate(activePlan.goal.exam_date)"
                class="overview-stat"
              />
            </el-col>
          </el-row>
        </div>

        <!-- 学习进度 -->
        <div class="plan-progress">
          <h4>学习进度</h4>
          <el-progress
            :percentage="completionRate"
            :show-text="true"
            :stroke-width="20"
            status="success"
            class="progress-bar"
          />
          <div class="progress-stats">
            <span>已完成 {{ completedItems }} / {{ totalItems }} 个任务</span>
          </div>
        </div>

        <!-- 每日计划 -->
        <div class="daily-plans">
          <h4>学习计划</h4>

          <el-timeline>
            <el-timeline-item
              v-for="(items, dateStr) in sortedDates"
              :key="dateStr"
              :timestamp="formatDate(dateStr)"
              placement="top"
            >
              <el-card class="day-card" shadow="hover">
                <template #header>
                  <div class="day-header">
                    <span class="day-title">{{ getDayTitle(dateStr) }}</span>
                    <el-tag
                      :type="getDayStatus(dateStr)"
                      size="small"
                    >
                      {{ getDayStatusText(dateStr) }}
                    </el-tag>
                  </div>
                </template>

                <div class="day-items">
                  <div
                    v-for="item in activePlan.items_by_date[dateStr]"
                    :key="item.id"
                    class="plan-item"
                    :class="{ 'completed': item.status === 'DONE', 'skipped': item.status === 'SKIPPED' }"
                  >
                    <div class="item-header">
                      <div class="item-info">
                        <el-tag
                          :type="getItemTypeColor(item.type)"
                          size="small"
                          class="item-type"
                        >
                          {{ getItemTypeText(item.type) }}
                        </el-tag>
                        <span class="item-title">{{ item.title }}</span>
                      </div>
                      <div class="item-actions">
                        <el-tag size="small" type="info">
                          {{ item.expected_minutes }}分钟
                        </el-tag>
                        <el-button
                          v-if="item.status === 'TODO' && (item.type === 'PRACTICE' || item.type === 'REVIEW')"
                          type="primary"
                          size="small"
                          @click="startItem(item)"
                          :loading="startingItem === item.id"
                        >
                          {{ item.type === 'PRACTICE' ? '开始练习' : '开始复习' }}
                        </el-button>
                        <el-button
                          v-if="item.status === 'TODO'"
                          type="success"
                          size="small"
                          @click="completeItem(item.id)"
                          :loading="completingItem === item.id"
                        >
                          完成
                        </el-button>
                        <el-button
                          v-if="item.status === 'TODO'"
                          type="warning"
                          size="small"
                          @click="skipItem(item.id)"
                          :loading="completingItem === item.id"
                        >
                          跳过
                        </el-button>
                        <el-tag
                          v-if="item.status === 'DONE'"
                          type="success"
                          size="small"
                        >
                          已完成
                        </el-tag>
                        <el-tag
                          v-if="item.status === 'SKIPPED'"
                          type="warning"
                          size="small"
                        >
                          已跳过
                        </el-tag>
                      </div>
                    </div>

                    <!-- 推荐理由 -->
                    <div v-if="item.reason" class="item-reason">
                      <el-text size="small" type="info">
                        推荐理由：{{ item.reason.explanation || '系统智能推荐' }}
                      </el-text>
                    </div>

                    <!-- 完成时间 -->
                    <div v-if="item.completed_at" class="item-completed">
                      <el-text size="small" type="success">
                        完成时间：{{ formatDateTime(item.completed_at) }}
                      </el-text>
                    </div>
                  </div>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </div>

        <!-- 重新生成计划 -->
        <div class="regenerate-section">
          <el-alert
            title="计划调整"
            type="info"
            :closable="false"
            show-icon
          >
            <template #description>
              如果学习情况发生变化，可以重新生成学习计划
            </template>
          </el-alert>
          <div class="regenerate-actions">
            <el-button @click="regeneratePlan" :loading="generating">
              重新生成计划
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const loading = ref(true)
const generating = ref(false)
const completingItem = ref(null)
const startingItem = ref(null)
const activePlan = ref(null)

const sortedDates = computed(() => {
  if (!activePlan.value?.items_by_date) return []

  return Object.keys(activePlan.value.items_by_date).sort()
})

const planDays = computed(() => {
  if (!activePlan.value) return 0
  const start = new Date(activePlan.value.start_date)
  const end = new Date(activePlan.value.end_date)
  return Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1
})

const totalItems = computed(() => {
  if (!activePlan.value?.items_by_date) return 0
  return Object.values(activePlan.value.items_by_date).reduce((sum, items) => sum + items.length, 0)
})

const completedItems = computed(() => {
  if (!activePlan.value?.items_by_date) return 0
  return Object.values(activePlan.value.items_by_date).reduce((sum, items) => {
    return sum + items.filter(item => item.status === 'DONE').length
  }, 0)
})

const completionRate = computed(() => {
  if (totalItems.value === 0) return 0
  return Math.round((completedItems.value / totalItems.value) * 100)
})

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
}

const formatDateTime = (dateTimeStr) => {
  const date = new Date(dateTimeStr)
  return date.toLocaleString('zh-CN')
}

const getDayTitle = (dateStr) => {
  const date = new Date(dateStr)
  const today = new Date()
  const diffDays = Math.floor((date - today) / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return '今天'
  if (diffDays === 1) return '明天'
  if (diffDays === -1) return '昨天'
  if (diffDays > 0) return `${diffDays}天后`
  return `${Math.abs(diffDays)}天前`
}

const getDayStatus = (dateStr) => {
  const items = activePlan.value.items_by_date[dateStr]
  const completed = items.filter(item => item.status === 'DONE').length
  const total = items.length

  if (completed === total && total > 0) return 'success'
  if (completed > 0) return 'warning'
  return 'info'
}

const getDayStatusText = (dateStr) => {
  const status = getDayStatus(dateStr)
  const map = {
    success: '已完成',
    warning: '进行中',
    info: '未开始'
  }
  return map[status] || '未开始'
}

const getItemTypeColor = (type) => {
  const map = {
    LEARN: 'primary',
    PRACTICE: 'success',
    REVIEW: 'warning',
    MOCK: 'danger'
  }
  return map[type] || 'info'
}

const getItemTypeText = (type) => {
  const map = {
    LEARN: '学习',
    PRACTICE: '练习',
    REVIEW: '复习',
    MOCK: '模拟'
  }
  return map[type] || type
}

const loadActivePlan = async () => {
  try {
    loading.value = true
    const response = await authStore.api.get('/plans/active')
    activePlan.value = response.data
  } catch (error) {
    if (error.response?.status !== 404) {
      ElMessage.error(error.response?.data?.detail || '加载学习计划失败')
    }
    activePlan.value = null
  } finally {
    loading.value = false
  }
}

const generatePlan = async () => {
  try {
    // 在生成计划前检查是否已设置学习目标
    const goalResponse = await authStore.api.get('/goals/me')
    if (!goalResponse.data) {
      await ElMessageBox.confirm(
        '您还没有设置学习目标，请先设置学习目标后再生成计划。',
        '需要设置学习目标',
        {
          confirmButtonText: '去设置',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )
      // 跳转到目标设置页面
      await router.push('/goal')
      return
    }

    generating.value = true
    const response = await authStore.api.post('/plans/generate', { days: 14 })
    ElMessage.success(response.data.message)
    await loadActivePlan()
  } catch (error) {
    if (error === 'cancel') {
      return // 用户取消
    }
    ElMessage.error(error.response?.data?.detail || '生成学习计划失败')
  } finally {
    generating.value = false
  }
}

const regeneratePlan = async () => {
  try {
    await ElMessageBox.confirm(
      '重新生成计划将覆盖当前的进度，确定要继续吗？',
      '确认重新生成',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    generating.value = true
    const response = await authStore.api.post('/plans/generate', { days: 14 })
    ElMessage.success(response.data.message)
    await loadActivePlan()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '重新生成学习计划失败')
    }
  } finally {
    generating.value = false
  }
}

const completeItem = async (itemId) => {
  try {
    completingItem.value = itemId
    await authStore.api.patch(`/plans/items/${itemId}`, { status: 'DONE' })
    ElMessage.success('任务已完成！')

    // 重新加载计划数据
    await loadActivePlan()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '更新任务状态失败')
  } finally {
    completingItem.value = null
  }
}

const skipItem = async (itemId) => {
  try {
    completingItem.value = itemId
    await authStore.api.patch(`/plans/items/${itemId}`, { status: 'SKIPPED' })
    ElMessage.success('任务已跳过')

    // 重新加载计划数据
    await loadActivePlan()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '更新任务状态失败')
  } finally {
    completingItem.value = null
  }
}

const startItem = async (item) => {
  try {
    startingItem.value = item.id

    let genResponse

    if (item.type === 'PRACTICE') {
      // 生成练习试卷
      genResponse = await authStore.api.post('/practice/generate', {
        knowledge_id: item.knowledge_id,
        count: 10,
        mode: 'ADAPTIVE'
      })
    } else if (item.type === 'REVIEW') {
      // 生成复习试卷
      genResponse = await authStore.api.post('/wrong-questions/review/generate', {
        count: 10
      })
    }

    const examId = genResponse.data.exam_id

    // 开始考试
    const startResponse = await authStore.api.post(`/exams/${examId}/start`)

    ElMessage.success('已进入答题页面')

    // 跳转到答题页面
    await router.push({
      path: '/exam',
      query: { attempt_id: startResponse.data.attempt_id }
    })

  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '开始任务失败')
  } finally {
    startingItem.value = null
  }
}

onMounted(() => {
  loadActivePlan()
})
</script>

<style scoped>
.plan-page {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.plan-card {
  max-width: 1000px;
  margin: 0 auto;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  color: #303133;
}

.loading-section, .no-plan-section {
  padding: 60px 0;
  text-align: center;
}

.plan-content {
  max-width: 900px;
}

.plan-overview {
  margin-bottom: 30px;
}

.overview-stat {
  text-align: center;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.plan-progress {
  margin-bottom: 30px;
}

.plan-progress h4 {
  margin: 0 0 15px 0;
  color: #303133;
}

.progress-bar {
  margin-bottom: 10px;
}

.progress-stats {
  text-align: center;
  color: #606266;
  font-size: 14px;
}

.daily-plans {
  margin-bottom: 30px;
}

.daily-plans h4 {
  margin: 0 0 20px 0;
  color: #303133;
}

.day-card {
  margin-bottom: 15px;
}

.day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.day-title {
  font-weight: 600;
  color: #303133;
}

.day-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.plan-item {
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background-color: #fafafa;
  transition: all 0.3s ease;
}

.plan-item.completed {
  background-color: #f0f9ff;
  border-color: #67c23a;
}

.plan-item.skipped {
  background-color: #fdf6ec;
  border-color: #e6a23c;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.item-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.item-type {
  flex-shrink: 0;
}

.item-title {
  font-weight: 500;
  color: #303133;
  flex: 1;
}

.item-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.item-reason {
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.item-completed {
  margin-top: 8px;
}

.regenerate-section {
  margin-top: 40px;
  padding-top: 30px;
  border-top: 1px solid #ebeef5;
}

.regenerate-actions {
  margin-top: 15px;
  text-align: center;
}

.regenerate-actions .el-button {
  min-width: 140px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .plan-page {
    padding: 10px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .plan-overview .el-col {
    margin-bottom: 15px;
  }

  .item-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .item-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>