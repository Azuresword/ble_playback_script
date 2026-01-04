#!/usr/bin/env python3
"""
将二进制文件 (.bin) 反向转换为 CSV 文件进行校验
协议格式: Header(2) + Cmd(1) + Len(1) + Payload(74) + CRC(2) = 80 Bytes
"""
import csv
import struct
import os
import sys

# 常量定义
HEADER0 = 0x55
HEADER1 = 0xAA
CMD_TYPE = 0x01
PAYLOAD_LEN = 74  # 0x4A
FRAME_LEN = 80

# CRC16-MODBUS 表
CRC16_TABLE = [
    0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241,
    0xC601, 0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440,
    0xCC01, 0x0CC0, 0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40,
    0x0A00, 0xCAC1, 0xCB81, 0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841,
    0xD801, 0x18C0, 0x1980, 0xD941, 0x1B00, 0xDBC1, 0xDA81, 0x1A40,
    0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01, 0x1DC0, 0x1C80, 0xDC41,
    0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0, 0x1680, 0xD641,
    0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081, 0x1040,
    0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
    0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441,
    0x3C00, 0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41,
    0xFA01, 0x3AC0, 0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840,
    0x2800, 0xE8C1, 0xE981, 0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41,
    0xEE01, 0x2EC0, 0x2F80, 0xEF41, 0x2D00, 0xEDC1, 0xEC81, 0x2C40,
    0xE401, 0x24C0, 0x2580, 0xE541, 0x2700, 0xE7C1, 0xE681, 0x2640,
    0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0, 0x2080, 0xE041,
    0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281, 0x6240,
    0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
    0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41,
    0xAA01, 0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840,
    0x7800, 0xB8C1, 0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41,
    0xBE01, 0x7EC0, 0x7F80, 0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40,
    0xB401, 0x74C0, 0x7580, 0xB541, 0x7700, 0xB7C1, 0xB681, 0x7640,
    0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101, 0x71C0, 0x7080, 0xB041,
    0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0, 0x5280, 0x9241,
    0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440,
    0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
    0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841,
    0x8801, 0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40,
    0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41,
    0x4400, 0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641,
    0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040
]

def calculate_crc16(data: bytes) -> int:
    """计算 CRC-16/MODBUS"""
    crc = 0xFFFF
    for byte in data:
        idx = (crc ^ byte) & 0xFF
        crc = (crc >> 8) ^ CRC16_TABLE[idx]
    return crc

def parse_frame(frame_data: bytes):
    """
    解析单帧数据
    返回: (是否有效, 解析后的数据字典, 错误信息)
    """
    if len(frame_data) != FRAME_LEN:
        return False, None, f"帧长度错误: {len(frame_data)}"
    
    # 1. 验证帧头
    if frame_data[0] != HEADER0 or frame_data[1] != HEADER1:
        return False, None, f"帧头错误: {frame_data[0]:02X} {frame_data[1]:02X}"
    
    # 2. 验证 Cmd 和 Len
    cmd = frame_data[2]
    payload_len = frame_data[3]
    if cmd != CMD_TYPE:
        return False, None, f"Cmd 错误: {cmd:02X}"
    if payload_len != PAYLOAD_LEN:
        return False, None, f"Payload 长度错误: {payload_len}"
    
    # 3. 验证 CRC
    payload = frame_data[4:4+PAYLOAD_LEN]
    received_crc = struct.unpack('<H', frame_data[78:80])[0]
    data_to_checksum = frame_data[2:78]  # Cmd + Len + Payload
    calculated_crc = calculate_crc16(data_to_checksum)
    
    crc_valid = (received_crc == calculated_crc)
    
    # 4. 解析 Payload
    # Payload 格式: Q iii iii iii iii iii i h
    # timestamp(8) + acc(12) + gyro(12) + mag(12) + euler(12) + gps(12) + pressure(4) + temp(2) = 74
    payload_fmt = '<Q iii iii iii iii iii i h'
    unpacked = struct.unpack(payload_fmt, payload)
    
    # 反向转换系数
    G_TO_MS2 = 9.80665
    
    data = {
        'time': unpacked[0],
        # Acc: bin中为 m/s^2 * 1000, 需转回 g
        'AccX(g)': unpacked[1] / 1000.0 / G_TO_MS2,
        'AccY(g)': unpacked[2] / 1000.0 / G_TO_MS2,
        'AccZ(g)': unpacked[3] / 1000.0 / G_TO_MS2,
        # Gyro: bin中为 deg/s * 1000
        'AsX(°/s)': unpacked[4] / 1000.0,
        'AsY(°/s)': unpacked[5] / 1000.0,
        'AsZ(°/s)': unpacked[6] / 1000.0,
        # Mag: bin中为 uT * 100
        'HX(uT)': unpacked[7] / 100.0,
        'HY(uT)': unpacked[8] / 100.0,
        'HZ(uT)': unpacked[9] / 100.0,
        # Euler: bin中为 deg * 10000
        'AngleX(°)': unpacked[10] / 10000.0,
        'AngleY(°)': unpacked[11] / 10000.0,
        'AngleZ(°)': unpacked[12] / 10000.0,
        # GPS: 原始值
        'GPS_Lat': unpacked[13],
        'GPS_Lon': unpacked[14],
        'GPS_Speed': unpacked[15],
        # Pressure: bin中为 hPa * 100
        'pressure': unpacked[16] / 100.0,
        # Temp: bin中为 °C * 100
        'Temperature(°C)': unpacked[17] / 100.0,
        # 额外信息
        '__crc_valid': crc_valid,
        '__received_crc': received_crc,
        '__calculated_crc': calculated_crc,
        # 原始整数值 (用于调试)
        '__raw_acc_x': unpacked[1],
        '__raw_acc_y': unpacked[2],
        '__raw_acc_z': unpacked[3],
    }
    
    return True, data, None

def convert_bin_to_csv(bin_path, csv_path=None, include_raw=False):
    """
    将 bin 文件转换为 csv
    :param bin_path: 输入的 bin 文件路径
    :param csv_path: 输出的 csv 文件路径 (默认: bin文件同名.csv)
    :param include_raw: 是否包含原始整数值列
    """
    if not os.path.exists(bin_path):
        print(f"✗ 找不到文件: {bin_path}")
        return False
    
    if csv_path is None:
        csv_path = os.path.splitext(bin_path)[0] + '_from_bin.csv'
    
    file_size = os.path.getsize(bin_path)
    expected_frames = file_size // FRAME_LEN
    
    print(f"=" * 60)
    print(f"BIN -> CSV 转换 & 校验工具")
    print(f"=" * 60)
    print(f"➜ 输入文件: {bin_path}")
    print(f"  文件大小: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
    print(f"  预期帧数: {expected_frames}")
    print(f"➜ 输出文件: {csv_path}")
    print()
    
    # 检查文件大小是否为帧长度的整数倍
    if file_size % FRAME_LEN != 0:
        print(f"⚠️ 警告: 文件大小 {file_size} 不是帧长度 {FRAME_LEN} 的整数倍!")
        print(f"   余数: {file_size % FRAME_LEN} bytes")
    
    # CSV 字段
    fieldnames = [
        'time',
        'AccX(g)', 'AccY(g)', 'AccZ(g)',
        'AsX(°/s)', 'AsY(°/s)', 'AsZ(°/s)',
        'HX(uT)', 'HY(uT)', 'HZ(uT)',
        'AngleX(°)', 'AngleY(°)', 'AngleZ(°)',
        'GPS_Lat', 'GPS_Lon', 'GPS_Speed',
        'pressure', 'Temperature(°C)',
    ]
    
    if include_raw:
        fieldnames.extend(['__raw_acc_x', '__raw_acc_y', '__raw_acc_z'])
    
    # 统计
    total_frames = 0
    valid_frames = 0
    crc_errors = 0
    parse_errors = 0
    
    with open(bin_path, 'rb') as f_bin, open(csv_path, 'w', newline='', encoding='utf-8') as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
        writer.writeheader()
        
        while True:
            frame_data = f_bin.read(FRAME_LEN)
            if not frame_data:
                break
            if len(frame_data) < FRAME_LEN:
                print(f"⚠️ 帧 {total_frames + 1}: 数据不完整 ({len(frame_data)} bytes)")
                break
            
            total_frames += 1
            is_valid, data, error = parse_frame(frame_data)
            
            if not is_valid:
                parse_errors += 1
                if parse_errors <= 10:
                    print(f"⚠️ 帧 {total_frames}: {error}")
                continue
            
            if not data['__crc_valid']:
                crc_errors += 1
                if crc_errors <= 10:
                    print(f"⚠️ 帧 {total_frames}: CRC 错误 "
                          f"(接收: {data['__received_crc']:04X}, "
                          f"计算: {data['__calculated_crc']:04X})")
            
            valid_frames += 1
            
            # 写入 CSV (只写入需要的字段)
            row = {k: v for k, v in data.items() if k in fieldnames}
            writer.writerow(row)
    
    # 打印统计
    print()
    print(f"=" * 60)
    print(f"转换完成!")
    print(f"=" * 60)
    print(f"  总帧数: {total_frames}")
    print(f"  有效帧: {valid_frames}")
    print(f"  解析错误: {parse_errors}")
    print(f"  CRC 错误: {crc_errors}")
    
    if parse_errors > 0 or crc_errors > 0:
        print()
        print(f"⚠️ 检测到 {parse_errors + crc_errors} 个错误!")
        return False
    else:
        print()
        print(f"✓ 全部帧校验通过!")
        return True

def compare_csv_files(original_csv, converted_csv, tolerance=1e-6):
    """
    对比原始 CSV 和从 bin 转换回来的 CSV
    """
    print()
    print(f"=" * 60)
    print(f"CSV 对比校验")
    print(f"=" * 60)
    print(f"  原始 CSV: {original_csv}")
    print(f"  转换 CSV: {converted_csv}")
    print()
    
    if not os.path.exists(original_csv):
        print(f"✗ 找不到原始文件: {original_csv}")
        return False
    if not os.path.exists(converted_csv):
        print(f"✗ 找不到转换文件: {converted_csv}")
        return False
    
    # 读取两个文件
    with open(original_csv, 'r', encoding='utf-8') as f:
        original_rows = list(csv.DictReader(f))
    with open(converted_csv, 'r', encoding='utf-8') as f:
        converted_rows = list(csv.DictReader(f))
    
    print(f"  原始行数: {len(original_rows)}")
    print(f"  转换行数: {len(converted_rows)}")
    
    if len(original_rows) != len(converted_rows):
        print(f"⚠️ 行数不匹配!")
    
    # 要对比的字段
    compare_fields = [
        'time',
        'AccX(g)', 'AccY(g)', 'AccZ(g)',
        'AsX(°/s)', 'AsY(°/s)', 'AsZ(°/s)',
        'HX(uT)', 'HY(uT)', 'HZ(uT)',
        'AngleX(°)', 'AngleY(°)', 'AngleZ(°)',
        'pressure', 'Temperature(°C)',
    ]
    
    mismatches = 0
    max_errors = {}  # 每个字段的最大误差
    
    for i, (orig, conv) in enumerate(zip(original_rows, converted_rows)):
        for field in compare_fields:
            orig_val = orig.get(field, '0')
            conv_val = conv.get(field, '0')
            
            try:
                orig_num = float(orig_val) if orig_val else 0.0
                conv_num = float(conv_val) if conv_val else 0.0
            except ValueError:
                continue
            
            # 计算相对误差或绝对误差
            if abs(orig_num) > 1e-10:
                rel_error = abs(orig_num - conv_num) / abs(orig_num)
            else:
                rel_error = abs(orig_num - conv_num)
            
            abs_error = abs(orig_num - conv_num)
            
            # 记录最大误差
            if field not in max_errors:
                max_errors[field] = {'rel': 0, 'abs': 0, 'row': 0}
            if rel_error > max_errors[field]['rel']:
                max_errors[field]['rel'] = rel_error
                max_errors[field]['abs'] = abs_error
                max_errors[field]['row'] = i
                max_errors[field]['orig'] = orig_num
                max_errors[field]['conv'] = conv_num
            
            # 检查是否超过容差 (整数转换会有精度损失)
            # 对于时间戳，使用精确匹配
            if field == 'time':
                if orig_num != conv_num:
                    mismatches += 1
                    if mismatches <= 5:
                        print(f"  行 {i+1}, {field}: 原始={orig_num}, 转换={conv_num}")
    
    # 打印最大误差
    print()
    print("字段最大误差:")
    print("-" * 80)
    print(f"{'字段':<20} {'相对误差':<15} {'绝对误差':<15} {'原始值':<15} {'转换值':<15}")
    print("-" * 80)
    for field in compare_fields:
        if field in max_errors:
            e = max_errors[field]
            print(f"{field:<20} {e['rel']:.6e}  {e['abs']:.6e}  {e.get('orig', 0):.6f}  {e.get('conv', 0):.6f}")
    
    print()
    if mismatches == 0:
        print("✓ 所有数据匹配 (在整数转换精度范围内)!")
        return True
    else:
        print(f"⚠️ 发现 {mismatches} 处不匹配")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='将 BIN 文件转换为 CSV 并校验')
    parser.add_argument('bin_file', help='输入的 BIN 文件路径')
    parser.add_argument('-o', '--output', help='输出的 CSV 文件路径')
    parser.add_argument('-c', '--compare', help='用于对比的原始 CSV 文件')
    parser.add_argument('--raw', action='store_true', help='包含原始整数值')
    
    args = parser.parse_args()
    
    # 转换
    success = convert_bin_to_csv(args.bin_file, args.output, args.raw)
    
    # 如果指定了对比文件，进行对比
    if args.compare and success:
        output_csv = args.output or (os.path.splitext(args.bin_file)[0] + '_from_bin.csv')
        compare_csv_files(args.compare, output_csv)

if __name__ == "__main__":
    main()
