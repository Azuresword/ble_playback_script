#!/usr/bin/env python3
"""
CSV 验证脚本 - 对比原始 txt 和生成的 CSV 文件是否一致
"""
import csv

TXT_FILE = 'data.txt'
CSV_FILE = 'data.csv'

def verify_files():
    """验证 txt 和 csv 文件内容是否一致"""
    print("=" * 60)
    print("开始验证 CSV 文件与原始 TXT 文件的一致性...")
    print("=" * 60)
    
    errors = []
    line_count = 0
    
    with open(TXT_FILE, 'r', encoding='utf-8') as txt_file:
        with open(CSV_FILE, 'r', encoding='utf-8') as csv_file:
            txt_reader = csv.reader(txt_file, delimiter='\t')
            csv_reader = csv.reader(csv_file)
            
            for txt_row, csv_row in zip(txt_reader, csv_reader):
                line_count += 1
                
                # 清理 txt 行末尾的 \r
                txt_row_clean = [cell.rstrip('\r') if cell.endswith('\r') else cell for cell in txt_row]
                
                # 比较行内容
                if txt_row_clean != csv_row:
                    errors.append({
                        'line': line_count,
                        'txt_cols': len(txt_row_clean),
                        'csv_cols': len(csv_row),
                        'txt_preview': txt_row_clean[:3],
                        'csv_preview': csv_row[:3]
                    })
                    
                    # 只记录前10个错误
                    if len(errors) >= 10:
                        break
                
                # 进度显示
                if line_count % 100000 == 0:
                    print(f"已验证 {line_count} 行...")
    
    # 检查行数是否一致
    txt_lines = sum(1 for _ in open(TXT_FILE, 'r', encoding='utf-8'))
    csv_lines = sum(1 for _ in open(CSV_FILE, 'r', encoding='utf-8'))
    
    print("\n" + "=" * 60)
    print("验证结果报告")
    print("=" * 60)
    print(f"原始 TXT 文件行数: {txt_lines}")
    print(f"生成 CSV 文件行数: {csv_lines}")
    print(f"行数一致: {'✓ 是' if txt_lines == csv_lines else '✗ 否'}")
    print(f"已验证行数: {line_count}")
    print(f"不一致行数: {len(errors)}")
    
    if errors:
        print("\n不一致的行 (前10个):")
        for err in errors:
            print(f"  行 {err['line']}: TXT列数={err['txt_cols']}, CSV列数={err['csv_cols']}")
            print(f"    TXT预览: {err['txt_preview']}")
            print(f"    CSV预览: {err['csv_preview']}")
        return False
    else:
        print("\n✓ 所有行验证通过！CSV 文件与原始 TXT 完全一致。")
        return True

def show_sample():
    """显示 CSV 文件的样本数据"""
    print("\n" + "=" * 60)
    print("CSV 文件样本数据 (前5行)")
    print("=" * 60)
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i >= 5:
                break
            if i == 0:
                print(f"表头 ({len(row)} 列):")
                for j, col in enumerate(row):
                    print(f"  [{j+1}] {col}")
            else:
                print(f"\n数据行 {i}: {row[:5]}...")

if __name__ == '__main__':
    result = verify_files()
    show_sample()
    
    print("\n" + "=" * 60)
    if result:
        print("验证状态: ✓ 通过")
    else:
        print("验证状态: ✗ 失败")
    print("=" * 60)
