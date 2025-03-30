from sqlalchemy import create_engine, Column, Float, text
import logging
from app.database.database import engine

# 获取日志记录器
logger = logging.getLogger("api.migrations")

def run_migrations():
    """运行数据库迁移脚本"""
    try:
        logger.info("开始数据库迁移...")
        
        # 添加有效小时数字段
        add_valid_hours_count()
        
        logger.info("数据库迁移完成")
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}", exc_info=True)
        raise

def add_valid_hours_count():
    """添加有效小时数字段到cycle_records表"""
    try:
        # 检查字段是否已存在
        connection = engine.connect()
        result = connection.execute(text("PRAGMA table_info(cycle_records)"))
        columns = [row[1] for row in result.fetchall()]
        
        if "valid_hours_count" not in columns:
            logger.info("添加valid_hours_count字段到cycle_records表")
            connection.execute(text("ALTER TABLE cycle_records ADD COLUMN valid_hours_count FLOAT DEFAULT 0.0"))
            connection.commit()
            logger.info("成功添加valid_hours_count字段")
        else:
            logger.info("valid_hours_count字段已存在，跳过迁移")
        
        connection.close()
    except Exception as e:
        logger.error(f"添加valid_hours_count字段失败: {e}", exc_info=True)
        raise 