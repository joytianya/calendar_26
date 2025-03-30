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
