<template>
  <el-card class="admin-dashboard">
    <template #header>
      <div class="header-row">
        <h3>管理端数据总览</h3>
        <el-text type="info">系统概览与导出</el-text>
      </div>
    </template>

    <div class="metrics">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card>
            <div class="metric-title">总用户</div>
            <div class="metric-value">{{ overview.total_users }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card>
            <div class="metric-title">活跃用户(7天)</div>
            <div class="metric-value">{{ overview.active_users }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card>
            <div class="metric-title">平均完成率</div>
            <div class="metric-value">{{ overview.avg_completion_rate }}%</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card>
            <div class="metric-title">到期错题总量</div>
            <div class="metric-value">{{ overview.wrong_due_total }}</div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div style="margin-top:20px;">
      <el-button type="primary" @click="downloadExport" :loading="exporting">下载脱敏数据</el-button>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const overview = ref({ total_users: 0, active_users: 0, avg_completion_rate: 0, avg_score: 0, wrong_due_total: 0 })
const exporting = ref(false)

const loadOverview = async () => {
  try {
    const res = await authStore.api.get('/analytics/admin/overview')
    overview.value = res.data
  } catch (e) {
    // ignore
  }
}

const downloadExport = async () => {
  try {
    exporting.value = true
    const res = await authStore.api.get('/admin/export/anonymized', { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'anonymized_export.csv')
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (e) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  loadOverview()
})
</script>


