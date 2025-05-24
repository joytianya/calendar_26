#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 获取脚本所在目录作为项目根目录
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

# 创建日志目录
mkdir -p "${ROOT_DIR}/logs"
BACKEND_LOG="${ROOT_DIR}/logs/backend.log"
FRONTEND_LOG="${ROOT_DIR}/logs/frontend.log"
MONITOR_LOG="${ROOT_DIR}/logs/monitor.log"

# 定义日志函数
log_info() {
  echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$BACKEND_LOG"
}

log_warn() {
  echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$BACKEND_LOG"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$BACKEND_LOG"
}

log_section() {
  echo -e "${BLUE}[${1}]${NC}"
}

# 配置
BACKEND_PORT=8000
FRONTEND_PORT=3000
BACKEND_PROCESS="uvicorn app.main:app"
FRONTEND_PROCESS="node.*react-scripts start"
# 自动检测公网IP地址
SERVER_IP=$(timeout 3 curl -s ifconfig.me 2>/dev/null || timeout 3 curl -s icanhazip.com 2>/dev/null || timeout 3 curl -s ipinfo.io/ip 2>/dev/null || hostname -I | awk '{print $1}' || echo "localhost")
log_info "检测到的服务器IP地址: ${SERVER_IP}"

# 服务状态文件，记录上次检查的结果
STATUS_FILE="${ROOT_DIR}/logs/service_status.json"
HEALTH_CHECK_URL="http://localhost:${BACKEND_PORT}/api/health-check"

# 显示帮助信息
show_help() {
  echo "日历应用管理脚本"
  echo ""
  echo "用法: ./manage.sh [命令]"
  echo ""
  echo "命令:"
  echo "  start       启动前端和后端服务"
  echo "  stop        停止所有服务"
  echo "  restart     重启所有服务"
  echo "  status      检查服务状态"
  echo "  monitor     监控服务状态并在需要时自动重启"
  echo "  cron        安装定时监控任务"
  echo "  build       构建应用（用于部署）"
  echo "  kill        强制终止所有相关进程"
  echo "  clean       清理日志文件"
  echo "  fix-cpu     修复高CPU使用率问题"
  echo "  help        显示此帮助信息"
  echo ""
}

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
  
  # 启动后端服务（移除 --reload 选项以减少CPU使用）
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
  
  # 返回根目录
  cd "${ROOT_DIR}"
}

# 启动所有服务
start_services() {
  log_section "启动服务"
  start_backend
  start_frontend
  
  log_info "所有服务已启动完成!"
  log_info "=========================================="
  log_info "前端访问地址: http://${SERVER_IP}:${FRONTEND_PORT}"
  log_info "后端API地址: http://${SERVER_IP}:${BACKEND_PORT}"
  log_info "=========================================="
  log_info "前端日志: tail -f $FRONTEND_LOG"
  log_info "后端日志: tail -f $BACKEND_LOG"
}

# 停止所有服务
stop_services() {
  log_section "停止服务"
  log_info "检查并停止现有服务..."
  stop_process "$BACKEND_PROCESS" $BACKEND_PORT "后端"
  stop_process "$FRONTEND_PROCESS" $FRONTEND_PORT "前端"
  log_info "所有服务已停止"
}

# 服务状态检查函数
check_services_status() {
  local backend_status="停止"
  local frontend_status="停止"
  
  # 检查后端状态
  if curl -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
    backend_status="运行中"
  fi
  
  # 检查前端状态
  if lsof -ti:$FRONTEND_PORT > /dev/null 2>&1; then
    frontend_status="运行中"
  fi
  
  log_section "服务状态"
  echo "后端服务: $backend_status"
  echo "前端服务: $frontend_status"
  echo "前端访问地址: http://${SERVER_IP}:${FRONTEND_PORT}"
  echo "后端API地址: http://${SERVER_IP}:${BACKEND_PORT}"
}

# 检查是否应该重启服务
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

# 监控服务状态并在需要时重启
monitor_services() {
  log_section "监控服务"
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
}

# 清理日志文件
clean_logs() {
  log_section "清理日志"
  read -p "确定要清理所有日志文件吗? [y/N] " confirm
  if [[ $confirm =~ ^[Yy]$ ]]; then
    rm -f "${ROOT_DIR}/logs/*.log"
    log_info "日志文件已清理"
  else
    log_info "操作已取消"
  fi
}

# 运行脚本中的命令
run_script_command() {
  local script_path=$1
  shift
  
  if [ -f "$script_path" ]; then
    log_info "执行脚本: $script_path"
    bash "$script_path" "$@"
  else
    log_error "找不到脚本: $script_path"
    return 1
  fi
}

# 设置定时监控
setup_cron() {
  log_section "设置定时监控"
  run_script_command "${ROOT_DIR}/scripts/crontab_setup.sh"
}

# 构建应用
build_app() {
  log_section "构建应用"
  run_script_command "${ROOT_DIR}/scripts/build.sh"
}

# 强制终止所有相关进程
kill_all() {
  log_section "强制终止相关进程"
  run_script_command "${ROOT_DIR}/scripts/kill.sh"
}

# 修复CPU使用率问题
fix_cpu_usage() {
  log_section "修复CPU使用率问题"
  run_script_command "${ROOT_DIR}/scripts/fix_cpu_usage.sh"
}

# 主函数
main() {
  local command=$1
  
  case $command in
    start)
      start_services
      ;;
    stop)
      stop_services
      ;;
    restart)
      stop_services
      start_services
      ;;
    status)
      check_services_status
      ;;
    monitor)
      monitor_services
      ;;
    cron)
      setup_cron
      ;;
    build)
      build_app
      ;;
    kill)
      kill_all
      ;;
    clean)
      clean_logs
      ;;
    fix-cpu)
      fix_cpu_usage
      ;;
    help|*)
      show_help
      ;;
  esac
}

# 如果脚本以root身份运行，发出警告
if [ "$(id -u)" = "0" ]; then
  log_warn "脚本正在以root身份运行。建议使用普通用户运行此脚本。"
fi

# 运行主函数
main "$@" 