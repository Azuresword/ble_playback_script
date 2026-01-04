#!/usr/bin/env python3
"""
将气压计数据根据时间戳对齐并添加到 WTR1, WTL1, WTB1 文件中

气压计时间戳格式: 19位纳秒级 (如 1761820447850108400)
设备时间戳格式: 16位微秒级 (如 1761820435980000)

对齐策略: 二分查找精确插入
- 对每条气压计数据，用二分查找找到 IMU 数据中时间戳最接近的那行
- 只有这一行填入气压计数据，其他行全部填 0
"""
import csv
import os
from bisect import bisect_left

# 文件路径
BAROMETER_FILE = 'bmp/Barometer.csv'
DEVICE_FILES = [
    'WTR1_data/WTR1.csv',
    'WTL1_data/WTL1.csv',
    'WTB1_data/WTB1.csv'
]

def load_barometer_data():
    """加载气压计数据，返回 (时间戳列表[us], 数据列表[(sec, alt, press), ...])"""
    print("加载气压计数据...")
    
    timestamps = []
    values = []
    
    with open(BAROMETER_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        print(f"  气压计表头: {header}")
        
        for row in reader:
            if not row or len(row) < 4:
                continue
            
            try:
                # 将19位纳秒时间戳转换为16位微秒时间戳
                ts_ns = int(row[0])
                ts_us = ts_ns // 1000  # 纳秒 -> 微秒
                
                seconds_elapsed = float(row[1])
                relative_altitude = float(row[2])
                pressure = float(row[3])
                
                timestamps.append(ts_us)
                values.append((seconds_elapsed, relative_altitude, pressure))
            except ValueError:
                continue
    
    # 排序
    combined = sorted(zip(timestamps, values), key=lambda x: x[0])
    timestamps = [x[0] for x in combined]
    values = [x[1] for x in combined]
    
    print(f"  加载 {len(timestamps)} 条气压计数据")
    if timestamps:
        print(f"  时间范围: {min(timestamps)} ~ {max(timestamps)} (us)")
    
    return timestamps, values

def find_closest_index(target_ts, timestamps):
    """二分查找找到最接近目标时间戳的索引"""
    if not timestamps:
        return -1
    
    pos = bisect_left(timestamps, target_ts)
    
    if pos == 0:
        return 0
    if pos == len(timestamps):
        return len(timestamps) - 1
    
    before = timestamps[pos - 1]
    after = timestamps[pos]
    
    if target_ts - before <= after - target_ts:
        return pos - 1
    else:
        return pos

def process_device_file(filepath, baro_timestamps, baro_values):
    """处理单个设备文件"""
    print(f"\n处理文件: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"  ✗ 文件不存在!")
        return False
    
    # Step 1: 读取 IMU 数据，获取所有时间戳
    imu_timestamps = []
    imu_rows = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            print("  空文件")
            return False
        
        base_header_len = 27
        
        for row in reader:
            if not row:
                continue
            base_row = row[:base_header_len]
            try:
                ts = int(base_row[0])
                imu_timestamps.append(ts)
                imu_rows.append(base_row)
            except (ValueError, IndexError):
                imu_timestamps.append(0)
                imu_rows.append(base_row)
    
    print(f"  读取 {len(imu_rows)} 行 IMU 数据")
    
    # Step 2: 为每行 IMU 数据初始化气压值为 10000 (表示无效/占位)
    DEFAULT_VAL = 10000.0
    baro_data_for_imu = [(DEFAULT_VAL, DEFAULT_VAL, DEFAULT_VAL)] * len(imu_rows)
    
    # Step 3: 对每条气压计数据，找到最接近的 IMU 行并填入
    matched_count = 0
    for i, baro_ts in enumerate(baro_timestamps):
        # 找到最接近的 IMU 行索引
        closest_idx = find_closest_index(baro_ts, imu_timestamps)
        
        if closest_idx >= 0 and closest_idx < len(imu_rows):
            # 只有当该位置尚未被填充时才填入（或者覆盖也可以）
            # 这里选择直接覆盖
            baro_data_for_imu[closest_idx] = baro_values[i]
            matched_count += 1
    
    print(f"  成功匹配 {matched_count} 条气压计数据到 IMU 行")
    
    # Step 4: 写回文件
    new_header = header[:base_header_len] + ['seconds_elapsed', 'relativeAltitude', 'pressure']
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(new_header)
        
        for i, base_row in enumerate(imu_rows):
            sec, alt, pres = baro_data_for_imu[i]
            # 格式化 - 10000 表示无效占位值
            s_elapsed = f"{sec:.3f}"
            rel_alt = f"{alt:.3f}"
            pressure = f"{pres:.2f}"
            
            new_row = base_row + [s_elapsed, rel_alt, pressure]
            writer.writerow(new_row)
    
    # 统计有多少行有有效气压数据
    non_zero_count = sum(1 for v in baro_data_for_imu if v[2] != 0.0)
    print(f"  ✓ 完成! 共 {len(imu_rows)} 行, 其中 {non_zero_count} 行有气压数据, {len(imu_rows) - non_zero_count} 行填 0")
    
    return True

def main():
    print("=" * 70)
    print("气压计数据对齐 (二分查找精确插入版)")
    print("=" * 70)
    
    if not os.path.exists(BAROMETER_FILE):
        print(f"✗ 气压计文件不存在: {BAROMETER_FILE}")
        return False
    
    baro_timestamps, baro_values = load_barometer_data()
    
    success_count = 0
    for filepath in DEVICE_FILES:
        if process_device_file(filepath, baro_timestamps, baro_values):
            success_count += 1
            
    print("\n" + "=" * 70)
    print(f"处理完成! 成功: {success_count}/{len(DEVICE_FILES)}")
    print("=" * 70)

if __name__ == '__main__':
    main()
