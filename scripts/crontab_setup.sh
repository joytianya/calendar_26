#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 获取脚本所在目录
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}[INFO]${NC} 设置定时监控任务..."

# 确保monitor.sh有执行权限
chmod +x "${ROOT_DIR}/monitor.sh"

# 创建临时crontab文件
TEMP_CRON=$(mktemp)

# 导出当前crontab
crontab -l > "$TEMP_CRON" 2>/dev/null || echo "" > "$TEMP_CRON"

# 检查是否已经有相同的任务
if grep -q "monitor.sh" "$TEMP_CRON"; then
  echo -e "${YELLOW}[WARNING]${NC} 监控任务已存在，将被更新"
  # 移除旧的监控任务
  sed -i '/monitor.sh/d' "$TEMP_CRON"
fi

# 添加新的cron任务 - 每分钟检查一次服务状态
echo "*/1 * * * * cd ${ROOT_DIR} && ${ROOT_DIR}/monitor.sh >> ${ROOT_DIR}/logs/cron.log 2>&1" >> "$TEMP_CRON"

# 安装新的crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo -e "${GREEN}[INFO]${NC} cron任务设置完成！服务将每分钟被检查一次"
echo -e "${GREEN}[INFO]${NC} 您可以通过以下命令查看当前的cron任务："
echo -e "  crontab -l"
echo -e "${GREEN}[INFO]${NC} 您可以通过以下命令查看监控日志："
echo -e "  tail -f ${ROOT_DIR}/logs/monitor.log"
echo -e "  tail -f ${ROOT_DIR}/logs/cron.log" 