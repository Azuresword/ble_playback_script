# 数据比较报告

## 概述
本报告对比了工作区中发现的"原始数据"文件（`data.csv`、`data.txt`、`WTB1_data/`）与"App数据"文件（`data_from_app/`）的结构和内容。

## 数据源

### 原始数据 (Original Data)
*   **文件**: `data.csv`, `data.txt` (内容完全相同), `WTB1_data/WTB1.csv` (特定设备的子集，包含额外列)。
*   **时间戳**: 2025年10月30日。
*   **格式**: 逗号分隔 (CSV) / 制表符分隔 (TXT)。
*   **结构**: 包含传感器读数（IMU）+ 衍生数据（如速度/轨迹）的组合数据。

### App数据 (App Data)
*   **文件**: `data_from_app/barometer_data_202512101933.csv`, `data_from_app/imu_data_202512101934.csv`。
*   **时间戳**: 2025年12月10日。
*   **格式**: 逗号分隔 (CSV)。
*   **结构**: 按传感器类型拆分标识符（IMU文件 vs 气压计文件）。

## 主要差异

### 1. 日期和会话
两个数据集来自完全不同的会话（相隔约1.5个月）。由于它们代表不同的物理事件，**无法进行直接的数值逐行比较**。

### 2. 文件组织
*   **原始数据**: 将所有传感器和衍生数据聚合到每个时间戳的单行中（主要是这样）。`WTB1.csv` 在末尾包含了气压/海拔数据。
*   **App数据**: 按传感器类型将数据分离到不同的文件中（`imu_data...csv` 与 `barometer_data...csv`）。

### 3. 列模式 (Schema) 比较

| 特性 | 原始数据 (`data.csv` / `WTB1.csv`) | App数据 (`imu_data...csv`) | 备注 |
| :--- | :--- | :--- | :--- |
| **命名规范** | PascalCase / 带单位的CamelCase (如 `AccX(g)`) | snake_case (如 `acc_x`) | App数据表头不带单位标签。 |
| **标识** | `DeviceName` (如 `WTR1(ID)`) | `device_id`, `user_id`, `session_id`, `id` (UUIDs) | App使用UUID；原始数据使用名称+MAC。 |
| **IMU: 加速度** | `AccX(g)`, `AccY(g)`, `AccZ(g)` | `acc_x`, `acc_y`, `acc_z` | |
| **IMU: 陀螺仪** | `AsX(°/s)`, `AsY(°/s)`, `AsZ(°/s)` | `gyro_x`, `gyro_y`, `gyro_z` | 原始用"As"，App用"gyro"。 |
| **IMU: 磁力计** | `HX(uT)`, `HY(uT)`, `HZ(uT)` | `mag_x`, `mag_y`, `mag_z` | 原始用"H"，App用"mag"。 |
| **方向 (Orientation)** | `AngleX/Y/Z` (欧拉角), `Q0/1/2/3` (四元数) | `euler_x/y/z` (欧拉角), `quaternion_w/x/y/z` | Q0 通常对应 w 或标量部分。 |
| **气压计** | `pressure` (仅在 `WTB1.csv` 中，不在 `data.csv` 中) | `pressure` (在 `barometer_data...csv` 中) | `data.csv` 缺少气压数据。 |
| **衍生数据** | `TrajectoryX/Y/Z` (轨迹), `SpeedX/Y/Z` (速度) | *不存在* | App数据仅包含原始传感器数据。 |
| **元数据** | `Version`, `Battery level(%)` | `battery_level` | App数据在IMU文件中包含 `battery_level`。 |

## 结论
由于记录会话不同，"原始数据"和"App数据"不兼容，无法进行直接的逐行比较。App数据采用了更现代、规范化的数据库风格模式（snake_case命名、UUID、分表存储），而原始数据似乎是为直接绘图/分析设计的原始转储或导出格式，包含了合并字段和衍生指标（速度、轨迹）。
