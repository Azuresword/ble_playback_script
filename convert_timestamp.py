#!/usr/bin/env python3
"""
将三个设备CSV文件中的时间列转换为13位毫秒级时间戳
时间格式: "2025-10-30 18:33:55.98" -> 1730281235980
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

def parse_time_to_timestamp(time_str):
    """
    将时间字符串转换为16位微秒级时间戳
    输入格式: "2025-10-30 18:33:55.98" 或 "2025-10-30 18:33:55.980"
    输出: 16位微秒时间戳 (字符串)
    """
    try:
        # 分离日期时间和微秒部分
        if '.' in time_str:
            main_part, frac_part = time_str.rsplit('.', 1)
            # 补齐微秒到6位
            frac_part = frac_part.ljust(6, '0')[:6]
        else:
            main_part = time_str
            frac_part = '000000'
        
        # 解析日期时间
        dt = datetime.strptime(main_part, '%Y-%m-%d %H:%M:%S')
        
        # 转换为时间戳（秒）并添加微秒
        timestamp_sec = int(dt.timestamp())
        timestamp_us = timestamp_sec * 1000000 + int(frac_part)
        
        return str(timestamp_us)
    except Exception as e:
        print(f"  ⚠️ 时间解析失败: '{time_str}' - {e}")
        return time_str  # 返回原值

def convert_file(filepath):
    """转换单个文件的时间列"""
    print(f"\n处理文件: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"  ✗ 文件不存在!")
        return False
    
    # 读取所有数据
    rows = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows.append(header)
        
        row_count = 0
        for row in reader:
            row_count += 1
            
            # 转换第一列（时间列）
            if row and len(row) > 0:
                original_time = row[0]
                row[0] = parse_time_to_timestamp(original_time)
            
            rows.append(row)
            
            # 进度显示
            if row_count % 50000 == 0:
                print(f"  已处理 {row_count} 行...")
    
    # 写回文件（覆盖）
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    print(f"  ✓ 完成! 共转换 {row_count} 行数据")
    
    # 显示转换示例
    if len(rows) > 1:
        print(f"  示例: {rows[1][0]} (第一行数据的时间戳)")
    
    return True

def main():
    print("=" * 60)
    print("时间格式转换 - 转为13位毫秒时间戳")
    print("=" * 60)
    
    success_count = 0
    
    for filepath in DEVICE_FILES:
        if convert_file(filepath):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"转换完成! 成功: {success_count}/{len(DEVICE_FILES)} 个文件")
    print("=" * 60)
    
    return success_count == len(DEVICE_FILES)

if __name__ == '__main__':
    main()
