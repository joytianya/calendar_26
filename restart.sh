#!/bin/bash

# 停止相关进程
echo "停止现有服务..."

# 查找并终止后端Python进程
python_pid=$(ps aux | grep 'python run.py' | grep -v grep | awk '{print $2}')
if [ -n "$python_pid" ]; then
  echo "终止后端进程 PID: $python_pid"
  kill -9 $python_pid
else
  echo "未找到后端进程"
fi

# 查找并终止前端服务进程 
serve_pid=$(ps aux | grep 'npx serve' | grep -v grep | awk '{print $2}')
if [ -n "$serve_pid" ]; then
  echo "终止前端进程 PID: $serve_pid"
  kill -9 $serve_pid
else
  echo "未找到前端进程"
fi

# 查找并终止占用8000端口的进程
port_8000_pid=$(lsof -i:8000 -t)
if [ -n "$port_8000_pid" ]; then
  echo "终止占用8000端口的进程 PID: $port_8000_pid"
  kill -9 $port_8000_pid
else
  echo "未找到占用8000端口的进程"
fi

# 查找并终止占用3000端口的进程
port_3000_pid=$(lsof -i:3000 -t)
if [ -n "$port_3000_pid" ]; then
  echo "终止占用3000端口的进程 PID: $port_3000_pid"
  kill -9 $port_3000_pid
else
  echo "未找到占用3000端口的进程"
fi

# 短暂等待确保进程已停止
sleep 2

# 启动后端服务
echo "启动后端服务..."
cd "$(dirname "$0")"
python run.py &
echo "后端服务已启动"

# 等待后端服务启动
sleep 3

# 启动前端服务
echo "启动前端服务..."
cd "$(dirname "$0")/app/frontend"
npx serve -s build &
echo "前端服务已启动"

echo "全部服务已重启完成"
echo "前端访问地址: http://localhost:3000"
echo "后端API地址: http://localhost:8000" 