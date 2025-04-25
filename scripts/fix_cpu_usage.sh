#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 获取脚本所在目录作为项目根目录
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

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

# 优雅地停止所有进程
stop_all_processes() {
  log_info "停止所有相关进程..."
  
  # 停止uvicorn进程
  if pgrep -f "uvicorn" > /dev/null; then
    log_info "正在停止后端服务..."
    pkill -f "uvicorn"
    sleep 2
    # 如果进程仍然存在，强制终止
    if pgrep -f "uvicorn" > /dev/null; then
      log_warn "后端服务没有响应，强制终止中..."
      pkill -9 -f "uvicorn"
    fi
  fi
  
  # 停止前端进程
  if pgrep -f "node.*react-scripts start" > /dev/null; then
    log_info "正在停止前端服务..."
    pkill -f "node.*react-scripts start"
    sleep 2
    # 如果进程仍然存在，强制终止
    if pgrep -f "node.*react-scripts start" > /dev/null; then
      log_warn "前端服务没有响应，强制终止中..."
      pkill -9 -f "node.*react-scripts start"
    fi
  fi
  
  log_info "所有服务已停止"
}

# 修改启动脚本，移除--reload选项
fix_startup_script() {
  log_info "修复启动脚本..."
  
  # 备份原始文件
  cp restart.sh restart.sh.original
  log_info "已备份原始启动脚本: restart.sh.original"
  
  # 修改启动脚本，移除--reload选项
  sed -i 's/--reload//' restart.sh
  log_info "已从启动脚本中移除--reload选项"
  
  # 检查修改
  if grep -q "\-\-reload" restart.sh; then
    log_warn "警告: --reload选项仍然存在于脚本中，可能在其他位置"
  else
    log_info "成功移除--reload选项"
  fi
}

# 优化计算函数，添加缓存机制
optimize_calculation() {
  log_info "正在优化计算有效天数函数..."
  
  # 查找计算函数的位置
  CALENDAR_SERVICE_FILE="app/services/calendar_service.py"
  
  if [ -f "$CALENDAR_SERVICE_FILE" ]; then
    # 备份原始文件
    cp "$CALENDAR_SERVICE_FILE" "${CALENDAR_SERVICE_FILE}.original"
    log_info "已备份原始计算服务文件: ${CALENDAR_SERVICE_FILE}.original"
    
    # 尝试添加缓存机制
    if grep -q "def calculate_valid_days" "$CALENDAR_SERVICE_FILE"; then
      # 文件内容添加缓存装饰器和导入
      if ! grep -q "from functools import lru_cache" "$CALENDAR_SERVICE_FILE"; then
        sed -i '1s/^/from functools import lru_cache\n/' "$CALENDAR_SERVICE_FILE"
        log_info "已添加lru_cache导入"
      fi
      
      # 添加缓存装饰器
      sed -i 's/def calculate_valid_days/@lru_cache(maxsize=128)\ndef calculate_valid_days/' "$CALENDAR_SERVICE_FILE"
      log_info "已为calculate_valid_days函数添加缓存装饰器"
    else
      log_warn "无法找到calculate_valid_days函数，请手动优化"
    fi
  else
    log_warn "无法找到日历服务文件，请手动优化"
  fi
}

# 修改监控脚本，减少监控频率
fix_monitor_script() {
  log_info "正在优化监控脚本..."
  
  if [ -f "monitor.sh" ]; then
    # 备份原始文件
    cp monitor.sh monitor.sh.original
    log_info "已备份原始监控脚本: monitor.sh.original"
    
    # 如果是cron任务，将频率从每分钟改为每5分钟
    if grep -q "sleep 60" monitor.sh; then
      sed -i 's/sleep 60/sleep 300/' monitor.sh
      log_info "已将监控时间间隔从1分钟改为5分钟"
    fi
  else
    log_warn "未找到监控脚本"
  fi
}

# 应用所有修复
apply_all_fixes() {
  # 先停止所有进程
  stop_all_processes
  
  # 修复启动脚本
  fix_startup_script
  
  # 优化计算函数
  optimize_calculation
  
  # 修复监控脚本
  fix_monitor_script
  
  log_info "所有修复已应用，请使用以下命令重启服务:"
  echo "./restart.sh"
}

# 运行修复
apply_all_fixes

log_info "==============================================="
log_info "CPU使用率优化完成，请使用以下命令重启服务:"
log_info "./restart.sh"
log_info "==============================================="
log_info "如需恢复原始文件，请使用以下命令:"
log_info "cp restart.sh.original restart.sh"
log_info "cp app/services/calendar_service.py.original app/services/calendar_service.py"
log_info "cp monitor.sh.original monitor.sh (如果存在)" 