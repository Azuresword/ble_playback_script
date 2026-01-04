<template>
  <div class="app-container">
    <!-- 头部 -->
    <el-header class="app-header">
      <div class="header-content">
        <div class="logo">
          <el-icon :size="32" color="#409EFF"><Connection /></el-icon>
          <h1>BLE 数据处理平台</h1>
        </div>
        <div class="header-info">
          <el-tag type="success">v1.0.0</el-tag>
        </div>
      </div>
    </el-header>

    <!-- 主内容 -->
    <el-container class="main-container">
      <!-- 侧边栏 -->
      <el-aside width="250px" class="sidebar">
        <el-menu
          :default-active="activeTab"
          @select="handleMenuSelect"
          class="sidebar-menu"
        >
          <el-menu-item index="upload">
            <el-icon><Upload /></el-icon>
            <span>数据上传</span>
          </el-menu-item>
          <el-menu-item index="process">
            <el-icon><Setting /></el-icon>
            <span>数据处理</span>
          </el-menu-item>
          <el-menu-item index="files">
            <el-icon><Document /></el-icon>
            <span>文件管理</span>
          </el-menu-item>
          <el-menu-item index="visualize">
            <el-icon><TrendCharts /></el-icon>
            <span>数据可视化</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主要内容区域 -->
      <el-main class="content-area">
        <!-- 上传页面 -->
        <div v-show="activeTab === 'upload'" class="tab-content">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title">上传数据文件</span>
                <el-text type="info">支持 CSV 和 TXT 格式</el-text>
              </div>
            </template>

            <el-upload
              class="upload-demo"
              drag
              :action="uploadUrl"
              :on-success="handleUploadSuccess"
              :on-error="handleUploadError"
              :before-upload="beforeUpload"
              :show-file-list="false"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                拖拽文件到此处或 <em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  请上传 data.csv 或 data.txt 文件
                </div>
              </template>
            </el-upload>

            <!-- 上传成功后显示预览 -->
            <div v-if="uploadedFile" class="file-preview">
              <el-divider />
              <h3>文件信息</h3>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="文件名">{{ uploadedFile.filename }}</el-descriptions-item>
                <el-descriptions-item label="文件大小">{{ formatFileSize(uploadedFile.size) }}</el-descriptions-item>
              </el-descriptions>

              <h3 style="margin-top: 20px">数据预览（前10行）</h3>
              <el-table :data="uploadedFile.preview" border stripe max-height="300">
                <el-table-column
                  v-for="(col, index) in uploadedFile.preview[0]"
                  :key="index"
                  :prop="index.toString()"
                  :label="`列 ${index + 1}`"
                  :formatter="(row) => row[index]"
                />
              </el-table>
            </div>
          </el-card>
        </div>

        <!-- 处理页面 -->
        <div v-show="activeTab === 'process'" class="tab-content">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title">数据处理流程</span>
              </div>
            </template>

            <el-form :model="processForm" label-width="120px">
              <el-form-item label="选择文件">
                <el-input v-model="processForm.filename" placeholder="请先上传文件" readonly />
              </el-form-item>

              <el-form-item label="处理步骤">
                <el-checkbox-group v-model="processForm.steps">
                  <el-checkbox label="split">拆分设备数据</el-checkbox>
                  <el-checkbox label="align">对齐气压计数据</el-checkbox>
                  <el-checkbox label="downsample">降采样到 50Hz</el-checkbox>
                  <el-checkbox label="convert">转换为二进制格式</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="startProcessing" :loading="processing">
                  <el-icon><VideoPlay /></el-icon>
                  开始处理
                </el-button>
                <el-button @click="resetForm">重置</el-button>
              </el-form-item>
            </el-form>

            <!-- 处理进度 -->
            <div v-if="taskStatus" class="progress-section">
              <el-divider />
              <h3>处理进度</h3>
              <el-progress
                :percentage="taskStatus.progress"
                :status="taskStatus.status === 'completed' ? 'success' : (taskStatus.status === 'failed' ? 'exception' : '')"
              />
              <el-alert
                :title="taskStatus.message"
                :type="taskStatus.status === 'completed' ? 'success' : (taskStatus.status === 'failed' ? 'error' : 'info')"
                :closable="false"
                show-icon
                style="margin-top: 10px"
              />

              <!-- 处理结果 -->
              <div v-if="taskStatus.result" style="margin-top: 20px">
                <h4>处理完成，生成了 {{ taskStatus.result.total_files }} 个文件</h4>
                <el-button type="primary" @click="activeTab = 'files'">查看文件</el-button>
              </div>
            </div>
          </el-card>
        </div>

        <!-- 文件管理页面 -->
        <div v-show="activeTab === 'files'" class="tab-content">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title">文件管理</span>
                <el-button type="primary" :icon="Refresh" @click="loadFiles" circle />
              </div>
            </template>

            <el-table :data="files" border stripe>
              <el-table-column prop="device" label="设备" width="100" />
              <el-table-column prop="name" label="文件名" />
              <el-table-column prop="type" label="类型" width="100" />
              <el-table-column prop="size" label="大小" width="120" :formatter="row => formatFileSize(row.size)" />
              <el-table-column label="操作" width="250">
                <template #default="scope">
                  <el-button size="small" @click="downloadFile(scope.row)">
                    <el-icon><Download /></el-icon>
                    下载
                  </el-button>
                  <el-button size="small" type="primary" @click="previewFile(scope.row)" v-if="scope.row.type === '.csv'">
                    <el-icon><View /></el-icon>
                    预览
                  </el-button>
                  <el-button size="small" type="success" @click="visualizeFile(scope.row)" v-if="scope.row.type === '.csv'">
                    <el-icon><TrendCharts /></el-icon>
                    图表
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>

        <!-- 数据可视化页面 -->
        <div v-show="activeTab === 'visualize'" class="tab-content">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title">数据可视化</span>
                <el-text type="info" v-if="currentFile">{{ currentFile.device }} - {{ currentFile.name }}</el-text>
              </div>
            </template>

            <div v-if="!currentFile" class="empty-state">
              <el-empty description="请从文件管理页面选择一个CSV文件进行可视化" />
            </div>

            <div v-else>
              <!-- 统计信息 -->
              <el-descriptions :column="4" border v-if="fileStats">
                <el-descriptions-item label="总行数">{{ fileStats.row_count }}</el-descriptions-item>
                <el-descriptions-item label="总列数">{{ fileStats.column_count }}</el-descriptions-item>
              </el-descriptions>

              <!-- 图表 -->
              <div ref="chartContainer" style="width: 100%; height: 500px; margin-top: 20px"></div>
            </div>
          </el-card>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

// 状态
const activeTab = ref('upload')
const uploadedFile = ref(null)
const processForm = ref({
  filename: '',
  steps: ['split', 'align', 'downsample', 'convert']
})
const processing = ref(false)
const taskStatus = ref(null)
const files = ref([])
const currentFile = ref(null)
const fileStats = ref(null)
const chartContainer = ref(null)

const uploadUrl = 'http://localhost:8000/api/upload'

// 菜单选择
const handleMenuSelect = (index) => {
  activeTab.value = index
  if (index === 'files') {
    loadFiles()
  }
}

// 文件上传
const beforeUpload = (file) => {
  const isValidType = file.name.endsWith('.csv') || file.name.endsWith('.txt')
  if (!isValidType) {
    ElMessage.error('只能上传 CSV 或 TXT 文件！')
  }
  return isValidType
}

const handleUploadSuccess = (response) => {
  uploadedFile.value = response
  processForm.value.filename = response.filename
  ElMessage.success('文件上传成功！')
}

const handleUploadError = () => {
  ElMessage.error('文件上传失败！')
}

// 开始处理
const startProcessing = async () => {
  if (!processForm.value.filename) {
    ElMessage.warning('请先上传文件！')
    return
  }
  if (processForm.value.steps.length === 0) {
    ElMessage.warning('请至少选择一个处理步骤！')
    return
  }

  processing.value = true
  try {
    const { data } = await axios.post('/api/process', processForm.value)
    const taskId = data.task_id
    ElMessage.success('处理任务已启动')

    // 轮询任务状态
    pollTaskStatus(taskId)
  } catch (error) {
    ElMessage.error('启动处理失败：' + error.message)
    processing.value = false
  }
}

const pollTaskStatus = async (taskId) => {
  const interval = setInterval(async () => {
    try {
      const { data } = await axios.get(`/api/task/${taskId}`)
      taskStatus.value = data

      if (data.status === 'completed' || data.status === 'failed') {
        clearInterval(interval)
        processing.value = false

        if (data.status === 'completed') {
          ElMessage.success('处理完成！')
        } else {
          ElMessage.error('处理失败：' + data.error)
        }
      }
    } catch (error) {
      clearInterval(interval)
      processing.value = false
      ElMessage.error('获取任务状态失败')
    }
  }, 1000)
}

const resetForm = () => {
  processForm.value = {
    filename: uploadedFile.value?.filename || '',
    steps: ['split', 'align', 'downsample', 'convert']
  }
  taskStatus.value = null
}

// 加载文件列表
const loadFiles = async () => {
  try {
    const { data } = await axios.get('/api/files')
    files.value = data.files
  } catch (error) {
    ElMessage.error('加载文件列表失败')
  }
}

// 下载文件
const downloadFile = (file) => {
  window.open(`http://localhost:8000/api/download/${file.device}/${file.name}`, '_blank')
}

// 预览文件
const previewFile = async (file) => {
  try {
    const { data } = await axios.get(`/api/preview/${file.device}/${file.name}`)
    ElMessageBox.alert(
      `共 ${data.total_rows} 行数据`,
      '文件预览',
      { confirmButtonText: '确定' }
    )
  } catch (error) {
    ElMessage.error('预览文件失败')
  }
}

// 可视化文件
const visualizeFile = async (file) => {
  currentFile.value = file
  activeTab.value = 'visualize'

  try {
    // 获取统计信息
    const { data: stats } = await axios.get(`/api/stats/${file.device}/${file.name}`)
    fileStats.value = stats

    // 获取预览数据
    const { data: preview } = await axios.get(`/api/preview/${file.device}/${file.name}?limit=1000`)

    // 绘制图表
    setTimeout(() => {
      renderChart(preview, stats)
    }, 100)
  } catch (error) {
    ElMessage.error('加载数据失败')
  }
}

// 绘制图表
const renderChart = (preview, stats) => {
  if (!chartContainer.value) return

  const chart = echarts.init(chartContainer.value)

  // 准备数据 - 绘制加速度数据
  const header = preview.header
  const data = preview.data

  const accXIndex = header.indexOf('AccX(g)')
  const accYIndex = header.indexOf('AccY(g)')
  const accZIndex = header.indexOf('AccZ(g)')

  if (accXIndex === -1) {
    ElMessage.warning('未找到加速度数据')
    return
  }

  const xData = data.map((row, index) => index)
  const accXData = data.map(row => parseFloat(row[accXIndex]))
  const accYData = data.map(row => parseFloat(row[accYIndex]))
  const accZData = data.map(row => parseFloat(row[accZIndex]))

  const option = {
    title: {
      text: '加速度数据可视化',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['AccX', 'AccY', 'AccZ'],
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xData,
      name: '采样点'
    },
    yAxis: {
      type: 'value',
      name: '加速度 (g)'
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        start: 0,
        end: 100
      }
    ],
    series: [
      {
        name: 'AccX',
        type: 'line',
        data: accXData,
        smooth: true,
        symbolSize: 0
      },
      {
        name: 'AccY',
        type: 'line',
        data: accYData,
        smooth: true,
        symbolSize: 0
      },
      {
        name: 'AccZ',
        type: 'line',
        data: accZData,
        smooth: true,
        symbolSize: 0
      }
    ]
  }

  chart.setOption(option)
}

// 工具函数
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}

onMounted(() => {
  loadFiles()
})
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  padding: 0 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 15px;
}

.logo h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.main-container {
  flex: 1;
  overflow: hidden;
}

.sidebar {
  background: white;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.sidebar-menu {
  border: none;
}

.content-area {
  padding: 20px;
  overflow-y: auto;
}

.tab-content {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.upload-demo {
  text-align: center;
}

.file-preview {
  margin-top: 30px;
}

.progress-section {
  margin-top: 20px;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

:deep(.el-upload-dragger) {
  padding: 60px;
}

:deep(.el-icon--upload) {
  font-size: 67px;
  color: #409EFF;
  margin-bottom: 16px;
}
</style>
