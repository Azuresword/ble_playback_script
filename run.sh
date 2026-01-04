#!/bin/bash
# BLE 数据处理一键启动脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_step() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# 检查 Python3 是否安装
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装，请先安装 Python3"
        exit 1
    fi
    print_info "Python 版本: $(python3 --version)"
}

# 检查必需文件
check_files() {
    print_step "步骤 0: 检查必需文件"

    local missing_files=0

    # 检查数据文件
    if [ ! -f "data.csv" ] && [ ! -f "data.txt" ]; then
        print_error "找不到数据文件 (data.csv 或 data.txt)"
        missing_files=$((missing_files + 1))
    else
        print_success "数据文件存在"
    fi

    # 检查气压计文件（可选）
    if [ ! -f "bmp/Barometer.csv" ]; then
        print_warning "找不到气压计文件 (bmp/Barometer.csv)，将跳过气压计对齐步骤"
    else
        print_success "气压计文件存在"
    fi

    # 检查脚本文件
    local scripts=("split_by_device.py" "align_barometer.py" "downsample_50hz.py" "csv_to_bin.py")
    for script in "${scripts[@]}"; do
        if [ ! -f "$script" ]; then
            print_error "找不到脚本: $script"
            missing_files=$((missing_files + 1))
        fi
    done

    if [ $missing_files -gt 0 ]; then
        print_error "缺少 $missing_files 个必需文件，退出"
        exit 1
    fi

    print_success "所有必需文件检查完成"
}

# 主处理流程
main() {
    clear
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║     BLE 数据处理工具 - 一键启动脚本                   ║"
    echo "║     BLE Playback Script - Auto Runner                  ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    check_python
    check_files

    # 步骤 1: 拆分设备数据
    print_step "步骤 1: 拆分设备数据 (split_by_device.py)"
    if python3 split_by_device.py; then
        print_success "设备数据拆分完成"
    else
        print_error "设备数据拆分失败"
        exit 1
    fi

    # 步骤 2: 对齐气压计数据（如果存在）
    if [ -f "bmp/Barometer.csv" ]; then
        print_step "步骤 2: 对齐气压计数据 (align_barometer.py)"
        if python3 align_barometer.py; then
            print_success "气压计数据对齐完成"
        else
            print_error "气压计数据对齐失败"
            exit 1
        fi
    else
        print_step "步骤 2: 跳过气压计对齐（文件不存在）"
    fi

    # 步骤 3: 降采样到 50Hz 并生成 bin 文件
    print_step "步骤 3: 降采样到 50Hz 并生成 BIN 文件 (downsample_50hz.py)"
    if python3 downsample_50hz.py; then
        print_success "降采样和 BIN 文件生成完成"
    else
        print_error "降采样失败"
        exit 1
    fi

    # 完成
    echo ""
    print_step "🎉 所有步骤完成！"
    echo ""
    print_info "生成的文件:"
    echo "  • WTR1_data/WTR1.csv, WTR1_50hz.csv, WTR1_50hz.bin"
    echo "  • WTL1_data/WTL1.csv, WTL1_50hz.csv, WTL1_50hz.bin"
    echo "  • WTB1_data/WTB1.csv, WTB1_50hz.csv, WTB1_50hz.bin"
    echo ""

    # 询问是否验证
    read -p "是否运行验证测试？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_verification
    fi
}

# 验证功能
run_verification() {
    print_step "验证数据"

    # 验证时间戳
    if [ -f "verify_timestamp.py" ]; then
        print_info "验证时间戳格式..."
        python3 verify_timestamp.py
    fi

    # 验证拆分结果
    if [ -f "verify_split.py" ]; then
        print_info "验证拆分结果..."
        python3 verify_split.py
    fi

    # 验证 BIN 文件（反向转换）
    if [ -f "bin_to_csv.py" ]; then
        print_info "验证 WTR1_50hz.bin..."
        python3 bin_to_csv.py WTR1_data/WTR1_50hz.bin -c WTR1_data/WTR1_50hz.csv
    fi

    print_success "验证完成"
}

# 处理 Ctrl+C
trap 'echo ""; print_warning "用户中断"; exit 130' INT

# 执行主函数
main "$@"
