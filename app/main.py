from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime
import sys

from app.routers import calendar, cycles
from app.database import database
from app.models import models
from app.services import calendar_service
from app.database.migrations import run_migrations

# 配置日志
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# 创建日志记录器
logger = logging.getLogger("root")
logger.setLevel(logging.INFO)

# 创建文件处理器，使用当前日期命名日志文件
log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y-%m-%d')}.log")
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# 创建格式化器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加处理器到记录器
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("日志记录器配置完成。日志保存在 %s 目录中，日志级别: %s", log_dir, "INFO")

# 创建数据库表
models.Base.metadata.create_all(bind=database.engine)

# 运行数据库迁移
run_migrations()

app = FastAPI(title="26天周期日历API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源的请求
    allow_credentials=False,  # 禁用凭据，避免与通配符一起使用时的安全问题
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有头部
)

# 包含路由
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(cycles.router, prefix="/api/cycles", tags=["cycles"])

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"发生全局异常：{exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误：{str(exc)}"}
    )

# 健康检查端点
@app.get("/api/health-check")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# 数据持久化配置，确保在应用启动时加载
@app.on_event("startup")
async def startup_db_client():
    logger.info("应用程序启动中...")
    # 确保所有数据库表已经创建
    database.Base.metadata.create_all(bind=database.engine)
    
    # 初始化周期数据
    db = database.SessionLocal()
    try:
        calendar_service.check_and_create_cycle(db)
    except Exception as e:
        logger.error(f"初始化周期数据时出错: {e}", exc_info=True)
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("应用程序关闭中...")
    # 这里可以添加关闭前的数据同步操作
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 