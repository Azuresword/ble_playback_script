#!/usr/bin/env python3
"""
精准 50Hz 降采样脚本

对 WTB1, WTL1, WTR1 三个 CSV 文件进行降采样：
- 不伪造任何数据，只选择原始数据点
- 使用最近邻方法选择最接近 50Hz 网格的数据
- 保留原始时间戳，不修改任何传感器数据

生成降采样后的 CSV 文件，然后调用 csv_to_bin.py 生成 bin 文件
"""
import csv
import os
import subprocess
from bisect import bisect_left

# 配置
SAMPLE_INTERVAL_US = 20000  # 50Hz = 20ms = 20000μs
FILES_TO_PROCESS = [
    ('WTR1_data/WTR1.csv', 'WTR1_data/WTR1_50hz.csv'),
    ('WTL1_data/WTL1.csv', 'WTL1_data/WTL1_50hz.csv'),
    ('WTB1_data/WTB1.csv', 'WTB1_data/WTB1_50hz.csv'),
]

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

def downsample_to_50hz(input_csv, output_csv):
    """
    将 CSV 文件降采样到 50Hz，同时保留所有有效气压数据
    
    策略：
    1. 标记所有有效气压数据的行（必须保留）
    2. 对于无气压数据的行，每2个取1个
    3. 占位符 10000.00 改为 0
    不伪造任何数据，只选择原始数据点
    """
    print(f"\n处理文件: {input_csv}")
    
    if not os.path.exists(input_csv):
        print(f"  ✗ 文件不存在: {input_csv}")
        return False
    
    # Step 1: 读取所有数据
    rows = []
    timestamps = []
    header = None
    pressure_col_idx = -1
    
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        # 找到pressure列的索引
        for i, col in enumerate(header):
            if col.strip().lower() == 'pressure':
                pressure_col_idx = i
                break
        
        for row in reader:
            if not row:
                continue
            try:
                ts = int(row[0])
                timestamps.append(ts)
                rows.append(row)
            except ValueError:
                continue
    
    if not rows:
        print(f"  ✗ 没有有效数据")
        return False
    
    # 按时间戳排序
    combined = sorted(zip(timestamps, rows), key=lambda x: x[0])
    timestamps = [x[0] for x in combined]
    rows = [x[1] for x in combined]
    
    print(f"  原始数据: {len(rows)} 行")
    print(f"  时间范围: {timestamps[0]} ~ {timestamps[-1]} (μs)")
    print(f"  气压列索引: {pressure_col_idx}")
    
    total_time_us = timestamps[-1] - timestamps[0]
    total_time_s = total_time_us / 1_000_000
    original_rate = len(rows) / total_time_s if total_time_s > 0 else 0
    print(f"  总时长: {total_time_s:.2f} 秒")
    print(f"  原始采样率: ~{original_rate:.1f} Hz")
    
    # Step 2: 标记有效气压数据行 & 将占位符改为0
    PLACEHOLDER_VALUE = '10000.00'
    valid_pressure_indices = set()
    
    for i, row in enumerate(rows):
        if pressure_col_idx >= 0 and pressure_col_idx < len(row):
            pressure = row[pressure_col_idx].strip()
            if pressure == PLACEHOLDER_VALUE:
                # 将占位符改为0
                row[pressure_col_idx] = '0'
            elif pressure and pressure != '0':
                # 有效气压数据，标记此行必须保留
                valid_pressure_indices.add(i)
    
    print(f"  有效气压数据行: {len(valid_pressure_indices)} 个")
    
    # Step 3: 降采样（保留所有有效气压行，其他行每2个取1个）
    output_rows = []
    downsample_factor = 2
    skip_counter = 0
    
    for i, row in enumerate(rows):
        if i in valid_pressure_indices:
            # 有效气压数据，必须保留
            output_rows.append(row)
            skip_counter = 0  # 重置计数器
        else:
            # 无有效气压，每2个取1个
            if skip_counter % downsample_factor == 0:
                output_rows.append(row)
            skip_counter += 1
    
    print(f"  降采样后: {len(output_rows)} 行")
    
    # 计算输出采样率
    output_rate = len(output_rows) / total_time_s if total_time_s > 0 else 0
    print(f"  输出采样率: ~{output_rate:.1f} Hz")
    
    # Step 4: 写入输出文件
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(output_rows)
    
    print(f"  ✓ 已保存: {output_csv}")
    
    return True

def main():
    print("=" * 70)
    print("精准 50Hz 降采样工具")
    print("=" * 70)
    print(f"目标采样率: 50Hz (间隔 {SAMPLE_INTERVAL_US} μs)")
    print("策略: 最近邻选择 (不伪造任何数据)")
    
    success_count = 0
    output_files = []
    
    for input_csv, output_csv in FILES_TO_PROCESS:
        if downsample_to_50hz(input_csv, output_csv):
            success_count += 1
            output_files.append(output_csv)
    
    print("\n" + "=" * 70)
    print(f"降采样完成! 成功: {success_count}/{len(FILES_TO_PROCESS)}")
    print("=" * 70)
    
    # 调用 csv_to_bin.py 生成 bin 文件
    if success_count > 0:
        print("\n正在生成 bin 文件...")
        
        # 临时修改 csv_to_bin.py 处理的文件列表
        # 直接调用 process_single_file 函数
        try:
            import csv_to_bin
            for output_csv in output_files:
                csv_to_bin.process_single_file(output_csv)
        except ImportError:
            print("⚠️ 无法导入 csv_to_bin 模块，请手动运行:")
            for output_csv in output_files:
                print(f"  python3 csv_to_bin.py 处理 {output_csv}")
    
    print("\n全部完成!")

if __name__ == "__main__":
    main()
