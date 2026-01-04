# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 BLE (蓝牙低功耗) 数据回放脚本工具集，用于处理 IMU (惯性测量单元) 传感器数据。主要功能包括数据格式转换、校验、对齐和降采样。

## 核心数据流

```
原始数据 (data.csv/data.txt)
    ↓
split_by_device.py → 按设备拆分 (WTR1/WTL1/WTB1)
    ↓
align_barometer.py → 对齐气压计数据
    ↓
downsample_50hz.py → 降采样到 50Hz
    ↓
csv_to_bin.py → 转换为二进制协议格式 (.bin)
    ↓
bin_to_csv.py → 反向转换验证
```

## 二进制协议格式

协议帧结构（80 字节）：
- Header: 2 bytes (0x55, 0xAA)
- Cmd: 1 byte (0x01)
- Len: 1 byte (0x4A = 74)
- Payload: 74 bytes
  - timestamp: 8 bytes (uint64, 微秒)
  - acc_xyz: 12 bytes (int32×3, m/s² × 1000)
  - gyro_xyz: 12 bytes (int32×3, deg/s × 1000)
  - mag_xyz: 12 bytes (int32×3, uT × 100)
  - euler_xyz: 12 bytes (int32×3, deg × 10000)
  - gps: 12 bytes (int32×3, lat/lon/speed)
  - pressure: 4 bytes (int32, hPa × 100)
  - temperature: 2 bytes (int16, °C × 100)
- CRC: 2 bytes (CRC16-MODBUS, 计算范围: Cmd+Len+Payload)

## 常用命令

### 数据处理流程

```bash
# 1. 拆分设备数据
python3 split_by_device.py

# 2. 对齐气压计数据
python3 align_barometer.py

# 3. 降采样到 50Hz（会自动调用 csv_to_bin.py）
python3 downsample_50hz.py

# 4. 单独转换 CSV 到 BIN
python3 csv_to_bin.py

# 5. 验证 BIN 文件（反向转换并对比）
python3 bin_to_csv.py <file.bin> -c <original.csv>
```

### 数据验证

```bash
# 验证时间戳格式
python3 verify_timestamp.py

# 验证 CSV 结构
python3 verify_csv.py

# 验证拆分结果
python3 verify_split.py

# 对比数据集
python3 compare_datasets.py
```

## 关键实现细节

### 时间戳对齐

- **气压计时间戳**: 19位纳秒级 (需除以 1000 转为微秒)
- **IMU 时间戳**: 16位微秒级
- **对齐方法**: 使用二分查找 (`bisect_left`) 找到最接近的数据点
- **占位符**: 无效气压数据使用 `10000.0`，降采样后转为 `0`

### 数据转换系数

在 `csv_to_bin.py` 和 `bin_to_csv.py` 中：
- **加速度**: g → m/s² (×9.80665) → int32 (×1000)
- **陀螺仪**: deg/s → int32 (×1000)
- **磁力计**: uT → int32 (×100)
- **欧拉角**: deg → int32 (×10000)
- **气压**: hPa → int32 (×100)
- **温度**: °C → int16 (×100)

### 降采样策略

`downsample_50hz.py` 的特殊逻辑：
1. 保留所有有效气压数据行（必须保留）
2. 对于无气压数据的行，每 2 个取 1 个
3. 不伪造任何数据，只选择原始数据点
4. 完成后自动调用 `csv_to_bin.py` 生成二进制文件

### 设备名称

- **WTR1**: 右腕设备
- **WTL1**: 左腕设备
- **WTB1**: 腰部设备

## 已知问题

参考 `data_comparison_report_v2.md`：
1. **加速度异常**: App数据的加速度值范围 (±39g) 远大于正常 IMU 量程 (±4g)，可能存在单位换算错误
2. **采样率差异**: 原始数据 ~99.2Hz，App数据 ~120.4Hz

## 目录结构

- `WTR1_data/`, `WTL1_data/`, `WTB1_data/`: 拆分后的设备数据（*.csv, *.bin）
- `bmp/`: 气压计数据
- `ref_algo/`: 参考算法（数据导入和查询工具）
- `data_from_app/`: App端数据
- `pref_data/`: 偏好/参考数据
