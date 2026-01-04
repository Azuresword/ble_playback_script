<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
    <div class="app-header">
      <div class="header-content">
        <div class="logo-section">
          <div class="logo-icon">
            <el-icon :size="28"><Connection /></el-icon>
          </div>
          <div class="logo-text">
            <h1>BLE 数据处理平台</h1>
            <p>智能传感器数据分析系统</p>
          </div>
        </div>
        <div class="header-actions">
          <el-badge :value="files.length" :max="99" class="badge-item">
            <el-button text @click="activeTab = 'files'">
              <el-icon><Folder /></el-icon>
            </el-button>
          </el-badge>
          <el-tag effect="dark" round>v1.0.0</el-tag>
        </div>
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="main-content">
      <!-- 左侧导航 -->
      <div class="sidebar">
        <div class="nav-menu">
          <div
            v-for="item in menuItems"
            :key="item.index"
            :class="['menu-item', { active: activeTab === item.index }]"
            @click="handleMenuSelect(item.index)"
          >
            <el-icon :size="20" class="menu-icon">
              <component :is="item.icon" />
            </el-icon>
            <span class="menu-text">{{ item.label }}</span>
            <div class="menu-indicator" v-if="activeTab === item.index"></div>
          </div>
        </div>
      </div>

      <!-- 右侧内容区 -->
      <div class="content-area">
        <!-- 页面标题 -->
        <div class="page-header">
          <h2>{{ currentPageTitle }}</h2>
          <p>{{ currentPageDesc }}</p>
        </div>

        <!-- 上传页面 -->
        <transition name="fade" mode="out-in">
          <div v-if="activeTab === 'upload'" class="page-content">
            <div class="upload-card">
              <el-upload
                class="upload-area"
                drag
                :action="uploadUrl"
                :on-success="handleUploadSuccess"
                :on-error="handleUploadError"
                :before-upload="beforeUpload"
                :show-file-list="false"
              >
                <div class="upload-inner">
                  <el-icon class="upload-icon"><UploadFilled /></el-icon>
                  <div class="upload-text">拖拽文件到此处</div>
                  <div class="upload-hint">或点击选择文件</div>
                  <div class="upload-formats">支持 CSV 和 TXT 格式</div>
                </div>
              </el-upload>

              <!-- 上传成功后的预览 -->
              <transition name="slide-up">
                <div v-if="uploadedFile" class="upload-result">
                  <div class="result-header">
                    <el-icon class="success-icon"><CircleCheck /></el-icon>
                    <span>上传成功</span>
                  </div>

                  <div class="file-info-grid">
                    <div class="info-item">
                      <div class="info-label">文件名称</div>
                      <div class="info-value">{{ uploadedFile.filename }}</div>
                    </div>
                    <div class="info-item">
                      <div class="info-label">文件大小</div>
                      <div class="info-value">{{ formatFileSize(uploadedFile.size) }}</div>
                    </div>
                  </div>

                  <div class="preview-section">
                    <h4>数据预览</h4>
                    <el-table
                      :data="uploadedFile.preview.slice(1, 6)"
                      stripe
                      style="width: 100%"
                      :header-cell-style="{ background: '#f5f7fa' }"
                    >
                      <el-table-column
                        v-for="(col, index) in uploadedFile.preview[0]"
                        :key="index"
                        :prop="index.toString()"
                        :label="uploadedFile.preview[0][index]"
                        :formatter="(row) => row[index]"
                        width="150"
                      />
                    </el-table>
                  </div>
                </div>
              </transition>
            </div>
          </div>
        </transition>

        <!-- 处理页面 -->
        <transition name="fade" mode="out-in">
          <div v-if="activeTab === 'process'" class="page-content">
            <div class="process-card">
              <div class="process-steps">
                <div
                  v-for="(step, idx) in processSteps"
                  :key="step.value"
                  :class="['step-item', { active: processForm.steps.includes(step.value) }]"
                  @click="toggleStep(step.value)"
                >
                  <div class="step-number">{{ idx + 1 }}</div>
                  <div class="step-content">
                    <div class="step-title">{{ step.label }}</div>
                    <div class="step-desc">{{ step.desc }}</div>
                  </div>
                  <el-icon class="step-check" v-if="processForm.steps.includes(step.value)">
                    <Check />
                  </el-icon>
                </div>
              </div>

              <div class="process-actions">
                <el-button
                  type="primary"
                  size="large"
                  :loading="processing"
                  @click="startProcessing"
                  :disabled="!uploadedFile || processForm.steps.length === 0"
                >
                  <el-icon><VideoPlay /></el-icon>
                  {{ processing ? '处理中...' : '开始处理' }}
                </el-button>
              </div>

              <!-- 处理进度 -->
              <transition name="slide-up">
                <div v-if="taskStatus" class="progress-panel">
                  <div class="progress-header">
                    <span>处理进度</span>
                    <span class="progress-percent">{{ taskStatus.progress }}%</span>
                  </div>
                  <el-progress
                    :percentage="taskStatus.progress"
                    :status="taskStatus.status === 'completed' ? 'success' : (taskStatus.status === 'failed' ? 'exception' : '')"
                    :stroke-width="12"
                  />
                  <div class="progress-message">{{ taskStatus.message }}</div>

                  <div v-if="taskStatus.result" class="progress-result">
                    <el-icon class="result-icon"><SuccessFilled /></el-icon>
                    <span>已生成 {{ taskStatus.result.total_files }} 个文件</span>
                    <el-button type="primary" link @click="activeTab = 'files'">
                      查看文件 <el-icon><ArrowRight /></el-icon>
                    </el-button>
                  </div>
                </div>
              </transition>
            </div>
          </div>
        </transition>

        <!-- 文件管理页面 -->
        <transition name="fade" mode="out-in">
          <div v-if="activeTab === 'files'" class="page-content">
            <div class="files-header">
              <el-button @click="loadFiles" :icon="Refresh">刷新</el-button>
            </div>

            <div class="files-grid">
              <div
                v-for="file in files"
                :key="file.path"
                class="file-card"
              >
                <div class="file-icon">
                  <el-icon :size="40" :color="file.type === '.csv' ? '#67C23A' : '#409EFF'">
                    <Document />
                  </el-icon>
                </div>
                <div class="file-info">
                  <div class="file-name">{{ file.name }}</div>
                  <div class="file-meta">
                    <el-tag size="small" effect="plain">{{ file.device }}</el-tag>
                    <span class="file-size">{{ formatFileSize(file.size) }}</span>
                  </div>
                </div>
                <div class="file-actions">
                  <el-button size="small" text @click="downloadFile(file)">
                    <el-icon><Download /></el-icon>
                  </el-button>
                  <el-button size="small" text @click="visualizeFile(file)" v-if="file.type === '.csv'">
                    <el-icon><TrendCharts /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>

            <el-empty v-if="files.length === 0" description="暂无文件" />
          </div>
        </transition>

        <!-- 可视化页面 -->
        <transition name="fade" mode="out-in">
          <div v-if="activeTab === 'visualize'" class="page-content">
            <div v-if="!currentFile" class="empty-state">
              <el-empty description="请从文件管理页面选择一个CSV文件进行可视化" />
            </div>

            <div v-else class="visualize-panel">
              <div class="stats-cards">
                <div class="stat-card">
                  <div class="stat-label">总行数</div>
                  <div class="stat-value">{{ fileStats?.row_count || 0 }}</div>
                </div>
                <div class="stat-card">
                  <div class="stat-label">总列数</div>
                  <div class="stat-value">{{ fileStats?.column_count || 0 }}</div>
                </div>
                <div class="stat-card">
                  <div class="stat-label">文件设备</div>
                  <div class="stat-value">{{ currentFile.device }}</div>
                </div>
              </div>

              <div class="chart-container">
                <div ref="chartContainer" class="chart"></div>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import {
  Upload, Setting, Document, TrendCharts, Connection,
  UploadFilled, VideoPlay, Refresh, Download, Folder,
  CircleCheck, Check, SuccessFilled, ArrowRight
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 菜单配置
const menuItems = [
  { index: 'upload', label: '数据上传', icon: 'Upload', desc: '上传原始数据文件' },
  { index: 'process', label: '数据处理', icon: 'Setting', desc: '配置并执行处理流程' },
  { index: 'files', label: '文件管理', icon: 'Document', desc: '管理和下载处理结果' },
  { index: 'visualize', label: '数据可视化', icon: 'TrendCharts', desc: '图表展示传感器数据' }
]

const processSteps = [
  { value: 'split', label: '拆分设备数据', desc: '按设备分离 WTR1/WTL1/WTB1' },
  { value: 'align', label: '对齐气压计数据', desc: '同步气压计与 IMU 时间戳' },
  { value: 'downsample', label: '降采样到 50Hz', desc: '优化数据采样率' },
  { value: 'convert', label: '转换二进制格式', desc: '生成 .bin 协议文件' }
]

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

// 计算属性
const currentPageTitle = computed(() => {
  const item = menuItems.find(m => m.index === activeTab.value)
  return item?.label || ''
})

const currentPageDesc = computed(() => {
  const item = menuItems.find(m => m.index === activeTab.value)
  return item?.desc || ''
})

// 方法
const handleMenuSelect = (index) => {
  activeTab.value = index
  if (index === 'files') {
    loadFiles()
  }
}

const toggleStep = (step) => {
  const index = processForm.value.steps.indexOf(step)
  if (index > -1) {
    processForm.value.steps.splice(index, 1)
  } else {
    processForm.value.steps.push(step)
  }
}

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

const loadFiles = async () => {
  try {
    const { data } = await axios.get('/api/files')
    files.value = data.files
  } catch (error) {
    ElMessage.error('加载文件列表失败')
  }
}

const downloadFile = (file) => {
  window.open(`http://localhost:8000/api/download/${file.device}/${file.name}`, '_blank')
}

const visualizeFile = async (file) => {
  currentFile.value = file
  activeTab.value = 'visualize'

  try {
    const { data: stats } = await axios.get(`/api/stats/${file.device}/${file.name}`)
    fileStats.value = stats

    const { data: preview } = await axios.get(`/api/preview/${file.device}/${file.name}?limit=1000`)

    setTimeout(() => {
      renderChart(preview, stats)
    }, 100)
  } catch (error) {
    ElMessage.error('加载数据失败')
  }
}

const renderChart = (preview, stats) => {
  if (!chartContainer.value) return

  const chart = echarts.init(chartContainer.value)
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
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 600
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#ddd',
      borderWidth: 1,
      textStyle: {
        color: '#333'
      }
    },
    legend: {
      data: ['AccX', 'AccY', 'AccZ'],
      top: 40,
      itemGap: 20
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xData,
      name: '采样点',
      nameTextStyle: {
        fontSize: 12
      }
    },
    yAxis: {
      type: 'value',
      name: '加速度 (g)',
      nameTextStyle: {
        fontSize: 12
      }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        start: 0,
        end: 100,
        height: 30
      }
    ],
    series: [
      {
        name: 'AccX',
        type: 'line',
        data: accXData,
        smooth: true,
        symbolSize: 0,
        lineStyle: { width: 2 },
        color: '#5470c6'
      },
      {
        name: 'AccY',
        type: 'line',
        data: accYData,
        smooth: true,
        symbolSize: 0,
        lineStyle: { width: 2 },
        color: '#91cc75'
      },
      {
        name: 'AccZ',
        type: 'line',
        data: accZData,
        smooth: true,
        symbolSize: 0,
        lineStyle: { width: 2 },
        color: '#fac858'
      }
    ]
  }

  chart.setOption(option)
}

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
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 顶部导航栏 */
.app-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
  padding: 0;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 16px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.logo-text h1 {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
  line-height: 1.2;
}

.logo-text p {
  font-size: 12px;
  color: #6b7280;
  margin: 4px 0 0 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.badge-item {
  margin-right: 8px;
}

/* 主体内容 */
.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 32px;
  display: flex;
  gap: 24px;
  min-height: calc(100vh - 96px);
}

/* 侧边栏 */
.sidebar {
  width: 240px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.menu-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  color: #6b7280;
  font-size: 15px;
  font-weight: 500;
}

.menu-item:hover {
  background: #f3f4f6;
  color: #667eea;
}

.menu-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.menu-icon {
  flex-shrink: 0;
}

.menu-text {
  flex: 1;
}

.menu-indicator {
  width: 6px;
  height: 6px;
  background: white;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 内容区域 */
.content-area {
  flex: 1;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow-y: auto;
  max-height: calc(100vh - 144px);
}

.page-header {
  margin-bottom: 32px;
}

.page-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.page-header p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.page-content {
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 上传卡片 */
.upload-card {
  max-width: 800px;
  margin: 0 auto;
}

.upload-area {
  margin-bottom: 32px;
}

:deep(.el-upload-dragger) {
  border: 2px dashed #d1d5db;
  border-radius: 16px;
  background: #fafbfc;
  padding: 60px 40px;
  transition: all 0.3s;
}

:deep(.el-upload-dragger:hover) {
  border-color: #667eea;
  background: #f9fafb;
}

.upload-inner {
  text-align: center;
}

.upload-icon {
  font-size: 72px;
  color: #667eea;
  margin-bottom: 16px;
}

.upload-text {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 16px;
}

.upload-formats {
  font-size: 12px;
  color: #9ca3af;
  padding: 8px 16px;
  background: #f3f4f6;
  border-radius: 8px;
  display: inline-block;
}

/* 上传结果 */
.upload-result {
  background: #f9fafb;
  border-radius: 16px;
  padding: 24px;
  animation: slideUp 0.4s;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.result-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  font-size: 18px;
  font-weight: 600;
  color: #059669;
}

.success-icon {
  font-size: 28px;
}

.file-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.info-item {
  background: white;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.info-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.info-value {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.preview-section h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 16px 0;
}

/* 处理卡片 */
.process-card {
  max-width: 900px;
  margin: 0 auto;
}

.process-steps {
  display: grid;
  gap: 16px;
  margin-bottom: 32px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #fafbfc;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.step-item:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.step-item.active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border-color: #667eea;
}

.step-number {
  width: 40px;
  height: 40px;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #6b7280;
  flex-shrink: 0;
}

.step-item.active .step-number {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  color: white;
}

.step-content {
  flex: 1;
}

.step-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.step-desc {
  font-size: 13px;
  color: #6b7280;
}

.step-check {
  font-size: 24px;
  color: #667eea;
}

.process-actions {
  text-align: center;
  margin-bottom: 32px;
}

.process-actions .el-button {
  padding: 14px 40px;
  font-size: 16px;
}

/* 进度面板 */
.progress-panel {
  background: #f9fafb;
  border-radius: 16px;
  padding: 24px;
  animation: slideUp 0.4s;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.progress-percent {
  color: #667eea;
}

.progress-message {
  margin-top: 12px;
  font-size: 13px;
  color: #6b7280;
}

.progress-result {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
  padding: 16px;
  background: white;
  border-radius: 12px;
  border: 1px solid #d1fae5;
}

.result-icon {
  font-size: 24px;
  color: #10b981;
}

/* 文件网格 */
.files-header {
  margin-bottom: 24px;
}

.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.file-card {
  background: #fafbfc;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 20px;
  transition: all 0.3s;
  cursor: pointer;
}

.file-card:hover {
  border-color: #667eea;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
  transform: translateY(-4px);
}

.file-icon {
  margin-bottom: 16px;
}

.file-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
  word-break: break-all;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.file-size {
  font-size: 12px;
  color: #6b7280;
}

.file-actions {
  display: flex;
  gap: 8px;
}

/* 可视化面板 */
.visualize-panel {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 24px;
  color: white;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
}

.stat-label {
  font-size: 13px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
}

.chart-container {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.chart {
  width: 100%;
  height: 500px;
}

/* 过渡动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.4s;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* 滚动条样式 */
.content-area::-webkit-scrollbar {
  width: 8px;
}

.content-area::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.content-area::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
}

.content-area::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%);
}

.empty-state {
  padding: 80px 20px;
  text-align: center;
}
</style>
