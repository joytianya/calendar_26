from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.database.database import engine
from app.models import models
from app.routers import calendar, cycles
from app.config.logging_config import setup_logging
from app.database.migrations import run_migrations

# 设置日志记录器
logger = setup_logging()

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

# 运行数据库迁移
run_migrations()

# 创建FastAPI应用
app = FastAPI(
    title="26天周期日历应用",
    description="一款智能日历系统，支持26天周期提醒及历史记录功能",
    version="1.0.0",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=False,  # 不允许凭证
    allow_methods=["*"],
    allow_headers=["*"],
)

# 记录应用启动日志
logging.info("应用程序启动中...")

# 包含路由
app.include_router(calendar.router, prefix="/api/calendar", tags=["日历"])
app.include_router(cycles.router, prefix="/api/cycles", tags=["周期记录"])

@app.get("/")
async def root():
    logging.info("访问根路径")
    return {"message": "26天周期日历应用API服务"} 

@app.get("/api/health-check")
async def health_check():
    """
    健康检查端点，用于前端检测后端服务状态
    """
    logging.info("健康检查请求")
    return {"status": "ok", "message": "服务运行正常"} 