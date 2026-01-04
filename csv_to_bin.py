#!/usr/bin/env python3
"""
将 CSV 文件转换为符合特定协议的二进制文件 (.bin)
协议格式: Header(2) + Cmd(1) + Len(1) + Payload(74) + CRC(2) = 80 Bytes
"""
import csv
import struct
import os
import glob

# 配置
FILES_TO_PROCESS = [
    'WTR1_data/WTR1.csv',
    'WTL1_data/WTL1.csv',
    'WTB1_data/WTB1.csv'
]

# 常量定义
HEADER0 = 0x55
HEADER1 = 0xAA
CMD_TYPE = 0x01
PAYLOAD_LEN = 74  # 0x4A
FRAME_LEN = 80

# CRC16-MODBUS 表 (也可实时计算，查表更快)
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

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_int(val, default=0):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

def process_single_file(csv_path):
    """处理单个 CSV 文件并生成 .bin"""
    if not os.path.exists(csv_path):
        print(f"✗ 找不到文件: {csv_path}")
        return False

    bin_path = os.path.splitext(csv_path)[0] + '.bin'
    print(f"➜ 正在处理: {csv_path}")
    print(f"  目标输出: {bin_path}")

    frame_count = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f_csv, open(bin_path, 'wb') as f_bin:
        reader = csv.DictReader(f_csv)
        
        # 预先构建 Header (前4字节)
        # B: uchar (1 byte), B: uchar, B: uchar, B: uchar
        header_bytes = struct.pack('<BBBB', HEADER0, HEADER1, CMD_TYPE, PAYLOAD_LEN)
        
        for row in reader:
            try:
                # 1. 提取並转换数据 (根据 Payload 定义)
                
                # Timestamp (8 bytes, uint64)
                ts = safe_int(row.get('time'), 0)
                
                # Acc (4 bytes each, int32) - 原始单位 g, 需转 m/s^2 (* 9.80665) 再 * 1000
                G_TO_MS2 = 9.80665
                acc_x = int(safe_float(row.get('AccX(g)')) * G_TO_MS2 * 1000)
                acc_y = int(safe_float(row.get('AccY(g)')) * G_TO_MS2 * 1000)
                acc_z = int(safe_float(row.get('AccZ(g)')) * G_TO_MS2 * 1000)
                
                # Gyro (4 bytes each, int32) - 原始单位 deg/s, * 1000
                gyro_x = int(safe_float(row.get('AsX(°/s)')) * 1000)
                gyro_y = int(safe_float(row.get('AsY(°/s)')) * 1000)
                gyro_z = int(safe_float(row.get('AsZ(°/s)')) * 1000)
                
                # Mag (4 bytes each, int32) - 原始单位 uT, * 100
                mag_x = int(safe_float(row.get('HX(uT)')) * 100)
                mag_y = int(safe_float(row.get('HY(uT)')) * 100)
                mag_z = int(safe_float(row.get('HZ(uT)')) * 100)
                
                # Euler (4 bytes each, int32) - 原始单位 deg, * 10000
                roll = int(safe_float(row.get('AngleX(°)')) * 10000)
                pitch = int(safe_float(row.get('AngleY(°)')) * 10000)
                yaw = int(safe_float(row.get('AngleZ(°)')) * 10000)
                
                # GPS (4 bytes each, int32) - 暂无数据，填 0
                gps_lat = 0
                gps_lon = 0
                gps_speed = 0
                
                # Pressure (4 bytes, int32) - 原始单位 hPa (mbar), * 100
                # 注意: align_barometer.py 添加的列名为 'pressure'
                pressure = int(safe_float(row.get('pressure', 0)) * 100)
                
                # Temp (2 bytes, int16) - 原始单位 C, * 100
                temp = int(safe_float(row.get('Temperature(°C)')) * 100)
                
                # 2. 打包 Payload
                # Python struct 格式化字符:
                # <: Little Endian
                # Q: uint64 (8)
                # i: int32 (4)
                # h: int16 (2)
                
                payload_fmt = '<Q iii iii iii iii iii i h'
                payload_data = struct.pack(
                    payload_fmt,
                    ts,
                    acc_x, acc_y, acc_z,
                    gyro_x, gyro_y, gyro_z,
                    mag_x, mag_y, mag_z,
                    roll, pitch, yaw,
                    gps_lat, gps_lon, gps_speed,
                    pressure,
                    temp
                )
                
                if len(payload_data) != PAYLOAD_LEN:
                    print(f"⚠️ Payload 长度错误: {len(payload_data)}, 预期 {PAYLOAD_LEN}")
                    return False

                # 3. 计算 CRC (Range: Cmd + Len + Payload)
                #Exclude Header0 (0x55) and Header1 (0xAA) from CRC
                data_to_checksum = header_bytes[2:] + payload_data
                crc = calculate_crc16(data_to_checksum)
                crc_bytes = struct.pack('<H', crc) # H: uint16
                
                # 4. 写入文件 (全帧: Header + Payload + CRC)
                full_frame = header_bytes + payload_data + crc_bytes
                f_bin.write(full_frame)
                
                frame_count += 1
                
            except Exception as e:
                print(f"⚠️ 处理行 {frame_count+1} 时出错: {e}")
                continue

    file_size = os.path.getsize(bin_path)
    print(f"  ✓ 完成。生成 {frame_count} 帧")
    print(f"  文件大小: {file_size / 1024 / 1024:.2f} MB")
    
    # 简单验证文件大小
    expected_size = frame_count * FRAME_LEN
    if file_size == expected_size:
        print(f"  验证通过: 文件大小正确 ({file_size} bytes)")
    else:
        print(f"  ⚠️ 验证失败: 文件大小 {file_size} != 预期 {expected_size}")
        
    return True

def main():
    print("=" * 60)
    print("CSV 转 二进制文件 (Protocol Bin) 工具")
    print(f"帧长度: {FRAME_LEN} 字节 (Payload: {PAYLOAD_LEN})")
    print("=" * 60)
    
    success_count = 0
    for csv_file in FILES_TO_PROCESS:
        if process_single_file(csv_file):
            success_count += 1
            
    print("\n" + "=" * 60)
    print(f"全部完成! 成功: {success_count}/{len(FILES_TO_PROCESS)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
