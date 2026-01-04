#!/bin/bash
# Web 应用启动脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║     BLE 数据处理平台 - Web 应用启动脚本              ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    print_error "Python3 未安装"
    exit 1
fi
print_success "Python3 已安装"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js 未安装，请先安装 Node.js"
    exit 1
fi
print_success "Node.js 已安装: $(node --version)"

# 检查 npm
if ! command -v npm &> /dev/null; then
    print_error "npm 未安装"
    exit 1
fi
print_success "npm 已安装: $(npm --version)"

# 安装 Python 依赖
print_info "检查 Python 依赖..."
if [ ! -d "venv" ]; then
    print_info "创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
print_info "安装 Python 依赖包..."
pip install -q -r requirements.txt
print_success "Python 依赖安装完成"

# 安装前端依赖
print_info "检查前端依赖..."
cd web
if [ ! -d "node_modules" ]; then
    print_info "安装前端依赖包（这可能需要几分钟）..."
    npm install
    print_success "前端依赖安装完成"
else
    print_success "前端依赖已安装"
fi
cd ..

# 启动后端
print_info "启动后端服务..."
source venv/bin/activate
python3 app.py &
BACKEND_PID=$!
sleep 2

if ps -p $BACKEND_PID > /dev/null; then
    print_success "后端服务已启动 (PID: $BACKEND_PID)"
    echo "      访问地址: http://localhost:8000"
    echo "      API 文档: http://localhost:8000/docs"
else
    print_error "后端服务启动失败"
    exit 1
fi

# 启动前端
print_info "启动前端开发服务器..."
cd web
npm run dev &
FRONTEND_PID=$!
cd ..

sleep 3
if ps -p $FRONTEND_PID > /dev/null; then
    print_success "前端服务已启动 (PID: $FRONTEND_PID)"
    echo "      访问地址: http://localhost:3000"
else
    print_error "前端服务启动失败"
    kill $BACKEND_PID
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 应用启动成功！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "  前端地址: http://localhost:3000"
echo "  后端地址: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"
echo ""
echo "  按 Ctrl+C 停止服务"
echo ""

# 保存 PID 到文件
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

# 等待用户中断
trap 'echo ""; print_info "正在停止服务..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f .backend.pid .frontend.pid; print_success "服务已停止"; exit 0' INT

wait
