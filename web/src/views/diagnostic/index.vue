<template>
  <div class="diagnostic-page">
    <el-card class="diagnostic-card">
      <template #header>
        <div class="card-header">
          <h3>基线诊断</h3>
          <el-text type="info">评估您的当前能力水平，生成个性化学习计划</el-text>
        </div>
      </template>

      <!-- 未开始状态 -->
      <div v-if="!examData" class="start-section">
        <el-empty description="开始基线诊断，了解您的学习起点">
          <el-button type="primary" @click="startDiagnostic" :loading="loading" size="large">
            开始诊断
          </el-button>
        </el-empty>
        <div class="tips-section">
          <el-alert
            title="诊断说明"
            type="info"
            :closable="false"
            show-icon
          >
            <ul>
              <li>诊断考试将覆盖所有基础知识点</li>
              <li>预计用时：30-45分钟</li>
              <li>完成后将自动生成您的个性化学习计划</li>
            </ul>
          </el-alert>
        </div>
      </div>

      <!-- 答题状态 -->
      <div v-else-if="!result" class="exam-section">
        <div class="exam-header">
          <div class="exam-info">
            <h4>{{ examData.exam.title }}</h4>
            <div class="exam-meta">
              <el-tag type="info">{{ examData.exam.category === 'DIAGNOSTIC' ? '基线诊断' : '练习考试' }}</el-tag>
              <el-tag type="warning">时长: {{ examData.exam.duration_minutes }}分钟</el-tag>
            </div>
          </div>
          <div class="progress-section">
            <el-progress
              :percentage="progressPercent"
              :show-text="false"
              class="progress-bar"
              status="success"
            />
            <span class="progress-text">{{ currentQuestionIndex + 1 }} / {{ totalQuestions }}</span>
          </div>
        </div>

        <div class="question-content">
          <div class="question-item">
            <div class="question-header">
              <span class="question-type">{{ getQuestionTypeText(currentQuestion.question.type) }}</span>
              <span class="question-score">2分</span>
            </div>
            <h5 class="question-stem" v-html="currentQuestion.question.stem"></h5>

            <!-- 单选题 -->
            <el-radio-group
              v-if="currentQuestion.question.type === 'SINGLE'"
              v-model="currentAnswer"
              class="options-group"
            >
              <el-radio
                v-for="(option, index) in currentQuestion.question.options_json"
                :key="index"
                :label="String.fromCharCode(65 + index)"
                class="option-item"
              >
                <span class="option-label">{{ String.fromCharCode(65 + index) }}.</span>
                <span v-html="option"></span>
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
                :label="String.fromCharCode(65 + index)"
                class="option-item"
              >
                <span class="option-label">{{ String.fromCharCode(65 + index) }}.</span>
                <span v-html="option"></span>
              </el-checkbox>
            </el-checkbox-group>

            <!-- 判断题 -->
            <el-radio-group
              v-if="currentQuestion.question.type === 'JUDGE'"
              v-model="currentAnswer"
              class="options-group"
            >
              <el-radio label="T" class="option-item">
                <span class="option-label">T.</span>
                正确
              </el-radio>
              <el-radio label="F" class="option-item">
                <span class="option-label">F.</span>
                错误
              </el-radio>
            </el-radio-group>

            <!-- 填空题 -->
            <el-input
              v-if="currentQuestion.question.type === 'FILL'"
              v-model="currentAnswer"
              placeholder="请输入答案"
              class="fill-input"
              clearable
            />

            <!-- 简答题 -->
            <el-input
              v-if="currentQuestion.question.type === 'SHORT'"
              v-model="currentAnswer"
              type="textarea"
              placeholder="请输入答案"
              class="short-input"
              :rows="4"
              clearable
            />
          </div>
        </div>

        <div class="action-buttons">
          <el-button
            v-if="currentQuestionIndex > 0"
            @click="previousQuestion"
            :disabled="submitting"
          >
            上一题
          </el-button>

          <el-button
            v-if="currentQuestionIndex < totalQuestions - 1"
            type="primary"
            @click="nextQuestion"
            :disabled="!hasAnswer || submitting"
          >
            下一题
          </el-button>

          <el-button
            v-else
            type="success"
            @click="submitExam"
            :loading="submitting"
            :disabled="!hasAnswer"
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
          show-icon
          class="result-alert"
        />

        <div class="result-content">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-card class="score-card" shadow="hover">
                <div class="score-header">
                  <h4>诊断成绩</h4>
                  <div class="score-display">
                    <span class="score-number">{{ result.total_score }}</span>
                    <span class="score-total">/ {{ totalQuestions * 2 }}</span>
                  </div>
                  <div class="score-meta">
                    正确率：{{ Math.round(result.total_score / (totalQuestions * 2) * 100) }}%
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card class="analysis-card" shadow="hover">
                <h4>能力分析</h4>
                <div class="analysis-content">
                  <div class="analysis-item">
                    <span class="analysis-label">薄弱知识点：</span>
                    <span class="analysis-value">{{ result.weak_points.length }} 个</span>
                  </div>
                  <div class="analysis-item">
                    <span class="analysis-label">建议重点复习：</span>
                    <span class="analysis-value">{{ getWeakPointsText() }}</span>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <div class="result-actions">
          <el-button type="primary" @click="$router.push('/plan')" size="large">
            查看学习计划
          </el-button>
          <el-button @click="restartDiagnostic" size="large">
            重新诊断
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()

const loading = ref(false)
const submitting = ref(false)
const examData = ref(null)
const result = ref(null)
const currentQuestionIndex = ref(0)
const answers = ref([])
const currentAnswer = ref('')

const totalQuestions = computed(() => {
  return examData.value?.questions?.length || 0
})

const progressPercent = computed(() => {
  return Math.round((currentQuestionIndex.value + 1) / totalQuestions.value * 100)
})

const currentQuestion = computed(() => {
  if (!examData.value || !examData.value.questions) return null
  return examData.value.questions[currentQuestionIndex.value]
})

const hasAnswer = computed(() => {
  const answer = currentAnswer.value
  if (Array.isArray(answer)) {
    return answer.length > 0
  }
  return answer && answer.trim() !== ''
})

const getQuestionTypeText = (type) => {
  const typeMap = {
    'SINGLE': '单选题',
    'MULTI': '多选题',
    'JUDGE': '判断题',
    'FILL': '填空题',
    'SHORT': '简答题'
  }
  return typeMap[type] || type
}

const getWeakPointsText = () => {
  if (!result.value?.weak_points || result.value.weak_points.length === 0) {
    return '暂无'
  }
  return result.value.weak_points.slice(0, 3).join('、') + (result.value.weak_points.length > 3 ? '等' : '')
}

const startDiagnostic = async () => {
  try {
    loading.value = true

    // 获取诊断考试列表
    const examResponse = await authStore.api.get('/exams?category=DIAGNOSTIC')
    const exams = examResponse.data.items

    if (!exams || exams.length === 0) {
      ElMessage.warning('暂无可用的诊断考试，请联系管理员')
      return
    }

    // 开始第一个诊断考试
    const examId = exams[0].id
    const startResponse = await authStore.api.post(`/exams/${examId}/start`)

    examData.value = startResponse.data
    currentQuestionIndex.value = 0
    answers.value = new Array(examData.value.questions.length).fill('')
    currentAnswer.value = ''

    ElMessage.success('诊断考试开始，请认真作答')
  } catch (error) {
    console.error('开始诊断失败:', error)
    ElMessage.error(error.response?.data?.detail || '开始诊断失败，请重试')
  } finally {
    loading.value = false
  }
}

const nextQuestion = async () => {
  if (!hasAnswer.value) {
    ElMessage.warning('请先答题')
    return
  }

  try {
    // 保存当前答案到后端
    await submitCurrentAnswer()

    // 移动到下一题
    if (currentQuestionIndex.value < totalQuestions.value - 1) {
      currentQuestionIndex.value++
      currentAnswer.value = answers.value[currentQuestionIndex.value] || ''
    }
  } catch (error) {
    ElMessage.error('保存答案失败，请重试')
  }
}

const previousQuestion = () => {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value--
    currentAnswer.value = answers.value[currentQuestionIndex.value] || ''
  }
}

const submitCurrentAnswer = async () => {
  const answerData = {
    question_id: currentQuestion.value.question.id,
    answer: currentAnswer.value,
    time_spent_seconds: 30 // 暂时固定，后续可计算实际用时
  }

  await authStore.api.post(`/attempts/${examData.value.attempt_id}/answer`, answerData)

  // 保存到本地数组
  answers.value[currentQuestionIndex.value] = currentAnswer.value
}

const submitExam = async () => {
  if (!hasAnswer.value) {
    ElMessage.warning('请先答题')
    return
  }

  try {
    await ElMessageBox.confirm(
      '确定要提交诊断考试吗？提交后将无法修改答案。',
      '提交确认',
      {
        confirmButtonText: '确定提交',
        cancelButtonText: '再检查一下',
        type: 'warning',
      }
    )

    submitting.value = true

    // 保存最后一题答案
    await submitCurrentAnswer()

    // 提交整个考试
    const submitResponse = await authStore.api.post(`/attempts/${examData.value.attempt_id}/submit`)
    result.value = submitResponse.data

    ElMessage.success('诊断完成！系统正在生成您的个性化学习计划')
  } catch (error) {
    if (error === 'cancel') {
      return // 用户取消
    }
    console.error('提交考试失败:', error)
    ElMessage.error(error.response?.data?.detail || '提交失败，请重试')
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
  background-color: #f5f5f5;
  min-height: 100vh;
}

.diagnostic-card {
  max-width: 900px;
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

.start-section {
  text-align: center;
  padding: 60px 20px;
}

.tips-section {
  margin-top: 40px;
  text-align: left;
}

.tips-section ul {
  margin: 10px 0 0 20px;
  padding: 0;
}

.tips-section li {
  margin: 8px 0;
  color: #606266;
}

.exam-section {
  max-width: 800px;
  margin: 0 auto;
}

.exam-header {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.exam-info h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.exam-meta {
  display: flex;
  gap: 10px;
}

.progress-section {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-top: 15px;
}

.progress-bar {
  flex: 1;
}

.progress-text {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.question-content {
  margin: 40px 0;
  padding: 30px;
  background-color: #fafafa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.question-type {
  background-color: #e1f3d8;
  color: #67c23a;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.question-score {
  color: #e6a23c;
  font-weight: 500;
}

.question-stem {
  margin-bottom: 25px;
  line-height: 1.8;
  color: #303133;
  font-size: 16px;
}

.options-group {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.option-item {
  padding: 15px 20px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  transition: all 0.3s ease;
  background-color: white;
  cursor: pointer;
}

.option-item:hover {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.option-label {
  font-weight: 600;
  margin-right: 10px;
  color: #409eff;
}

.fill-input, .short-input {
  margin-top: 15px;
}

.action-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.result-section {
  text-align: center;
}

.result-alert {
  margin-bottom: 40px;
}

.result-content {
  margin: 40px 0;
}

.score-card, .analysis-card {
  text-align: left;
  height: 100%;
}

.score-header {
  text-align: center;
  margin-bottom: 20px;
}

.score-header h4 {
  margin: 0 0 15px 0;
  color: #303133;
}

.score-display {
  display: flex;
  align-items: baseline;
  justify-content: center;
  margin-bottom: 10px;
}

.score-number {
  font-size: 48px;
  font-weight: bold;
  color: #409eff;
}

.score-total {
  font-size: 24px;
  color: #909399;
  margin-left: 5px;
}

.score-meta {
  color: #606266;
  font-size: 14px;
}

.analysis-content {
  padding: 10px 0;
}

.analysis-item {
  display: flex;
  margin-bottom: 15px;
  align-items: flex-start;
}

.analysis-label {
  font-weight: 500;
  color: #303133;
  min-width: 120px;
  margin-right: 15px;
}

.analysis-value {
  color: #606266;
  flex: 1;
}

.result-actions {
  margin-top: 40px;
  display: flex;
  justify-content: center;
  gap: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .diagnostic-page {
    padding: 10px;
  }

  .diagnostic-card {
    margin: 0;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .exam-meta {
    flex-wrap: wrap;
  }

  .question-content {
    padding: 20px;
    margin: 20px 0;
  }

  .action-buttons {
    flex-direction: column;
    gap: 10px;
  }

  .action-buttons .el-button {
    width: 100%;
  }

  .result-actions {
    flex-direction: column;
    align-items: center;
  }

  .result-actions .el-button {
    width: 200px;
  }
}
</style>