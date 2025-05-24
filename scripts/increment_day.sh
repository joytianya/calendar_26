#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# 调用increment-valid-day接口
curl -X POST http://localhost:8000/calendar/increment-day

# 记录日志
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 已调用increment-valid-day接口" >> "${ROOT_DIR}/logs/increment_day.log"