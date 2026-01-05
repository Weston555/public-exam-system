<template>
  <div class="goal-page">
    <el-card class="goal-card">
      <template #header>
        <div class="card-header">
          <h3>学习目标设置</h3>
          <el-text type="info">设置您的考试目标，系统将为您制定个性化学习计划</el-text>
        </div>
      </template>

      <div class="goal-form">
        <el-form
          ref="goalFormRef"
          :model="goalForm"
          :rules="rules"
          label-width="120px"
          size="large"
        >
          <el-form-item label="考试日期" prop="exam_date">
            <el-date-picker
              v-model="goalForm.exam_date"
              type="date"
              placeholder="选择考试日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              :disabled-date="disabledDate"
              style="width: 100%"
            />
            <div class="form-tip">
              <el-text size="small" type="info">考试日期必须是未来的日期</el-text>
            </div>
          </el-form-item>

          <el-form-item label="目标分数" prop="target_score">
            <el-input-number
              v-model="goalForm.target_score"
              :min="0"
              :max="150"
              :precision="1"
              placeholder="输入目标分数"
              style="width: 100%"
            />
            <div class="form-tip">
              <el-text size="small" type="info">可选字段，输入您的期望分数（0-150分）</el-text>
            </div>
          </el-form-item>

          <el-form-item label="每日学习时长" prop="daily_minutes">
            <el-input-number
              v-model="goalForm.daily_minutes"
              :min="30"
              :max="240"
              :step="15"
              placeholder="输入每日学习时长"
              style="width: 100%"
            />
            <div class="form-tip">
              <el-text size="small" type="info">建议时长：30-240分钟，默认为60分钟</el-text>
            </div>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              @click="submitGoal"
              :loading="submitting"
              style="width: 120px"
            >
              {{ isEditing ? '更新目标' : '设置目标' }}
            </el-button>
            <el-button @click="resetForm" style="margin-left: 20px">
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 已设置的目标信息 -->
      <div v-if="currentGoal" class="current-goal-info">
        <el-divider>当前学习目标</el-divider>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="考试日期">
            {{ formatDate(currentGoal.exam_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="目标分数">
            {{ currentGoal.target_score ? `${currentGoal.target_score}分` : '未设置' }}
          </el-descriptions-item>
          <el-descriptions-item label="每日学习时长">
            {{ currentGoal.daily_minutes }}分钟
          </el-descriptions-item>
          <el-descriptions-item label="设置时间">
            {{ formatDateTime(currentGoal.created_at) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()

// 表单引用
const goalFormRef = ref(null)

// 表单数据
const goalForm = reactive({
  exam_date: '',
  target_score: null,
  daily_minutes: 60
})

// 表单验证规则
const rules = {
  exam_date: [
    { required: true, message: '请选择考试日期', trigger: 'change' },
    {
      validator: (rule, value, callback) => {
        if (value) {
          const selectedDate = new Date(value)
          const today = new Date()
          today.setHours(0, 0, 0, 0)
          if (selectedDate <= today) {
            callback(new Error('考试日期必须是未来的日期'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  target_score: [
    {
      validator: (rule, value, callback) => {
        if (value !== null && (value < 0 || value > 150)) {
          callback(new Error('目标分数必须在0-150之间'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  daily_minutes: [
    { required: true, message: '请输入每日学习时长', trigger: 'blur' },
    { type: 'number', min: 30, max: 240, message: '学习时长必须在30-240分钟之间', trigger: 'blur' }
  ]
}

// 状态变量
const submitting = ref(false)
const currentGoal = ref(null)
const isEditing = ref(false)

// 日期选择器禁用函数 - 只允许选择未来日期
const disabledDate = (time) => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return time.getTime() < today.getTime()
}

// 格式化日期
const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 格式化日期时间
const formatDateTime = (dateTimeStr) => {
  const date = new Date(dateTimeStr)
  return date.toLocaleString('zh-CN')
}

// 加载当前目标
const loadCurrentGoal = async () => {
  try {
    const response = await authStore.api.get('/goals/me')
    if (response.data) {
      currentGoal.value = response.data
      isEditing.value = true
      // 回填表单
      goalForm.exam_date = response.data.exam_date
      goalForm.target_score = response.data.target_score
      goalForm.daily_minutes = response.data.daily_minutes
    } else {
      currentGoal.value = null
      isEditing.value = false
    }
  } catch (error) {
    console.error('加载目标失败:', error)
    // 如果接口不存在或出错，不影响页面正常使用
    currentGoal.value = null
    isEditing.value = false
  }
}

// 提交表单
const submitGoal = async () => {
  try {
    await goalFormRef.value.validate()

    submitting.value = true

    // 准备提交数据
    const submitData = {
      exam_date: goalForm.exam_date,
      daily_minutes: goalForm.daily_minutes
    }

    if (goalForm.target_score !== null) {
      submitData.target_score = goalForm.target_score
    }

    let response
    if (isEditing.value && currentGoal.value) {
      // 更新现有目标
      response = await authStore.api.put(`/goals/${currentGoal.value.id}`, submitData)
      ElMessage.success('学习目标更新成功！')
    } else {
      // 创建新目标
      response = await authStore.api.post('/goals/', submitData)
      ElMessage.success('学习目标设置成功！')
    }

    // 重新加载目标信息
    await loadCurrentGoal()

  } catch (error) {
    if (error === 'validation_failed') {
      return // 表单验证失败，不显示错误信息
    }
    console.error('保存目标失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败，请重试')
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  goalFormRef.value.resetFields()
  goalForm.daily_minutes = 60 // 重置为默认值
  goalForm.target_score = null
}

// 页面加载时获取当前目标
onMounted(() => {
  loadCurrentGoal()
})
</script>

<style scoped>
.goal-page {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.goal-card {
  max-width: 600px;
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

.goal-form {
  padding: 20px 0;
}

.form-tip {
  margin-top: 5px;
}

.current-goal-info {
  margin-top: 40px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .goal-page {
    padding: 10px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .goal-card {
    margin: 0;
  }
}
</style>
