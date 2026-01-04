# BLE 数据回放脚本工具

用于处理 BLE (蓝牙低功耗) IMU 传感器数据的工具集，支持数据格式转换、校验、对齐和降采样。

## 快速开始

### 🌐 Web 界面（推荐）

启动现代化的 Web 界面，图形化操作更简单：

```bash
./start_web.sh
```

启动后访问：
- **前端界面**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs

**功能特性**：
- ✨ 拖拽上传数据文件
- 📊 实时处理进度显示
- 📁 文件管理和下载
- 📈 数据可视化（ECharts 图表）
- 🎯 一键式操作流程

### 命令行一键运行

```bash
./run.sh
```

这个脚本会自动执行完整的数据处理流程：
1. 拆分设备数据 (WTR1/WTL1/WTB1)
2. 对齐气压计数据
3. 降采样到 50Hz
4. 生成二进制文件 (.bin)
5. 可选：运行验证测试

### 手动执行步骤

```bash
# 1. 拆分设备数据
python3 split_by_device.py

# 2. 对齐气压计数据
python3 align_barometer.py

# 3. 降采样到 50Hz（会自动生成 bin 文件）
python3 downsample_50hz.py

# 4. 验证转换结果
python3 bin_to_csv.py WTR1_data/WTR1_50hz.bin -c WTR1_data/WTR1_50hz.csv
```

## 前置要求

### 命令行工具
- Python 3.6+
- 输入数据文件：`data.csv` 或 `data.txt`
- 可选：`bmp/Barometer.csv` (气压计数据)

### Web 应用
- Python 3.6+
- Node.js 14+ 和 npm
- 自动安装依赖：
  ```bash
  pip install -r requirements.txt  # Python 依赖
  cd web && npm install           # 前端依赖
  ```

## 输出文件

运行完成后，会在设备文件夹中生成以下文件：

```
WTR1_data/
├── WTR1.csv          # 拆分后的原始数据
├── WTR1_50hz.csv     # 降采样到 50Hz
└── WTR1_50hz.bin     # 二进制协议格式

WTL1_data/
├── WTL1.csv
├── WTL1_50hz.csv
└── WTL1_50hz.bin

WTB1_data/
├── WTB1.csv
├── WTB1_50hz.csv
└── WTB1_50hz.bin
```

## 工具说明

### 数据处理工具

- `split_by_device.py` - 按设备拆分数据
- `align_barometer.py` - 对齐气压计数据
- `downsample_50hz.py` - 降采样到 50Hz
- `csv_to_bin.py` - CSV 转二进制格式
- `bin_to_csv.py` - 二进制转 CSV（验证用）

### 验证工具

- `verify_timestamp.py` - 验证时间戳格式
- `verify_csv.py` - 验证 CSV 结构
- `verify_split.py` - 验证拆分结果
- `verify_conversion_schema.py` - 验证转换模式
- `compare_datasets.py` - 对比数据集
- `compare_acc.py` - 对比加速度数据

### 其他工具

- `convert_timestamp.py` - 时间戳格式转换
- `convert_to_csv.py` - 通用格式转换

## 二进制协议格式

每帧 80 字节，结构如下：

```
Header (2B)  + Cmd (1B) + Len (1B) + Payload (74B) + CRC (2B)
0x55 0xAA      0x01       0x4A       [数据]          CRC16
```

Payload 包含：
- 时间戳 (8B, uint64, 微秒)
- 加速度 (12B, int32×3, m/s² × 1000)
- 陀螺仪 (12B, int32×3, deg/s × 1000)
- 磁力计 (12B, int32×3, uT × 100)
- 欧拉角 (12B, int32×3, deg × 10000)
- GPS (12B, int32×3)
- 气压 (4B, int32, hPa × 100)
- 温度 (2B, int16, °C × 100)

## 常见问题

### 1. 脚本没有执行权限

```bash
chmod +x run.sh
```

### 2. 找不到数据文件

确保在项目根目录有 `data.csv` 或 `data.txt` 文件。

### 3. 验证 BIN 文件

```bash
python3 bin_to_csv.py <file.bin> -c <original.csv>
```

## 项目结构

```
.
├── start_web.sh              # Web 应用启动脚本 ⭐
├── run.sh                    # 命令行一键启动脚本
├── app.py                    # FastAPI 后端服务
├── requirements.txt          # Python 依赖
├── web/                      # Vue 3 前端项目
│   ├── src/
│   │   ├── App.vue          # 主应用组件
│   │   └── main.js          # 入口文件
│   ├── package.json
│   └── vite.config.js
├── CLAUDE.md                 # 项目架构文档
├── README.md                 # 本文件
├── data.csv                  # 原始数据（忽略）
├── split_by_device.py        # 拆分脚本
├── align_barometer.py        # 对齐脚本
├── downsample_50hz.py        # 降采样脚本
├── csv_to_bin.py             # 转换脚本
├── bin_to_csv.py             # 验证脚本
├── verify_*.py               # 验证工具
├── compare_*.py              # 对比工具
├── WTR1_data/                # 右腕数据
├── WTL1_data/                # 左腕数据
├── WTB1_data/                # 腰部数据
├── bmp/                      # 气压计数据
└── ref_algo/                 # 参考算法
```

## 技术栈

### 后端
- **FastAPI** - 现代化的 Python Web 框架
- **Uvicorn** - ASGI 服务器
- **Pandas** - 数据处理

### 前端
- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 下一代前端构建工具
- **Element Plus** - Vue 3 组件库
- **ECharts** - 数据可视化图表库
- **Axios** - HTTP 客户端

## 许可证

本项目用于 BLE 数据处理和分析。
