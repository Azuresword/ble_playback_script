#!/usr/bin/env python3
"""
按设备拆分 CSV 数据到不同文件夹
"""
import csv
import os

INPUT_FILE = 'data.csv'

# 设备名称到文件夹的映射
DEVICE_FOLDERS = {
    'WTR1': 'WTR1_data',
    'WTL1': 'WTL1_data', 
    'WTB1': 'WTB1_data'
}

def split_by_device():
    """按设备拆分数据"""
    
    # 创建文件夹
    for folder in DEVICE_FOLDERS.values():
        os.makedirs(folder, exist_ok=True)
        print(f"创建文件夹: {folder}/")
    
    # 打开所有输出文件
    files = {}
    writers = {}
    header = None
    device_counts = {device: 0 for device in DEVICE_FOLDERS}
    unknown_devices = {}
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        
        # 读取表头
        header = next(reader)
        print(f"\n表头: {len(header)} 列")
        
        # 为每个设备创建输出文件并写入表头
        for device, folder in DEVICE_FOLDERS.items():
            output_path = os.path.join(folder, f'{device}.csv')
            files[device] = open(output_path, 'w', encoding='utf-8', newline='')
            writers[device] = csv.writer(files[device])
            writers[device].writerow(header)
            print(f"创建文件: {output_path}")
        
        # 处理数据行
        total_rows = 0
        for row in reader:
            total_rows += 1
            
            # 获取设备名称（第2列，索引1）
            device_name = row[1] if len(row) > 1 else ''
            
            # 提取设备前缀（如 WTR1(xxx) -> WTR1）
            device_prefix = None
            for prefix in DEVICE_FOLDERS:
                if device_name.startswith(prefix):
                    device_prefix = prefix
                    break
            
            if device_prefix:
                writers[device_prefix].writerow(row)
                device_counts[device_prefix] += 1
            else:
                # 记录未知设备
                if device_name not in unknown_devices:
                    unknown_devices[device_name] = 0
                unknown_devices[device_name] += 1
            
            # 进度显示
            if total_rows % 100000 == 0:
                print(f"已处理 {total_rows} 行...")
    
    # 关闭所有文件
    for f in files.values():
        f.close()
    
    # 打印统计
    print("\n" + "=" * 60)
    print("拆分统计")
    print("=" * 60)
    print(f"原始数据总行数（不含表头）: {total_rows}")
    
    split_total = 0
    for device, count in device_counts.items():
        print(f"  {device}: {count} 行")
        split_total += count
    
    print(f"拆分后总行数: {split_total}")
    
    if unknown_devices:
        print(f"\n⚠️ 未知设备:")
        for dev, count in unknown_devices.items():
            print(f"  {dev}: {count} 行")
    
    # 验证
    if split_total == total_rows and not unknown_devices:
        print(f"\n✓ 数据完整！拆分行数 ({split_total}) = 原始行数 ({total_rows})")
        return True, device_counts, total_rows
    else:
        print(f"\n✗ 数据不完整！拆分行数 ({split_total}) ≠ 原始行数 ({total_rows})")
        return False, device_counts, total_rows

if __name__ == '__main__':
    split_by_device()
