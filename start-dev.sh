#!/bin/bash
# BeanFlow Payroll Development Server Startup Script
# Starts both backend (FastAPI) and frontend (SvelteKit) servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Ports
BACKEND_PORT=8040
FRONTEND_PORT=5176

# PID files for cleanup
BACKEND_PID_FILE="/tmp/beanflow-payroll-backend.pid"
FRONTEND_PID_FILE="/tmp/beanflow-payroll-frontend.pid"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"

    if [ -f "$BACKEND_PID_FILE" ]; then
        kill $(cat "$BACKEND_PID_FILE") 2>/dev/null || true
        rm -f "$BACKEND_PID_FILE"
    fi

    if [ -f "$FRONTEND_PID_FILE" ]; then
        kill $(cat "$FRONTEND_PID_FILE") 2>/dev/null || true
        rm -f "$FRONTEND_PID_FILE"
    fi

    # Kill any remaining processes on the ports
    lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
    lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true

    echo -e "${GREEN}Servers stopped.${NC}"
    exit 0
}

# Set up trap for cleanup on exit
trap cleanup SIGINT SIGTERM EXIT

# Check if ports are available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}Error: Port $port is already in use${NC}"
        echo "Run: lsof -i:$port to see what's using it"
        exit 1
    fi
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  BeanFlow Payroll Development Server  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check ports
echo -e "${YELLOW}Checking ports...${NC}"
check_port $BACKEND_PORT
check_port $FRONTEND_PORT
echo -e "${GREEN}Ports $BACKEND_PORT and $FRONTEND_PORT are available${NC}"
echo ""

# Start Backend
echo -e "${YELLOW}Starting Backend (FastAPI) on port $BACKEND_PORT...${NC}"
cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    uv venv
    uv sync
fi

uv run uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload &
BACKEND_PID=$!
echo $BACKEND_PID > "$BACKEND_PID_FILE"
echo -e "${GREEN}Backend started (PID: $BACKEND_PID)${NC}"
echo ""

# Wait for backend to be ready
echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}Backend is ready!${NC}"
        break
    fi
    sleep 1
done
echo ""

# Start Frontend
echo -e "${YELLOW}Starting Frontend (SvelteKit) on port $FRONTEND_PORT...${NC}"
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing npm dependencies...${NC}"
    npm install
fi

npm run dev -- --port $FRONTEND_PORT --host &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"
echo ""

# Print status
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Development servers are running:${NC}"
echo -e "  Backend:  ${BLUE}http://localhost:$BACKEND_PORT${NC}"
echo -e "  API Docs: ${BLUE}http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "  Frontend: ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Wait for processes
wait
