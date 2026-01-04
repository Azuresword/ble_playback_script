#!/usr/bin/env python3
"""
将 data.txt (Tab分隔) 转换为 CSV 格式
"""
import csv

INPUT_FILE = 'data.txt'
OUTPUT_FILE = 'data.csv'

def convert_txt_to_csv():
    """将 Tab 分隔的 txt 文件转换为 CSV"""
    with open(INPUT_FILE, 'r', encoding='utf-8') as infile:
        with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as outfile:
            reader = csv.reader(infile, delimiter='\t')
            writer = csv.writer(outfile)
            
            line_count = 0
            for row in reader:
                # 移除每行末尾可能的 \r
                if row and row[-1].endswith('\r'):
                    row[-1] = row[-1].rstrip('\r')
                writer.writerow(row)
                line_count += 1
                
                # 每10万行打印进度
                if line_count % 100000 == 0:
                    print(f"已处理 {line_count} 行...")
    
    print(f"转换完成！共处理 {line_count} 行")
    print(f"输出文件: {OUTPUT_FILE}")
    return line_count

if __name__ == '__main__':
    convert_txt_to_csv()
