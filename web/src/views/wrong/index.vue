<template>
  <el-card class="wrong-card">
    <template #header>
      <div class="header-row">
        <h3>我的错题本</h3>
        <el-text type="info">查看错题、开始到期复习</el-text>
      </div>
    </template>

    <div class="controls">
      <el-radio-group v-model="mode">
        <el-radio-button label="all">全部错题</el-radio-button>
        <el-radio-button label="due">到期复习</el-radio-button>
      </el-radio-group>
      <el-button type="primary" @click="generateReview" :loading="generating">开始到期复习</el-button>
    </div>

    <div class="list">
      <el-table :data="items" style="width:100%">
        <el-table-column prop="question_id" label="ID" width="80" />
        <el-table-column prop="stem" label="题干" />
        <el-table-column prop="knowledge_points" label="知识点" width="200">
          <template #default="{ row }">
            <el-tag v-for="kp in row.knowledge_points" :key="kp.id" size="small" style="margin-right:6px">{{ kp.name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="wrong_count" label="错题次数" width="120" />
        <el-table-column prop="next_review_at" label="下次复习" width="200" />
      </el-table>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const mode = ref('all')
const items = ref([])
const generating = ref(false)

const load = async () => {
  try {
    const res = await authStore.api.get('/wrong-questions', { params: { due_only: mode.value === 'due' } })
    items.value = res.data.items
  } catch (e) {
    ElMessage.error('加载错题本失败')
  }
}

const generateReview = async () => {
  try {
    generating.value = true
    const res = await authStore.api.post('/wrong-questions/review/generate', { count: 10 })
    const examId = res.data.exam_id
    const startRes = await authStore.api.post(`/exams/${examId}/start`)
    const attemptId = startRes.data.attempt_id
    // use router.push to avoid full page reload (demo mode)
    router.push({ path: '/exam', query: { attempt_id: attemptId } })
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '生成复习失败')
  } finally {
    generating.value = false
  }
}

onMounted(() => {
  load()
})
</script>

<style scoped>
.wrong-card { max-width: 1000px; margin: 20px auto; }
.controls { display:flex; gap:12px; align-items:center; margin-bottom:12px; }
.list { margin-top:12px; }
</style>


