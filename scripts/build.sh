#!/bin/bash
# 构建脚本 - 用于Render部署

# 确保脚本在出错时停止
set -e

# 创建日志目录
mkdir -p logs

# 创建并激活虚拟环境
echo "创建虚拟环境..."
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate

# 安装Python依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 如果前端目录不存在build文件夹，则构建前端
if [ ! -d "app/frontend/build" ]; then
  echo "构建前端应用..."
  cd app/frontend
  
  # 安装Node.js依赖
  npm install
  
  # 构建React应用 - 设置CI=false避免ESLint警告导致构建失败
  CI=false npm run build
  
  # 返回项目根目录
  cd ../..
fi

echo "构建完成!" 