#!/usr/bin/env python3
"""
清理无效的跳过时间段

此脚本会检查并删除以下无效的跳过时间段：
1. 跳过日期在周期开始时间之前的
2. 跳过日期在已完成周期结束时间之后的
"""
import sys
import os
sys.path.append('/root/calendar_26')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import models

def cleanup_invalid_skip_periods():
    """清理无效的跳过时间段"""
    DATABASE_URL = 'sqlite:///./calendar_app.db'
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # 获取所有跳过时间段
        all_skip_periods = db.query(models.SkipPeriod).all()
        invalid_periods = []
        
        for period in all_skip_periods:
            cycle = db.query(models.CycleRecords).filter(models.CycleRecords.id == period.cycle_id).first()
            if cycle:
                period_date = period.date.date()
                cycle_start_date = cycle.start_date.date()
                
                # 检查是否在周期开始之前
                if period_date < cycle_start_date:
                    invalid_periods.append({
                        'period_id': period.id,
                        'period_date': period_date,
                        'cycle_id': cycle.id,
                        'cycle_number': cycle.cycle_number,
                        'cycle_start': cycle_start_date,
                        'reason': '跳过日期在周期开始之前'
                    })
                
                # 检查是否在已完成周期的结束之后
                elif cycle.is_completed and cycle.end_date:
                    cycle_end_date = cycle.end_date.date()
                    if period_date > cycle_end_date:
                        invalid_periods.append({
                            'period_id': period.id,
                            'period_date': period_date,
                            'cycle_id': cycle.id,
                            'cycle_number': cycle.cycle_number,
                            'cycle_end': cycle_end_date,
                            'reason': '跳过日期在周期结束之后'
                        })
        
        print(f'=== 跳过时间段验证结果 ===')
        print(f'总跳过时间段数量: {len(all_skip_periods)}')
        print(f'发现无效跳过时间段: {len(invalid_periods)}')
        
        if invalid_periods:
            print(f'\n无效跳过时间段详情:')
            for invalid in invalid_periods:
                print(f'  - ID: {invalid["period_id"]}, 日期: {invalid["period_date"]}, 周期: #{invalid["cycle_number"]}, 原因: {invalid["reason"]}')
            
            # 删除无效的跳过时间段
            confirm = input(f'\n是否删除这 {len(invalid_periods)} 个无效的跳过时间段？(y/N): ')
            if confirm.lower() == 'y':
                for invalid in invalid_periods:
                    period = db.query(models.SkipPeriod).filter(models.SkipPeriod.id == invalid['period_id']).first()
                    if period:
                        db.delete(period)
                
                db.commit()
                print(f'✅ 已删除 {len(invalid_periods)} 个无效的跳过时间段')
            else:
                print('取消删除操作')
        else:
            print('✅ 所有跳过时间段都是有效的')
            
    except Exception as e:
        print(f'❌ 清理失败: {e}')
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    cleanup_invalid_skip_periods()