#!/usr/bin/env python3
"""
修复脚本：重新计算有效天数
用于修复有效小时数与有效天数不一致的问题
"""

import sqlite3
import logging
import sys
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('fix_days')

def main():
    # 连接数据库
    try:
        conn = sqlite3.connect('calendar_app.db')
        cursor = conn.cursor()
        logger.info("成功连接到数据库")
    except Exception as e:
        logger.error(f"连接数据库失败: {e}")
        sys.exit(1)

    try:
        # 获取当前周期记录
        cursor.execute("""
            SELECT id, cycle_number, start_date, valid_days_count, valid_hours_count 
            FROM cycle_records 
            WHERE is_completed = 0
            ORDER BY id DESC LIMIT 1
        """)
        cycle = cursor.fetchone()
        
        if not cycle:
            logger.error("没有找到进行中的周期记录")
            sys.exit(1)
            
        cycle_id, cycle_number, start_date, valid_days_count, valid_hours_count = cycle
        
        logger.info(f"当前周期 #{cycle_number} 数据:")
        logger.info(f"  - 开始时间: {start_date}")
        logger.info(f"  - 有效天数: {valid_days_count}")
        logger.info(f"  - 有效小时数: {valid_hours_count}")
        
        # 重新计算有效天数（从有效小时数）
        new_valid_days = int(valid_hours_count / 24)  # 向下取整
        logger.info(f"新计算的有效天数: {new_valid_days}")
        
        if new_valid_days == valid_days_count:
            logger.info("有效天数已是正确值，无需修复")
            return
            
        # 更新数据库
        logger.info(f"更新有效天数: {valid_days_count} -> {new_valid_days}")
        cursor.execute("""
            UPDATE cycle_records 
            SET valid_days_count = ?, updated_at = ? 
            WHERE id = ?
        """, (new_valid_days, datetime.now().isoformat(), cycle_id))
        
        conn.commit()
        logger.info("数据库更新成功")
        
        # 验证更新结果
        cursor.execute("""
            SELECT valid_days_count 
            FROM cycle_records 
            WHERE id = ?
        """, (cycle_id,))
        updated_days = cursor.fetchone()[0]
        logger.info(f"验证后的有效天数: {updated_days}")
        
        logger.info("修复完成!")
        
    except Exception as e:
        logger.error(f"修复过程中出错: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main() 