<template>
  <el-card class="practice-card">
    <template #header>
      <div class="header-row">
        <h3>专项练习</h3>
        <el-text type="info">按知识点练习，系统会根据掌握度自适应难度</el-text>
      </div>
    </template>

    <div class="practice-body">
      <el-form :model="form" label-position="top">
        <el-form-item label="选择知识点">
          <el-select v-model="form.knowledge_id" placeholder="选择知识点">
            <el-option
              v-for="kp in knowledgeTreeFlat"
              :key="kp.id"
              :label="kp.name"
              :value="kp.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="题量">
          <el-select v-model="form.count" placeholder="选择题量" style="width: 120px;">
            <el-option label="5题" :value="5" />
            <el-option label="10题" :value="10" />
            <el-option label="20题" :value="20" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="startPractice" :loading="loading">开始练习</el-button>
        </el-form-item>
      </el-form>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const loading = ref(false)
const form = ref({
  knowledge_id: null,
  count: 10
})

const knowledgeTree = ref([])

const knowledgeTreeFlat = computed(() => {
  return knowledgeTree.value || []
})

const loadKnowledge = async () => {
  try {
    const res = await authStore.api.get('/knowledge/tree')
    // flatten tree for select
    const flatten = []
    const walk = (nodes) => {
      for (const n of nodes) {
        flatten.push({ id: n.id, name: n.name })
        if (n.children && n.children.length) walk(n.children)
      }
    }
    walk(res.data.tree || [])
    knowledgeTree.value = flatten
  } catch (e) {
    ElMessage.error('加载知识点失败')
  }
}

const startPractice = async () => {
  if (!form.value.knowledge_id) {
    ElMessage.warning('请选择知识点')
    return
  }
  loading.value = true
  try {
    const res = await authStore.api.post('/practice/generate', {
      knowledge_id: form.value.knowledge_id,
      count: form.value.count,
      mode: 'ADAPTIVE'
    })
    const examId = res.data.exam_id
    // 启动考试，复用 /exams/{id}/start
    const start = await authStore.api.post(`/exams/${examId}/start`)
    // 跳转到诊断答题页面（diagnostic 组件可处理 attempt_id）
    // 简单方式：将 attempt info 存到 localStorage 然后跳转
    localStorage.setItem('current_attempt', JSON.stringify(start.data))
    window.location.href = '/diagnostic'
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '生成练习失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadKnowledge()
})
</script>

<style scoped>
.practice-card { max-width: 700px; margin: 20px auto; }
.header-row { display:flex; justify-content:space-between; align-items:center; }
.practice-body { padding: 20px 0; }
</style>


