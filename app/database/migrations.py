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
        columns_info = result.fetchall()
        
        # 输出完整的表结构信息
        logger.info("当前数据库表结构:")
        for col in columns_info:
            logger.info(f"列名: {col[1]}, 类型: {col[2]}, 是否可空: {col[3]}, 默认值: {col[4]}, 是否主键: {col[5]}")
            
        # 获取表中的数据
        data_result = connection.execute(text("SELECT * FROM cycle_records"))
        records = data_result.fetchall()
        logger.info("当前表数据:")
        for record in records:
            # 将 Row 对象转换为字典
            record_dict = {}
            for key in record._mapping.keys():
                record_dict[key] = record._mapping[key]
            logger.info(f"记录: {record_dict}")
            
        columns = [row[1] for row in columns_info]
        
        if "valid_hours_count" not in columns:
            logger.info("添加valid_hours_count字段到cycle_records表")
            connection.execute(text("ALTER TABLE cycle_records ADD COLUMN valid_hours_count FLOAT DEFAULT 0.0"))
            connection.commit()
            logger.info("成功添加valid_hours_count字段")
            
            # 读取更新后的表结构
            result = connection.execute(text("PRAGMA table_info(cycle_records)"))
            updated_columns = [row[1] for row in result.fetchall()]
            logger.info(f"更新后的数据库表结构: {updated_columns}")
        else:
            logger.info("valid_hours_count字段已存在，跳过迁移")
        
        connection.close()
    except Exception as e:
        logger.error(f"添加valid_hours_count字段失败: {e}", exc_info=True)
        raise