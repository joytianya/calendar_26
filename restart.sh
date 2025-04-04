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

# 检查并终止占用8000端口的进程
port_8000_pid=$(lsof -ti:8000)
if [ -n "$port_8000_pid" ]; then
  echo "终止占用8000端口的进程 PID: $port_8000_pid"
  kill -9 $port_8000_pid
else
  echo "端口8000未被占用"
fi

# 检查并终止占用3000端口的进程
port_3000_pid=$(lsof -ti:3000)
if [ -n "$port_3000_pid" ]; then
  echo "终止占用3000端口的进程 PID: $port_3000_pid"
  kill -9 $port_3000_pid
else
  echo "端口3000未被占用"
fi

# 短暂等待确保进程已停止
sleep 2

# 检查并创建虚拟环境
cd "$(dirname "$0")"
if [ ! -d "venv" ]; then
  echo "创建虚拟环境..."
  python3 -m venv venv
  source venv/bin/activate
  echo "安装依赖包..."
  pip install -r requirements.txt
else
  echo "激活虚拟环境..."
  source venv/bin/activate
fi

# 设置根目录
ROOT_DIR="$(dirname "$0")"

# 启动后端服务
echo "启动后端服务..."
mkdir -p "${ROOT_DIR}/logs"
python run.py > "${ROOT_DIR}/logs/backend.log" 2>&1 &
echo "后端服务已启动"

# 等待后端服务启动
sleep 3

# 更新前端环境配置
echo "更新前端API地址配置..."
SERVER_IP=$(curl -s http://ifconfig.me || hostname -I | awk '{print $1}')
echo "检测到服务器IP: $SERVER_IP"
cat > "${ROOT_DIR}/app/frontend/build/env-config.js" << EOF
window._env_ = {
  REACT_APP_API_URL: "http://${SERVER_IP}:8000"
}; 
EOF

# 启动前端服务
echo "启动前端服务..."
cd "${ROOT_DIR}/app/frontend"
mkdir -p "${ROOT_DIR}/logs"
npx serve -s build -l 3000 --no-clipboard > "${ROOT_DIR}/logs/frontend.log" 2>&1 &
echo "前端服务已启动"

echo "全部服务已重启完成"
echo "前端访问地址: http://${SERVER_IP}:3000"
echo "后端API地址: http://${SERVER_IP}:8000" 
