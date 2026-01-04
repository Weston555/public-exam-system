<template>
  <div class="diagnostic-page">
    <el-card class="diagnostic-card">
      <template #header>
        <div class="card-header">
          <h3>基线诊断</h3>
          <el-text type="info">评估您的当前能力水平</el-text>
        </div>
      </template>

      <!-- 未开始状态 -->
      <div v-if="!examData" class="start-section">
        <el-empty description="开始基线诊断，了解您的学习起点">
          <el-button type="primary" @click="startDiagnostic" :loading="loading">
            开始诊断
          </el-button>
        </el-empty>
      </div>

      <!-- 答题状态 -->
      <div v-else-if="!result" class="exam-section">
        <div class="exam-header">
          <h4>{{ examData.exam.title }}</h4>
          <el-progress
            :percentage="progressPercent"
            :show-text="false"
            class="progress-bar"
          />
          <span class="progress-text">{{ currentQuestionIndex + 1 }} / {{ examData.questions.length }}</span>
        </div>

        <div class="question-content">
          <div class="question-item">
            <h5>{{ currentQuestion.question.stem }}</h5>

            <!-- 单选题 -->
            <el-radio-group
              v-if="currentQuestion.question.type === 'SINGLE'"
              v-model="currentAnswer"
              class="options-group"
            >
              <el-radio
                v-for="(option, index) in currentQuestion.question.options_json"
                :key="index"
                :label="option"
                class="option-item"
              >
                {{ option }}
              </el-radio>
            </el-radio-group>

            <!-- 多选题 -->
            <el-checkbox-group
              v-if="currentQuestion.question.type === 'MULTI'"
              v-model="currentAnswer"
              class="options-group"
            >
              <el-checkbox
                v-for="(option, index) in currentQuestion.question.options_json"
                :key="index"
                :label="option"
                class="option-item"
              >
                {{ option }}
              </el-checkbox>
            </el-checkbox-group>

            <!-- 判断题 -->
            <el-radio-group
              v-if="currentQuestion.question.type === 'JUDGE'"
              v-model="currentAnswer"
              class="options-group"
            >
              <el-radio label="T" class="option-item">正确</el-radio>
              <el-radio label="F" class="option-item">错误</el-radio>
            </el-radio-group>

            <!-- 填空题 -->
            <el-input
              v-if="currentQuestion.question.type === 'FILL'"
              v-model="currentAnswer"
              placeholder="请输入答案"
              class="fill-input"
            />
          </div>
        </div>

        <div class="action-buttons">
          <el-button
            v-if="currentQuestionIndex > 0"
            @click="previousQuestion"
          >
            上一题
          </el-button>

          <el-button
            v-if="currentQuestionIndex < examData.questions.length - 1"
            type="primary"
            @click="nextQuestion"
            :disabled="!currentAnswer"
          >
            下一题
          </el-button>

          <el-button
            v-else
            type="success"
            @click="submitExam"
            :loading="submitting"
          >
            提交诊断
          </el-button>
        </div>
      </div>

      <!-- 结果状态 -->
      <div v-else class="result-section">
        <el-alert
          title="诊断完成！"
          type="success"
          :closable="false"
          class="result-alert"
        />

        <div class="result-content">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-card class="score-card">
                <h4>总分：{{ result.total_score }} / {{ result.total_questions * 2 }}</h4>
                <p>正确率：{{ Math.round(result.total_score / (result.total_questions * 2) * 100) }}%</p>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card class="weak-points-card">
                <h4>诊断结果</h4>
                <p>您已完成基线诊断，系统将基于此结果生成个性化学习计划。</p>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <div class="result-actions">
          <el-button type="primary" @click="$router.push('/plan')">
            生成学习计划
          </el-button>
          <el-button @click="restartDiagnostic">
            重新诊断
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()

const loading = ref(false)
const submitting = ref(false)
const examData = ref(null)
const result = ref(null)
const currentQuestionIndex = ref(0)
const answers = ref([])
const startTime = ref(null)
const currentAnswer = ref('')

const progressPercent = computed(() => {
  if (!examData.value) return 0
  return Math.round((currentQuestionIndex.value + 1) / examData.value.questions.length * 100)
})

const currentQuestion = computed(() => {
  if (!examData.value || !examData.value.questions[currentQuestionIndex.value]) return null
  return examData.value.questions[currentQuestionIndex.value]
})

const startDiagnostic = async () => {
  loading.value = true
  try {
    // 获取诊断考试
    const examResponse = await authStore.api.get('/exams/?category=DIAGNOSTIC')
    const diagnosticExams = examResponse.data.items

    if (diagnosticExams.length === 0) {
      ElMessage.error('暂无可用的诊断考试，请联系管理员')
      return
    }

    const examId = diagnosticExams[0].id

    // 开始考试
    const response = await authStore.api.post(`/exams/${examId}/start`)
    examData.value = response.data
    currentQuestionIndex.value = 0
    answers.value = new Array(examData.value.questions.length).fill('')
    startTime.value = Date.now()

    ElMessage.success('诊断考试开始')
  } catch (error) {
    console.error('Start diagnostic error:', error)
    ElMessage.error(error.response?.data?.detail || '开始诊断失败')
  } finally {
    loading.value = false
  }
}

const nextQuestion = async () => {
  if (!currentAnswer.value) {
    ElMessage.warning('请先答题')
    return
  }

  // 提交当前答案
  const timeSpent = Math.floor((Date.now() - startTime.value) / 1000)
  try {
    await authStore.api.post(`/attempts/${examData.value.attempt_id}/answer`, {
      question_id: currentQuestion.value.question.id,
      answer: currentAnswer.value,
      time_spent_seconds: timeSpent
    })
  } catch (error) {
    console.error('Submit answer error:', error)
    // 不阻止继续，允许继续答题
  }

  // 保存答案到本地
  answers.value[currentQuestionIndex.value] = currentAnswer.value

  if (currentQuestionIndex.value < examData.value.questions.length - 1) {
    currentQuestionIndex.value++
    currentAnswer.value = answers.value[currentQuestionIndex.value] || ''
    startTime.value = Date.now()
  }
}

const previousQuestion = () => {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value--
    currentAnswer.value = answers.value[currentQuestionIndex.value] || ''
    startTime.value = Date.now()
  }
}

const submitExam = async () => {
  if (!currentAnswer.value) {
    ElMessage.warning('请先答题')
    return
  }

  // 提交最后一题答案
  const timeSpent = Math.floor((Date.now() - startTime.value) / 1000)
  try {
    await authStore.api.post(`/attempts/${examData.value.attempt_id}/answer`, {
      question_id: currentQuestion.value.question.id,
      answer: currentAnswer.value,
      time_spent_seconds: timeSpent
    })
  } catch (error) {
    console.error('Submit final answer error:', error)
  }

  // 提交考试
  submitting.value = true
  try {
    const response = await authStore.api.post(`/attempts/${examData.value.attempt_id}/submit`)
    result.value = response.data

    ElMessage.success('诊断完成！')
  } catch (error) {
    console.error('Submit exam error:', error)
    ElMessage.error(error.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

const restartDiagnostic = () => {
  examData.value = null
  result.value = null
  currentQuestionIndex.value = 0
  answers.value = []
  currentAnswer.value = ''
}
</script>

<style scoped>
.diagnostic-page {
  padding: 20px;
}

.diagnostic-card {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.start-section {
  text-align: center;
  padding: 40px 0;
}

.exam-section {
  max-width: 700px;
  margin: 0 auto;
}

.exam-header {
  margin-bottom: 20px;
}

.progress-bar {
  margin: 10px 0;
}

.progress-text {
  font-size: 14px;
  color: #666;
}

.question-content {
  margin: 30px 0;
}

.question-item h5 {
  margin-bottom: 20px;
  line-height: 1.6;
}

.options-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  transition: all 0.3s;
}

.option-item:hover {
  border-color: #409eff;
}

.fill-input {
  max-width: 300px;
}

.action-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 30px;
}

.result-section {
  text-align: center;
}

.result-alert {
  margin-bottom: 30px;
}

.result-content {
  margin: 30px 0;
}

.score-card, .weak-points-card {
  text-align: left;
}

.result-actions {
  margin-top: 30px;
}

.result-actions .el-button {
  margin: 0 10px;
}
</style>
