#!/usr/bin/env python3
"""
验证时间戳转换是否正确
1. 检查时间戳格式是否为13位数字
2. 检查时间戳是否在合理范围内
3. 抽样验证转换的正确性
"""
import csv
import os
from datetime import datetime

# 设备文件列表
DEVICE_FILES = [
    'WTR1_data/WTR1.csv',
    'WTL1_data/WTL1.csv',
    'WTB1_data/WTB1.csv'
]

# 原始CSV文件用于对比
ORIGINAL_FILE = 'data.csv'

def timestamp_to_datetime(ts_str):
    """将13位时间戳转换为datetime对象"""
    ts_ms = int(ts_str)
    ts_sec = ts_ms / 1000
    return datetime.fromtimestamp(ts_sec)

def verify_file(filepath):
    """验证单个文件的时间戳"""
    print(f"\n验证文件: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"  ✗ 文件不存在!")
        return False
    
    errors = []
    valid_count = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        print(f"  时间列标题: '{header[0]}'")
        
        for i, row in enumerate(reader, start=2):  # 从第2行开始（跳过表头）
            if not row or len(row) == 0:
                continue
            
            ts = row[0]
            
            # 检查1: 是否为13位数字
            if not ts.isdigit() or len(ts) != 13:
                errors.append(f"行{i}: 非13位数字 '{ts}'")
                if len(errors) >= 10:
                    break
                continue
            
            # 检查2: 时间戳范围（2020年1月1日 - 2030年1月1日）
            ts_val = int(ts)
            min_ts = 1577836800000  # 2020-01-01 00:00:00
            max_ts = 1893456000000  # 2030-01-01 00:00:00
            
            if ts_val < min_ts or ts_val > max_ts:
                errors.append(f"行{i}: 时间戳超出范围 '{ts}'")
                if len(errors) >= 10:
                    break
                continue
            
            valid_count += 1
    
    if errors:
        print(f"  ✗ 发现 {len(errors)} 个错误:")
        for err in errors[:5]:
            print(f"    - {err}")
        if len(errors) > 5:
            print(f"    ... 还有 {len(errors) - 5} 个错误")
        return False
    else:
        print(f"  ✓ 所有 {valid_count} 行时间戳格式正确!")
        
        # 显示时间范围
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 跳过表头
            first_row = next(reader)
            first_ts = first_row[0]
            
            # 读取最后一行
            for last_row in reader:
                pass
            last_ts = last_row[0]
        
        first_dt = timestamp_to_datetime(first_ts)
        last_dt = timestamp_to_datetime(last_ts)
        
        print(f"  时间范围: {first_dt} ~ {last_dt}")
        print(f"  时间戳范围: {first_ts} ~ {last_ts}")
        
        return True

def verify_against_original():
    """与原始数据对比验证（抽样）"""
    print("\n" + "=" * 60)
    print("抽样对比验证 - 与原始数据对比")
    print("=" * 60)
    
    if not os.path.exists(ORIGINAL_FILE):
        print(f"原始文件 {ORIGINAL_FILE} 不存在，跳过对比验证")
        return True
    
    # 读取原始数据的前10行
    original_samples = {}
    with open(ORIGINAL_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        sample_count = 0
        for row in reader:
            if sample_count >= 30:  # 每个设备取约10个样本
                break
            device = row[1] if len(row) > 1 else ''
            time_str = row[0] if len(row) > 0 else ''
            
            for prefix in ['WTR1', 'WTL1', 'WTB1']:
                if device.startswith(prefix):
                    if prefix not in original_samples:
                        original_samples[prefix] = []
                    if len(original_samples[prefix]) < 3:
                        original_samples[prefix].append(time_str)
            sample_count += 1
    
    # 读取转换后的数据进行对比
    all_match = True
    for device, times in original_samples.items():
        filepath = f"{device}_data/{device}.csv"
        if not os.path.exists(filepath):
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 跳过表头
            
            converted_times = []
            for i, row in enumerate(reader):
                if i >= len(times):
                    break
                converted_times.append(row[0])
        
        print(f"\n{device} 抽样对比:")
        for orig, conv in zip(times, converted_times):
            # 验证转换是否正确
            try:
                # 解析原始时间
                if '.' in orig:
                    main_part, ms_part = orig.rsplit('.', 1)
                    ms_part = ms_part.ljust(3, '0')[:3]
                else:
                    main_part = orig
                    ms_part = '000'
                
                dt = datetime.strptime(main_part, '%Y-%m-%d %H:%M:%S')
                expected_ts = int(dt.timestamp()) * 1000 + int(ms_part)
                
                if str(expected_ts) == conv:
                    print(f"  ✓ '{orig}' -> {conv}")
                else:
                    print(f"  ✗ '{orig}' 期望 {expected_ts}, 实际 {conv}")
                    all_match = False
            except Exception as e:
                print(f"  ⚠️ 验证失败: {e}")
    
    return all_match

def main():
    print("=" * 60)
    print("时间戳转换验证")
    print("=" * 60)
    
    all_valid = True
    
    for filepath in DEVICE_FILES:
        if not verify_file(filepath):
            all_valid = False
    
    # 与原始数据对比
    if not verify_against_original():
        all_valid = False
    
    print("\n" + "=" * 60)
    if all_valid:
        print("🎉 验证通过！所有时间戳转换正确！")
    else:
        print("❌ 验证失败！请检查上述问题。")
    print("=" * 60)
    
    return all_valid

if __name__ == '__main__':
    main()
