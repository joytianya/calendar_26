#!/usr/bin/env python3
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'calendar_26'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'calendar_26', 'app'))

# 切换到app目录
os.chdir(os.path.join(os.path.dirname(__file__), 'calendar_26', 'app'))

from database.database import get_db
from models import models
from services.calendar_service import calculate_valid_days_and_hours

def test_calculation():
    """直接测试计算函数"""
    # 获取数据库会话
    db = next(get_db())
    
    # 获取周期5
    cycle5 = db.query(models.CycleRecords).filter(models.CycleRecords.cycle_number == 5).first()
    
    if not cycle5:
        print("未找到周期5")
        return
    
    print("周期5信息:")
    print(f"开始时间: {cycle5.start_date}")
    print(f"结束时间: {cycle5.end_date}")
    print()
    
    # 获取跳过时间段
    skip_periods = db.query(models.SkipPeriod).filter(models.SkipPeriod.cycle_id == cycle5.id).all()
    print(f"跳过时间段数量: {len(skip_periods)}")
    
    # 直接调用计算函数
    print("直接调用calculate_valid_days_and_hours函数...")
    try:
        valid_days, valid_hours = calculate_valid_days_and_hours(cycle5, skip_periods)
        print(f"计算结果 - 有效天数: {valid_days}, 有效小时数: {valid_hours:.2f}")
        
        # 手动计算预期值
        end_time = cycle5.end_date if cycle5.end_date else datetime.now()
        total_hours = (end_time - cycle5.start_date).total_seconds() / 3600
        print(f"手动计算 - 总小时数: {total_hours:.2f}")
        
        if valid_hours == 0 and total_hours > 0:
            print("❌ 函数返回0但应该有有效时间")
        else:
            print("✅ 函数计算正常")
            
    except Exception as e:
        print(f"计算函数出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_calculation() 