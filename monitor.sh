#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 获取脚本所在目录作为项目根目录
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

# 日志文件
LOG_FILE="${ROOT_DIR}/logs/monitor.log"
mkdir -p "${ROOT_DIR}/logs"

# 服务状态文件，记录上次检查的结果
STATUS_FILE="${ROOT_DIR}/logs/service_status.json"

# 定义日志函数
log_info() {
  echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_warn() {
  echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# 配置
BACKEND_PORT=8000
FRONTEND_PORT=3000
# 使用硬编码的公网IP地址，而不是自动检测
SERVER_IP="101.126.143.26"
log_info "使用服务器IP: ${SERVER_IP}"
HEALTH_CHECK_URL="http://localhost:${BACKEND_PORT}/api/health-check"

# 检查是否应该重启服务
# 为了避免过于频繁地重启服务，我们只在服务连续失败一定次数后才重启
should_restart_service() {
  local service_name="$1"
  local timestamp=$(date +%s)
  local restart_threshold=3  # 连续失败3次才重启
  
  # 如果状态文件不存在，创建一个
  if [ ! -f "$STATUS_FILE" ]; then
    echo "{\"backend\": {\"failures\": 0, \"last_restart\": 0}, \"frontend\": {\"failures\": 0, \"last_restart\": 0}}" > "$STATUS_FILE"
  fi
  
  # 读取当前状态
  local failures=$(jq -r ".${service_name}.failures" "$STATUS_FILE")
  local last_restart=$(jq -r ".${service_name}.last_restart" "$STATUS_FILE")
  
  # 增加失败次数
  failures=$((failures + 1))
  
  # 更新状态文件
  local json_tmp=$(mktemp)
  jq ".${service_name}.failures = ${failures}" "$STATUS_FILE" > "$json_tmp" && mv "$json_tmp" "$STATUS_FILE"
  
  # 如果超过阈值，且距离上次重启至少5分钟，则重启
  if [ $failures -ge $restart_threshold ] && [ $((timestamp - last_restart)) -gt 300 ]; then
    log_info "${service_name}服务连续失败${failures}次，将尝试重启"
    
    # 重置失败计数并更新上次重启时间
    local json_tmp=$(mktemp)
    jq ".${service_name}.failures = 0 | .${service_name}.last_restart = ${timestamp}" "$STATUS_FILE" > "$json_tmp" && mv "$json_tmp" "$STATUS_FILE"
    
    return 0  # 应该重启
  else
    if [ $failures -ge $restart_threshold ]; then
      log_info "${service_name}服务失败，但距离上次重启不足5分钟，暂不重启"
    else
      log_info "${service_name}服务失败${failures}次，未达到重启阈值(${restart_threshold}次)"
    fi
    return 1  # 不应该重启
  fi
}

# 重置服务的失败计数
reset_service_failures() {
  local service_name="$1"
  
  # 如果状态文件不存在，创建一个
  if [ ! -f "$STATUS_FILE" ]; then
    echo "{\"backend\": {\"failures\": 0, \"last_restart\": 0}, \"frontend\": {\"failures\": 0, \"last_restart\": 0}}" > "$STATUS_FILE"
    return
  fi
  
  # 重置失败计数
  local json_tmp=$(mktemp)
  jq ".${service_name}.failures = 0" "$STATUS_FILE" > "$json_tmp" && mv "$json_tmp" "$STATUS_FILE"
  
  log_info "${service_name}服务正常，重置失败计数"
}

# 检查后端服务是否运行
check_backend() {
  log_info "检查后端服务状态..."
  if curl -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
    log_info "后端服务运行正常"
    reset_service_failures "backend"
    return 0
  else
    log_warn "后端服务不可用"
    return 1
  fi
}

# 检查前端服务是否运行
check_frontend() {
  log_info "检查前端服务状态..."
  
  # 使用端口检测前端服务是否运行
  if lsof -ti:$FRONTEND_PORT > /dev/null 2>&1; then
    # 端口已被占用，表示服务可能在运行
    # 进一步验证可访问性
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
      log_info "前端服务运行正常"
      reset_service_failures "frontend"
      return 0
    else
      log_warn "前端服务端口被占用但无法访问，可能需要重启"
      return 1
    fi
  else
    log_warn "前端服务端口未被占用，服务未运行"
    return 1
  fi
}

# 启动后端服务
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
  
  # 检查并终止可能占用端口的进程
  local port_pid=$(lsof -ti:$BACKEND_PORT 2>/dev/null)
  if [ -n "$port_pid" ]; then
    log_warn "端口 $BACKEND_PORT 被进程 $port_pid 占用，尝试终止..."
    kill -15 $port_pid 2>/dev/null
    sleep 2
    if lsof -ti:$BACKEND_PORT > /dev/null 2>&1; then
      log_warn "强制终止进程..."
      kill -9 $(lsof -ti:$BACKEND_PORT) 2>/dev/null
      sleep 1
    fi
  fi
  
  # 启动后端服务
  cd "${ROOT_DIR}"
  PYTHONUNBUFFERED=1 nohup uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > "${ROOT_DIR}/logs/backend.log" 2>&1 &
  
  # 保存进程ID
  echo $! > "${ROOT_DIR}/backend.pid"
  
  log_info "后端服务启动中，进程ID: $!"
  
  # 等待服务启动
  for i in {1..15}; do
    if curl -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
      log_info "后端服务已成功启动"
      return 0
    fi
    sleep 1
  done
  
  log_error "后端服务启动失败或超时"
  return 1
}

# 启动前端服务
start_frontend() {
  log_info "启动前端服务..."
  
  # 进入前端目录
  cd "${ROOT_DIR}/app/frontend"
  
  # 检查并终止可能占用端口的进程
  local port_pid=$(lsof -ti:$FRONTEND_PORT 2>/dev/null)
  if [ -n "$port_pid" ]; then
    log_warn "端口 $FRONTEND_PORT 被进程 $port_pid 占用，尝试终止..."
    kill -15 $port_pid 2>/dev/null
    sleep 2
    if lsof -ti:$FRONTEND_PORT > /dev/null 2>&1; then
      log_warn "强制终止进程..."
      kill -9 $(lsof -ti:$FRONTEND_PORT) 2>/dev/null
      sleep 1
    fi
  fi
  
  # 修改index.html中的硬编码API地址
  log_info "更新index.html中的API地址..."
  INDEX_HTML="${ROOT_DIR}/app/frontend/public/index.html"
  if [ -f "$INDEX_HTML" ]; then
    # 查找并替换window._env_对象
    sed -i 's|window\._env_ *= *{[^}]*}|window._env_ = {\n      REACT_APP_API_URL: "http://'"${SERVER_IP}"':'"${BACKEND_PORT}"'"\n    }|g' "$INDEX_HTML"
    log_info "index.html已更新"
  fi
  
  # 确保环境配置文件正确
  mkdir -p public
  cat > "public/env-config.js" << EOF
window._env_ = {
  REACT_APP_API_URL: "http://${SERVER_IP}:${BACKEND_PORT}"
};
EOF
  log_info "env-config.js已更新，使用API地址: http://${SERVER_IP}:${BACKEND_PORT}"
  
  # 启动前端服务
  BROWSER=none nohup npm start > "${ROOT_DIR}/logs/frontend.log" 2>&1 &
  
  # 保存进程ID
  echo $! > "${ROOT_DIR}/frontend.pid"
  
  log_info "前端服务启动中，进程ID: $!"
  
  # 等待服务启动
  for i in {1..20}; do
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
      log_info "前端服务已成功启动"
      return 0
    fi
    sleep 1
  done
  
  log_error "前端服务启动失败或超时"
  return 1
}

# 主要流程
log_info "开始监控服务..."

# 检查后端服务
if ! check_backend; then
  # 只有应该重启时才重启服务
  if should_restart_service "backend"; then
    log_info "尝试启动后端服务..."
    start_backend
    
    # 如果后端启动成功，也检查前端
    if [ $? -eq 0 ]; then
      if ! check_frontend; then
        if should_restart_service "frontend"; then
          log_info "尝试启动前端服务..."
          start_frontend
        fi
      fi
    fi
  fi
else
  # 后端正常，检查前端
  if ! check_frontend; then
    if should_restart_service "frontend"; then
      log_info "尝试启动前端服务..."
      start_frontend
    fi
  fi
fi

log_info "服务监控完成"
log_info "============================================"
log_info "前端访问地址: http://${SERVER_IP}:${FRONTEND_PORT}"
log_info "后端API地址: http://${SERVER_IP}:${BACKEND_PORT}"
log_info "============================================" 