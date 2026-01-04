<template>
  <el-card class="mock-card">
    <template #header>
      <div class="header-row">
        <h3>模拟考试</h3>
        <el-text type="info">参加全真模拟考试</el-text>
      </div>
    </template>

    <div class="exam-list">
      <el-table :data="exams" style="width:100%">
        <el-table-column prop="title" label="试卷标题" />
        <el-table-column prop="duration_minutes" label="时长(分钟)" width="140" />
        <el-table-column prop="created_at" label="发布时间" width="220" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="startExam(row.id)">开始</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="history" style="margin-top:20px;">
      <h4>历史记录</h4>
      <el-table :data="history" style="width:100%">
        <el-table-column prop="submitted_at" label="时间" width="220" />
        <el-table-column prop="exam_title" label="试卷" />
        <el-table-column prop="total_score" label="得分" width="120" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" @click="viewResult(row.attempt_id)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const exams = ref([])
const history = ref([])

const loadExams = async () => {
  try {
    const res = await authStore.api.get('/exams?category=MOCK')
    exams.value = res.data.items || []
  } catch (e) {
    ElMessage.error('加载模拟考试列表失败')
  }
}

const loadHistory = async () => {
  try {
    const res = await authStore.api.get('/attempts/history?category=MOCK&limit=20')
    history.value = res.data.items || []
  } catch (e) {
    // ignore
  }
}

const startExam = async (examId) => {
  try {
    const res = await authStore.api.post(`/exams/${examId}/start`)
    const attempt = res.data
    // go to unified exam page
    window.location.href = `/exam?attempt_id=${attempt.attempt_id}`
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '开始考试失败')
  }
}

const viewResult = (attemptId) => {
  window.location.href = `/exam?attempt_id=${attemptId}`
}

onMounted(async () => {
  await loadExams()
  await loadHistory()
})
</script>

<style scoped>
.mock-card { max-width: 1000px; margin: 20px auto; }
.header-row { display:flex; justify-content:space-between; align-items:center; }
</style>


