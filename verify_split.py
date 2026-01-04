#!/usr/bin/env python3
"""
验证拆分后的数据是否与原始数据完全一致
确保不丢失任何数据
"""
import csv
import os

ORIGINAL_FILE = 'data.csv'

DEVICE_FILES = {
    'WTR1': 'WTR1_data/WTR1.csv',
    'WTL1': 'WTL1_data/WTL1.csv',
    'WTB1': 'WTB1_data/WTB1.csv'
}

def verify_split():
    """验证拆分后的数据完整性"""
    print("=" * 70)
    print("开始验证拆分数据的完整性...")
    print("=" * 70)
    
    # 1. 读取原始数据，按设备分组
    print("\n[步骤1] 读取原始数据并按设备分组...")
    original_data = {device: [] for device in DEVICE_FILES}
    original_header = None
    unknown_rows = []
    
    with open(ORIGINAL_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        original_header = next(reader)
        
        for row in reader:
            device_name = row[1] if len(row) > 1 else ''
            matched = False
            for prefix in DEVICE_FILES:
                if device_name.startswith(prefix):
                    original_data[prefix].append(tuple(row))
                    matched = True
                    break
            if not matched:
                unknown_rows.append(row)
    
    print(f"  原始数据表头列数: {len(original_header)}")
    for device, rows in original_data.items():
        print(f"  原始 {device} 行数: {len(rows)}")
    if unknown_rows:
        print(f"  ⚠️ 未匹配设备行数: {len(unknown_rows)}")
    
    # 2. 读取拆分后的数据
    print("\n[步骤2] 读取拆分后的各设备文件...")
    split_data = {}
    split_headers = {}
    
    for device, filepath in DEVICE_FILES.items():
        if not os.path.exists(filepath):
            print(f"  ✗ 文件不存在: {filepath}")
            return False
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            split_headers[device] = next(reader)
            split_data[device] = [tuple(row) for row in reader]
        
        print(f"  {device}: {len(split_data[device])} 行 (文件: {filepath})")
    
    # 3. 验证表头一致性
    print("\n[步骤3] 验证表头一致性...")
    header_match = True
    for device, header in split_headers.items():
        if header != original_header:
            print(f"  ✗ {device} 表头不一致!")
            header_match = False
        else:
            print(f"  ✓ {device} 表头一致")
    
    # 4. 验证行数
    print("\n[步骤4] 验证行数...")
    count_match = True
    for device in DEVICE_FILES:
        orig_count = len(original_data[device])
        split_count = len(split_data[device])
        if orig_count != split_count:
            print(f"  ✗ {device}: 原始 {orig_count} 行 ≠ 拆分 {split_count} 行")
            count_match = False
        else:
            print(f"  ✓ {device}: {orig_count} 行 一致")
    
    # 5. 逐行验证数据内容
    print("\n[步骤5] 逐行验证数据内容...")
    content_match = True
    
    for device in DEVICE_FILES:
        orig_rows = original_data[device]
        split_rows = split_data[device]
        
        mismatches = []
        for i, (orig, split) in enumerate(zip(orig_rows, split_rows)):
            if orig != split:
                mismatches.append(i + 1)
                if len(mismatches) >= 5:  # 只记录前5个
                    break
        
        if mismatches:
            print(f"  ✗ {device}: 发现 {len(mismatches)} 行不匹配 (行号: {mismatches[:5]}...)")
            content_match = False
        else:
            print(f"  ✓ {device}: 所有 {len(orig_rows)} 行内容完全一致")
    
    # 6. 验证总行数
    print("\n[步骤6] 验证总行数...")
    original_total = sum(len(rows) for rows in original_data.values()) + len(unknown_rows)
    split_total = sum(len(rows) for rows in split_data.values())
    
    print(f"  原始数据总行数（不含表头）: {original_total}")
    print(f"  拆分数据总行数（不含表头）: {split_total}")
    
    # 7. 最终结果
    print("\n" + "=" * 70)
    print("验证结果汇总")
    print("=" * 70)
    
    all_pass = header_match and count_match and content_match and len(unknown_rows) == 0
    
    checks = [
        ("表头一致性", header_match),
        ("行数一致性", count_match),
        ("内容一致性", content_match),
        ("无未知设备", len(unknown_rows) == 0),
        ("总行数一致", original_total == split_total)
    ]
    
    for name, passed in checks:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {name}: {status}")
    
    print("\n" + "=" * 70)
    if all_pass:
        print("🎉 验证通过！所有数据完整，无任何丢失！")
    else:
        print("❌ 验证失败！请检查上述问题。")
    print("=" * 70)
    
    return all_pass

if __name__ == '__main__':
    verify_split()
