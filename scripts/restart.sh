#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 获取脚本所在目录作为项目根目录
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

# 创建日志目录
mkdir -p "${ROOT_DIR}/logs"
BACKEND_LOG="${ROOT_DIR}/logs/backend.log"
FRONTEND_LOG="${ROOT_DIR}/logs/frontend.log"

# 定义日志函数
log_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# 配置
BACKEND_PORT=8000
FRONTEND_PORT=3000
BACKEND_PROCESS="uvicorn app.main:app"
FRONTEND_PROCESS="node.*react-scripts start"
# 使用硬编码的公网IP地址，而不是自动检测
SERVER_IP="101.126.143.26"
log_info "使用服务器IP: ${SERVER_IP}"

# 优雅地停止进程
stop_process() {
  local process_pattern=$1
  local port=$2
  local name=$3
  
  # 通过进程名查找
  pid=$(ps aux | grep -E "$process_pattern" | grep -v "grep" | awk '{print $2}' | head -1)
  
  # 如果通过进程名没找到，尝试通过端口查找
  if [ -z "$pid" ] && [ -n "$port" ]; then
    pid=$(lsof -ti:$port 2>/dev/null)
  fi
  
  if [ -n "$pid" ]; then
    log_info "正在停止${name}服务 (PID: $pid)..."
    kill -15 $pid 2>/dev/null
    
    # 等待进程自然结束
    for i in {1..5}; do
      if ! ps -p $pid > /dev/null 2>&1; then
        break
      fi
      sleep 1
    done
    
    # 如果进程仍然存在，强制终止
    if ps -p $pid > /dev/null 2>&1; then
      log_warn "${name}服务没有响应，强制终止中..."
      kill -9 $pid 2>/dev/null
    fi
    
    log_info "${name}服务已停止"
  else
    log_info "未检测到运行中的${name}服务"
  fi
}

# 启动后端
start_backend() {
  log_info "启动后端服务..."
  
  # 检查并激活虚拟环境
  if [ ! -d "venv" ]; then
    log_info "创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    log_info "安装后端依赖..."
    pip install -r requirements.txt
  else
    log_info "激活虚拟环境..."
    source venv/bin/activate
  fi
  
  # 启动后端服务
  PYTHONUNBUFFERED=1 nohup uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > "$BACKEND_LOG" 2>&1 &
  
  # 保存进程ID
  echo $! > "${ROOT_DIR}/backend.pid"
  
  # 等待后端启动
  log_info "等待后端服务启动..."
  for i in {1..10}; do
    if curl -s "http://localhost:$BACKEND_PORT/api/health-check" > /dev/null 2>&1; then
      log_info "后端服务已成功启动"
      break
    fi
    if [ $i -eq 10 ]; then
      log_warn "后端服务可能未正常启动，请检查日志: $BACKEND_LOG"
    fi
    sleep 1
  done
}

# 启动前端
start_frontend() {
  log_info "启动前端服务..."
  
  # 进入前端目录
  cd "${ROOT_DIR}/app/frontend"
  
  # 更新环境配置
  log_info "更新前端环境配置..."
  
  # 修改index.html中的硬编码API地址
  log_info "更新index.html中的API地址..."
  INDEX_HTML="${ROOT_DIR}/app/frontend/public/index.html"
  if [ -f "$INDEX_HTML" ]; then
    # 查找并替换window._env_对象
    sed -i 's|window\._env_ *= *{[^}]*}|window._env_ = {\n      REACT_APP_API_URL: "http://'"${SERVER_IP}"':'"${BACKEND_PORT}"'"\n    }|g' "$INDEX_HTML"
    log_info "index.html已更新"
  fi
  
  # 创建前端环境配置文件
  mkdir -p public
  cat > "public/env-config.js" << EOF
window._env_ = {
  REACT_APP_API_URL: "http://${SERVER_IP}:${BACKEND_PORT}"
};
EOF
  log_info "env-config.js已更新，使用API地址: http://${SERVER_IP}:${BACKEND_PORT}"
  
  # 安装依赖（如果需要）
  if [ ! -d "node_modules" ]; then
    log_info "安装前端依赖..."
    npm install
  fi
  
  # 启动前端开发服务器（支持热重载）
  BROWSER=none nohup npm start > "$FRONTEND_LOG" 2>&1 &
  
  # 保存进程ID
  echo $! > "${ROOT_DIR}/frontend.pid"
  
  # 等待前端启动
  log_info "等待前端服务启动..."
  for i in {1..15}; do
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
      log_info "前端服务已成功启动"
      break
    fi
    if [ $i -eq 15 ]; then
      log_warn "前端服务可能未正常启动，请检查日志: $FRONTEND_LOG"
    fi
    sleep 1
  done
}

# 主要流程

# 1. 停止现有服务
log_info "检查并停止现有服务..."
stop_process "$BACKEND_PROCESS" $BACKEND_PORT "后端"
stop_process "$FRONTEND_PROCESS" $FRONTEND_PORT "前端"

# 2. 启动服务
start_backend
start_frontend

# 3. 显示访问信息
cd "${ROOT_DIR}"
log_info "服务已启动完成!"
log_info "=========================================="
log_info "前端访问地址: http://${SERVER_IP}:${FRONTEND_PORT}"
log_info "后端API地址: http://${SERVER_IP}:${BACKEND_PORT}"
log_info "=========================================="
log_info "前端日志: tail -f $FRONTEND_LOG"
log_info "后端日志: tail -f $BACKEND_LOG"
log_info "要停止服务，请再次运行 ./restart.sh" 
