# 26天周期日历系统

这是一款智能日历系统，支持26天周期提醒及历史记录功能。

## 功能特色

- 26天周期计算和跟踪
- 跳过时间段设置，灵活调整有效天数计算
- 周期历史记录，支持查看详细的跳过时间记录
- 有效天数和有效小时数统计

## 技术栈

- 后端: Python FastAPI
- 前端: React + Material-UI
- 数据库: SQLite

## 安装说明

### 后端设置

```bash
# 克隆仓库
git clone https://github.com/joytianya/calendar_26.git
cd calendar_26

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动后端服务
./manage.sh start
```

### 使用统一管理脚本

本项目提供了一个统一的管理脚本 `manage.sh`，用于简化各种操作：

```bash
# 显示帮助信息
./manage.sh help

# 启动所有服务（前端和后端）
./manage.sh start

# 停止所有服务
./manage.sh stop

# 重启所有服务
./manage.sh restart

# 检查服务状态
./manage.sh status

# 监控服务并自动重启
./manage.sh monitor

# 安装定时监控任务
./manage.sh cron

# 构建应用（用于部署）
./manage.sh build

# 强制终止所有相关进程
./manage.sh kill

# 清理日志文件
./manage.sh clean

# 修复高CPU使用率问题
./manage.sh fix-cpu
```

### 前端设置

```bash
# 进入前端目录
cd app/frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```

## 使用指南

1. 访问 `http://localhost:3000` 打开应用
2. 在"设置"页面配置周期起始日期和时间
3. 在日历视图中，点击日期可设置跳过时间段
4. 在"历史记录"页面可查看所有周期记录和详细的跳过时间

## 环境变量配置

可通过以下环境变量自定义应用行为:

- `LOG_DIR`: 日志文件存储目录
- `LOG_LEVEL`: 日志级别 (DEBUG, INFO, WARNING, ERROR)

## 协议

MIT License 