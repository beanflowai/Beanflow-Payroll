#!/bin/bash

# BeanFlow Payroll 开发环境停止脚本
# 安全停止所有开发服务并清理缓存

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Ports
BACKEND_PORT=8040
FRONTEND_PORT=5176

# PID files
BACKEND_PID_FILE="/tmp/beanflow-payroll-backend.pid"
FRONTEND_PID_FILE="/tmp/beanflow-payroll-frontend.pid"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  BeanFlow Payroll Stop Script         ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ==================== 安全进程终止函数 ====================

safe_kill_pid() {
    local pid=$1
    local name=$2

    # 检查进程是否存在
    if ! kill -0 "$pid" 2>/dev/null; then
        return 0
    fi

    echo -e "   Stopping $name (PID $pid)..."

    # 先发送 SIGTERM，给进程优雅退出的机会
    kill -TERM "$pid" 2>/dev/null || true

    # 等待进程退出（最多 5 秒）
    local wait_count=0
    while kill -0 "$pid" 2>/dev/null && [ $wait_count -lt 10 ]; do
        sleep 0.5
        wait_count=$((wait_count + 1))
    done

    # 如果进程还在，才使用 SIGKILL
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "   ${YELLOW}Force stopping $name (PID $pid)...${NC}"
        kill -KILL "$pid" 2>/dev/null || true
    fi
}

safe_stop_port() {
    local port=$1
    local name=$2

    local pids=$(lsof -ti:"$port" 2>/dev/null || true)

    if [ -z "$pids" ]; then
        echo -e "   $name (port $port) not running"
        return 0
    fi

    echo -e "${YELLOW}Stopping $name (port $port)...${NC}"
    for pid in $pids; do
        safe_kill_pid "$pid" "$name"
    done
}

# ==================== 1. 停止服务 ====================
echo -e "${YELLOW}=== Stopping services ===${NC}"

# 使用 PID 文件停止
if [ -f "$BACKEND_PID_FILE" ]; then
    pid=$(cat "$BACKEND_PID_FILE")
    safe_kill_pid "$pid" "Backend (from PID file)"
    rm -f "$BACKEND_PID_FILE"
fi

if [ -f "$FRONTEND_PID_FILE" ]; then
    pid=$(cat "$FRONTEND_PID_FILE")
    safe_kill_pid "$pid" "Frontend (from PID file)"
    rm -f "$FRONTEND_PID_FILE"
fi

# 按端口停止（处理 PID 文件丢失的情况）
safe_stop_port $BACKEND_PORT "Backend API"
safe_stop_port $FRONTEND_PORT "Frontend"

# ==================== 2. 清理缓存 ====================
echo ""
echo -e "${YELLOW}=== Cleaning caches ===${NC}"

# 清理后端 Python 缓存
echo "Cleaning backend Python cache..."
find "$BACKEND_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$BACKEND_DIR" -name "*.pyc" -type f -delete 2>/dev/null || true
find "$BACKEND_DIR" -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
find "$BACKEND_DIR" -name ".mypy_cache" -type d -exec rm -rf {} + 2>/dev/null || true
find "$BACKEND_DIR" -name ".ruff_cache" -type d -exec rm -rf {} + 2>/dev/null || true
echo -e "   ${GREEN}Backend cache cleaned${NC}"

# 清理前端缓存
if [ -d "$FRONTEND_DIR" ]; then
    echo "Cleaning frontend cache..."
    rm -rf "$FRONTEND_DIR/node_modules/.cache" 2>/dev/null || true
    rm -rf "$FRONTEND_DIR/node_modules/.vite" 2>/dev/null || true
    rm -rf "$FRONTEND_DIR/.svelte-kit" 2>/dev/null || true
    echo -e "   ${GREEN}Frontend cache cleaned${NC}"
fi

# ==================== 3. 验证端口状态 ====================
echo ""
echo -e "${YELLOW}=== Verifying port status ===${NC}"

check_port() {
    local port=$1
    local name=$2
    local pid=$(lsof -ti:$port 2>/dev/null || true)

    if [ -n "$pid" ]; then
        echo -e "   ${RED}WARNING: $name (port $port) still occupied by PID $pid${NC}"
    else
        echo -e "   ${GREEN}OK: $name (port $port) released${NC}"
    fi
}

check_port $BACKEND_PORT "Backend API"
check_port $FRONTEND_PORT "Frontend"

# ==================== 完成 ====================
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}BeanFlow Payroll development stopped${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "To restart, run:"
echo "   ./start-dev.sh"
echo ""
