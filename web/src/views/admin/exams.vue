<template>
  <el-card class="admin-exams">
    <template #header>
      <div class="header-row">
        <h3>考试发布管理</h3>
        <div class="header-actions">
          <el-button type="warning" @click="regenerateDiagnostic">重新生成基线诊断</el-button>
          <el-button type="primary" @click="showCreate = true">创建考试</el-button>
        </div>
      </div>
    </template>

    <el-table :data="exams" style="width:100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="category" label="类别" width="120" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column prop="duration_minutes" label="时长" width="120" />
      <el-table-column prop="paper_id" label="Paper ID" width="120" />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button size="small" type="success" @click="publish(row.id)" v-if="row.status !== 'PUBLISHED'">发布</el-button>
          <el-button size="small" type="warning" @click="archive(row.id)" v-if="row.status !== 'ARCHIVED'">下架</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog title="创建考试" v-model="showCreate">
      <el-form :model="form">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="类别">
          <el-select v-model="form.category">
            <el-option label="DIAGNOSTIC" value="DIAGNOSTIC" />
            <el-option label="MOCK" value="MOCK" />
          </el-select>
        </el-form-item>
        <el-form-item label="时长(分钟)"><el-input-number v-model="form.duration_minutes" :min="0" /></el-form-item>
        <el-form-item label="Paper ID"><el-input v-model="form.paper_id" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="createExam">创建</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const authStore = useAuthStore()
const exams = ref([])
const loading = ref(false)
const showCreate = ref(false)
const form = ref({
  title: '',
  category: 'MOCK',
  duration_minutes: 60,
  paper_id: null
})

const load = async () => {
  try {
    loading.value = true
    const res = await authStore.api.get('/admin/exams')
    exams.value = res.data.items || []
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const createExam = async () => {
  try {
    const res = await authStore.api.post('/admin/exams', form.value)
    ElMessage.success('创建成功')
    showCreate.value = false
    await load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  }
}

const publish = async (id) => {
  try {
    await authStore.api.put(`/admin/exams/${id}/publish`)
    ElMessage.success('已发布')
    await load()
  } catch (e) {
    ElMessage.error('发布失败')
  }
}

const archive = async (id) => {
  try {
    await authStore.api.put(`/admin/exams/${id}/archive`)
    ElMessage.success('已下架')
    await load()
  } catch (e) {
    ElMessage.error('下架失败')
  }
}

const regenerateDiagnostic = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重新生成基线诊断试卷吗？这将创建新的诊断考试，原有的诊断考试将被归档。',
      '重新生成基线诊断',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    const res = await authStore.api.post('/admin/exams/diagnostic/regenerate')
    ElMessage.success('基线诊断试卷重新生成成功')
    await load()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '重新生成失败')
    }
  }
}

onMounted(() => {
  load()
})
</script>

<style scoped>
.admin-exams { max-width: 1000px; margin: 20px auto; }
.header-row { display:flex; justify-content:space-between; align-items:center; }
.header-actions { display: flex; gap: 10px; }
</style>


