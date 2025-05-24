import sys
sys.path.append('app')
from datetime import datetime
from app.database.database import get_db
from app.models import models
from app.services.calendar_service import calculate_valid_days_and_hours

# 获取数据库会话
db = next(get_db())

# 获取周期5
cycle5 = db.query(models.CycleRecords).filter(models.CycleRecords.cycle_number == 5).first()

if cycle5:
    print('周期5信息:')
    print(f'开始时间: {cycle5.start_date}')
    print(f'结束时间: {cycle5.end_date}')
    
    # 获取跳过时间段
    skip_periods = db.query(models.SkipPeriod).filter(models.SkipPeriod.cycle_id == cycle5.id).all()
    print(f'跳过时间段数量: {len(skip_periods)}')
    
    # 直接调用计算函数
    print('直接调用calculate_valid_days_and_hours函数...')
    valid_days, valid_hours = calculate_valid_days_and_hours(cycle5, skip_periods)
    print(f'计算结果 - 有效天数: {valid_days}, 有效小时数: {valid_hours:.2f}')
    
    # 手动计算预期值
    end_time = cycle5.end_date if cycle5.end_date else datetime.now()
    total_hours = (end_time - cycle5.start_date).total_seconds() / 3600
    print(f'手动计算 - 总小时数: {total_hours:.2f}')
    
    if valid_hours == 0 and total_hours > 0:
        print('❌ 函数返回0但应该有有效时间')
        print('检查函数内部逻辑...')
        
        # 检查是否是因为时间太短被过滤
        if total_hours < 1:
            print(f'时间差很小: {total_hours:.4f} 小时 = {total_hours*60:.2f} 分钟')
else:
    print('未找到周期5') 