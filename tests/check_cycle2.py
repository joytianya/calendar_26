#!/usr/bin/env python3
"""
检查周期2的有效天数和小时数计算是否合理
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
calendar_dir = os.path.join(current_dir, 'calendar_26')
app_dir = os.path.join(calendar_dir, 'app')

sys.path.append(current_dir)
sys.path.append(calendar_dir)
sys.path.append(app_dir)

# 切换到app目录
os.chdir(app_dir)

from database.database import get_db
from models import models

def check_cycle_2():
    """检查周期2的计算逻辑"""
    # 获取数据库会话
    db = next(get_db())
    
    # 查询周期2的详细信息
    cycle_2 = db.query(models.CycleRecords).filter(models.CycleRecords.cycle_number == 2).first()
    
    if not cycle_2:
        print('未找到周期2')
        return
    
    print(f'周期2详细信息:')
    print(f'ID: {cycle_2.id}')
    print(f'周期号: {cycle_2.cycle_number}')
    print(f'开始时间: {cycle_2.start_date}')
    print(f'结束时间: {cycle_2.end_date}')
    print(f'有效天数: {cycle_2.valid_days_count}')
    print(f'有效小时数: {cycle_2.valid_hours_count:.2f}')
    print(f'是否完成: {cycle_2.is_completed}')
    print(f'备注: {cycle_2.remark}')
    print()
    
    # 计算实际时间差
    if cycle_2.start_date and cycle_2.end_date:
        time_diff = cycle_2.end_date - cycle_2.start_date
        total_hours = time_diff.total_seconds() / 3600
        total_days = total_hours / 24
        print(f'实际总时间差: {total_days:.2f} 天 ({total_hours:.2f} 小时)')
    else:
        print('缺少开始或结束时间，无法计算时间差')
        return
    
    # 查询该周期的跳过时间段
    skip_periods = db.query(models.SkipPeriod).filter(models.SkipPeriod.cycle_id == cycle_2.id).all()
    print(f'跳过时间段数量: {len(skip_periods)}')
    print()
    
    total_skipped_hours = 0
    for i, period in enumerate(skip_periods, 1):
        print(f'跳过时间段 {i}:')
        print(f'  日期: {period.date}')
        print(f'  时间: {period.start_time} - {period.end_time}')
        
        # 计算跳过的小时数
        try:
            start_hour, start_minute = map(int, period.start_time.split(':'))
            end_hour, end_minute = map(int, period.end_time.split(':'))
            
            if end_hour > start_hour or (end_hour == start_hour and end_minute >= start_minute):
                # 同一天内
                hours = (end_hour - start_hour) + (end_minute - start_minute) / 60
            else:
                # 跨天
                hours = (24 - start_hour) + end_hour + (end_minute - start_minute) / 60
            
            total_skipped_hours += hours
            print(f'  跳过小时数: {hours:.2f}')
        except Exception as e:
            print(f'  计算跳过小时数时出错: {e}')
        print()
    
    print(f'总跳过小时数: {total_skipped_hours:.2f}')
    
    # 计算预期有效小时数
    expected_valid_hours = total_hours - total_skipped_hours
    print(f'预期有效小时数: {expected_valid_hours:.2f}')
    print(f'数据库中有效小时数: {cycle_2.valid_hours_count:.2f}')
    
    # 计算差异
    difference = abs(expected_valid_hours - cycle_2.valid_hours_count)
    print(f'差异: {difference:.2f} 小时')
    
    # 分析合理性
    print()
    print('=== 合理性分析 ===')
    
    # 检查有效天数是否合理
    expected_valid_days = int(expected_valid_hours / 24)
    print(f'根据有效小时数计算的有效天数: {expected_valid_days}')
    print(f'数据库中的有效天数: {cycle_2.valid_days_count}')
    
    if cycle_2.valid_days_count == 26:
        print('⚠️ 有效天数为26天，这意味着没有任何跳过时间')
        if total_skipped_hours > 0:
            print('❌ 但是存在跳过时间段，这是不合理的')
        else:
            print('✅ 没有跳过时间段，26天是合理的')
    
    # 检查790.59小时是否合理
    if cycle_2.valid_hours_count > 700:
        days_from_hours = cycle_2.valid_hours_count / 24
        print(f'{cycle_2.valid_hours_count:.2f}小时相当于 {days_from_hours:.2f} 天')
        if days_from_hours > 26:
            print('❌ 有效小时数超过26天，这是不合理的')
        elif abs(days_from_hours - 26) < 1:
            print('⚠️ 有效小时数接近26天，可能计算有误')
    
    # 检查是否有计算错误
    if difference > 1:  # 差异超过1小时
        print(f'❌ 计算差异较大 ({difference:.2f}小时)，可能存在计算错误')
    else:
        print(f'✅ 计算差异较小 ({difference:.2f}小时)，计算基本正确')

if __name__ == "__main__":
    check_cycle_2() 