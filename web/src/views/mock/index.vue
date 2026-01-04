<template>
  <div class="mock-exam-page">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>模拟考试</span>
          <el-text type="info">模拟真实考试环境，检验学习成果</el-text>
        </div>
      </template>

      <el-empty v-if="exams.length === 0 && !loading" description="暂无模拟考试可参与" />
      <div v-else>
        <el-table :data="exams" v-loading="loading" style="width: 100%">
          <el-table-column prop="title" label="考试名称" />
          <el-table-column prop="duration_minutes" label="时长(分钟)" width="120" />
          <el-table-column prop="total_questions" label="总题数" width="100" />
          <el-table-column prop="created_at" label="发布时间" width="180">
            <template #default="scope">
              {{ new Date(scope.row.created_at).toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button type="primary" link @click="startExam(scope.row.id)">开始考试</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="totalExams > size"
          background
          layout="prev, pager, next"
          :total="totalExams"
          :page-size="size"
          :current-page="page"
          @current-change="handlePageChange"
          style="margin-top: 20px; justify-content: center;"
        />
      </div>
    </el-card>

    <el-card class="box-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>历史记录</span>
        </div>
      </template>
      <el-empty v-if="history.length === 0 && !historyLoading" description="暂无模拟考试历史记录" />
      <div v-else>
        <el-table :data="history" v-loading="historyLoading" style="width: 100%">
          <el-table-column prop="exam_title" label="考试名称" />
          <el-table-column prop="total_score" label="得分" width="100" />
          <el-table-column prop="submitted_at" label="提交时间" width="180">
            <template #default="scope">
              {{ new Date(scope.row.submitted_at).toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button type="primary" link @click="viewResult(scope.row.attempt_id)">查看结果</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const exams = ref([])
const totalExams = ref(0)
const page = ref(1)
const size = ref(10)
const loading = ref(false)

const history = ref([])
const historyLoading = ref(false)

const fetchExams = async () => {
  loading.value = true
  try {
    const response = await authStore.api.get('/exams', {
      params: { category: 'MOCK', page: page.value, size: size.value }
    })
    exams.value = response.data.items
    totalExams.value = response.data.total
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '获取模拟考试列表失败')
  } finally {
    loading.value = false
  }
}

const fetchHistory = async () => {
  historyLoading.value = true
  try {
    const response = await authStore.api.get('/attempts/history', {
      params: { category: 'MOCK', limit: 20 }
    })
    history.value = response.data.items
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '获取历史记录失败')
  } finally {
    historyLoading.value = false
  }
}

const startExam = async (examId) => {
  try {
    const response = await authStore.api.post(`/exams/${examId}/start`)
    localStorage.setItem('current_attempt', JSON.stringify(response.data))
    router.push({ path: '/exam', query: { attempt_id: response.data.attempt_id } })
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '开始考试失败')
  }
}

const viewResult = (attemptId) => {
  router.push({ path: '/exam', query: { attempt_id: attemptId, view_only: 'true' } })
}

const handlePageChange = (val) => {
  page.value = val
  fetchExams()
}

onMounted(() => {
  fetchExams()
  fetchHistory()
})
</script>

<style scoped>
.mock-exam-page {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>


