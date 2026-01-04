<template>
  <div class="exam-page">
    <el-card class="exam-card">
      <template #header>
        <div class="header-row">
          <h3>{{ examData?.exam?.title || '考试' }}</h3>
          <div v-if="remainingSeconds !== null" class="timer">剩余时间：{{ formatTime(remainingSeconds) }}</div>
        </div>
      </template>

      <div v-if="loading" class="loading">加载中...</div>

      <div v-else-if="!examData" class="no-data">无法加载考试信息</div>

      <div v-else class="exam-body">
        <div class="progress">{{ currentIndex + 1 }} / {{ totalQuestions }}</div>

        <div class="question-area">
          <h4 v-html="currentQuestion.question.stem"></h4>

          <div v-if="currentQuestion.question.type === 'SINGLE'">
            <el-radio-group v-model="currentAnswer">
              <el-radio v-for="(opt, i) in currentQuestion.question.options_json" :key="i" :label="String.fromCharCode(65 + i)">
                <span v-html="opt"></span>
              </el-radio>
            </el-radio-group>
          </div>

          <div v-if="currentQuestion.question.type === 'MULTI'">
            <el-checkbox-group v-model="currentAnswer">
              <el-checkbox v-for="(opt, i) in currentQuestion.question.options_json" :key="i" :label="String.fromCharCode(65 + i)">
                <span v-html="opt"></span>
              </el-checkbox>
            </el-checkbox-group>
          </div>

          <div v-if="currentQuestion.question.type === 'JUDGE'">
            <el-radio-group v-model="currentAnswer">
              <el-radio label="T">正确</el-radio>
              <el-radio label="F">错误</el-radio>
            </el-radio-group>
          </div>

          <div v-if="currentQuestion.question.type === 'FILL'">
            <el-input v-model="currentAnswer" placeholder="请输入答案" />
          </div>

          <div v-if="currentQuestion.question.type === 'SHORT'">
            <el-input type="textarea" v-model="currentAnswer" rows="4" />
          </div>
        </div>

        <div class="actions">
          <el-button @click="prevQuestion" :disabled="currentIndex===0">上一题</el-button>
          <el-button @click="saveAnswer">保存</el-button>
          <el-button v-if="currentIndex < totalQuestions -1" type="primary" @click="nextQuestion">下一题</el-button>
          <el-button v-else type="success" @click="submitExam" :loading="submitting">提交</el-button>
        </div>
      </div>

      <!-- 结果展示（只在viewOnly模式下显示） -->
      <div v-else-if="viewOnly && result" class="result-section">
        <el-alert
          title="考试已完成！"
          type="success"
          :closable="false"
          class="result-alert"
        />

        <div class="result-summary">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-statistic title="总得分" :value="result.total_score" />
            </el-col>
            <el-col :span="12">
              <el-statistic title="总题数" :value="result.results.length" />
            </el-col>
          </el-row>
        </div>

        <el-divider>题目详情与解析</el-divider>
        <el-collapse v-model="activeNames">
          <el-collapse-item
            v-for="(item, index) in result.results"
            :key="item.question_id"
            :name="index"
            :title="`Q${index + 1}: ${item.question_stem.substring(0, 50)}${item.question_stem.length > 50 ? '...' : ''}`"
          >
            <div class="question-result-detail">
              <p><strong>你的答案:</strong>
                <span :class="{ 'correct-answer': item.is_correct, 'wrong-answer': !item.is_correct }">
                  {{ formatAnswer(item.user_answer) }}
                </span>
              </p>
              <p><strong>正确答案:</strong>
                <span class="correct-answer">{{ formatAnswer(item.correct_answer) }}</span>
              </p>
              <p><strong>判分:</strong>
                <el-tag :type="item.is_correct ? 'success' : 'danger'">
                  {{ item.is_correct ? '正确' : '错误' }} (得分: {{ item.score_awarded }})
                </el-tag>
              </p>
              <p v-if="item.analysis"><strong>解析:</strong> {{ item.analysis }}</p>
              <p v-if="item.matched_keywords && item.matched_keywords.length > 0">
                <strong>命中关键词:</strong> {{ item.matched_keywords.join('、') }} ({{ item.matched_keywords.length }}个)
              </p>
            </div>
          </el-collapse-item>
        </el-collapse>

        <div class="result-actions" style="margin-top: 20px;">
          <el-button type="primary" @click="router.push('/home')">返回首页</el-button>
          <el-button @click="router.back()">返回上一页</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(true)
const submitting = ref(false)
const examData = ref(null)
const currentIndex = ref(0)
const currentAnswer = ref('')
const remainingSeconds = ref(null)
const viewOnly = ref(false)
const result = ref(null)
const activeNames = ref([]) // For collapse in results
let timerHandle = null

const totalQuestions = computed(() => examData.value?.questions?.length || 0)
const currentQuestion = computed(() => examData.value?.questions?.[currentIndex.value] || null)

function formatTime(sec) {
  if (sec === null) return ''
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
}

function formatAnswer(answer) {
  if (Array.isArray(answer)) {
    return answer.join(', ')
  }
  return answer || '未作答'
}

async function loadResult(attemptId) {
  try {
    loading.value = true
    const res = await authStore.api.get(`/attempts/${attemptId}/result`)
    result.value = res.data
    // Set exam data for display
    examData.value = {
      exam: { title: result.value.exam_title },
      questions: result.value.results.map(r => ({
        question: { stem: r.question_stem, type: 'COMPLETED' }
      }))
    }
  } catch (e) {
    ElMessage.error('加载结果失败')
  } finally {
    loading.value = false
  }
}

async function loadAttempt(attemptId) {
  try {
    loading.value = true
    const res = await authStore.api.get(`/attempts/${attemptId}`)
    examData.value = res.data
    currentIndex.value = 0
    // init currentAnswer from saved_answer
    currentAnswer.value = examData.value.questions[0]?.saved_answer || ''

    // setup timer if duration provided
    const dur = examData.value.exam?.duration_minutes || 0
    if (dur && examData.value.started_at) {
      const started = new Date(examData.value.started_at)
      const end = new Date(started.getTime() + dur * 60000)
      const update = () => {
        const now = new Date()
        const diff = Math.floor((end - now) / 1000)
        remainingSeconds.value = diff > 0 ? diff : 0
        if (diff <= 0) {
          clearInterval(timerHandle)
          // auto submit after 3s grace
          submitExam()
        }
      }
      update()
      timerHandle = setInterval(update, 1000)
    } else {
      remainingSeconds.value = null
    }
  } catch (e) {
    ElMessage.error('加载作答记录失败')
  } finally {
    loading.value = false
  }
}

async function saveAnswer() {
  try {
    if (!currentQuestion.value) return
    await authStore.api.post(`/attempts/${examData.value.attempt_id}/answer`, {
      question_id: currentQuestion.value.question.id,
      answer: currentAnswer.value,
      time_spent_seconds: 30
    })
    ElMessage.success('已保存')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

async function nextQuestion() {
  await saveAnswer()
  if (currentIndex.value < totalQuestions.value - 1) {
    currentIndex.value++
    currentAnswer.value = examData.value.questions[currentIndex.value]?.saved_answer || ''
  }
}

async function prevQuestion() {
  await saveAnswer()
  if (currentIndex.value > 0) {
    currentIndex.value--
    currentAnswer.value = examData.value.questions[currentIndex.value]?.saved_answer || ''
  }
}

async function submitExam() {
  try {
    await ElMessageBox.confirm('确认提交考试？', '提交确认', { type: 'warning' })
    submitting.value = true
    await saveAnswer()
    const res = await authStore.api.post(`/attempts/${examData.value.attempt_id}/submit`)
    ElMessage.success('提交完成')
    // go to result view
    router.push({
      path: '/exam',
      query: {
        attempt_id: examData.value.attempt_id,
        view_only: 'true'
      }
    })
  } catch (e) {
    if (e === 'cancel') return
    ElMessage.error(e.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  const attemptId = route.query.attempt_id
  const viewOnlyParam = route.query.view_only === 'true'
  viewOnly.value = viewOnlyParam

  if (!attemptId) {
    ElMessage.error('缺少 attempt_id')
    router.push('/home')
    return
  }

  if (viewOnly.value) {
    loadResult(attemptId)
  } else {
    loadAttempt(attemptId)
  }
})
</script>

<style scoped>
.exam-card { max-width: 900px; margin: 20px auto; }
.header-row { display:flex; justify-content:space-between; align-items:center; }
.timer { color: #f56c6c; font-weight: 600; }
.question-area { padding: 20px 0; }
.actions { display:flex; gap:10px; justify-content:flex-end; margin-top:20px; }

.result-section {
  text-align: center;
}
.result-alert {
  margin-bottom: 30px;
}
.result-summary {
  margin: 30px 0;
}
.question-result-detail {
  text-align: left;
  padding-left: 20px;
  border-left: 3px solid #e4e7ed;
  margin-top: 10px;
}
.question-result-detail p {
  margin-bottom: 8px;
}
.correct-answer {
  color: #67c23a;
  font-weight: 500;
}
.wrong-answer {
  color: #f56c6c;
  font-weight: 500;
}
.result-actions {
  margin-top: 30px;
}
.result-actions .el-button {
  margin: 0 10px;
}
</style>


