from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache

from app.models import models, schemas

# 获取日志记录器
logger = logging.getLogger("api.calendar_service")

def check_and_create_cycle(db: Session):
    """检查并创建新的周期记录（如果需要）"""
    # 检查是否有未完成的周期
    current_cycle = db.query(models.CycleRecords)\
        .filter(models.CycleRecords.is_completed == False)\
        .order_by(models.CycleRecords.id.desc())\
        .first()
    
    # 如果没有未完成的周期，创建一个新周期
    if not current_cycle:
        # 查找最后一个周期获取周期号
        last_cycle = db.query(models.CycleRecords)\
            .order_by(models.CycleRecords.cycle_number.desc())\
            .first()
        
        cycle_number = 1
        if last_cycle:
            cycle_number = last_cycle.cycle_number + 1
        
        # 获取用户设置的起始时间
        settings = db.query(models.CalendarSettings).first()
        start_date = datetime.now()
        
        # 如果有设置，使用设置的开始时间
        if settings:
            # 检查是否是首次创建的设置（通常设置时间与现在时间相差不大）
            time_diff = abs((settings.created_at - datetime.now()).total_seconds())
            if time_diff < 300:  # 如果设置是在最近5分钟内创建的
                # 对于刚刚创建的设置，直接使用设置中的完整时间
                logger.info(f"首次创建设置，直接使用设置的完整开始时间: {settings.start_date}")
                start_date = settings.start_date
            else:
                # 对于已有的设置，使用当前日期和设置中的时间部分
                now = datetime.now()
                start_date = datetime(
                    now.year,
                    now.month,
                    now.day,
                    settings.start_date.hour,
                    settings.start_date.minute,
                    0
                )
                logger.info(f"使用当前日期和设置的时间部分创建周期: {start_date}")
        else:
            logger.info(f"没有日历设置，使用当前时间创建周期: {start_date}")
        
        # 创建新周期
        new_cycle = models.CycleRecords(
            cycle_number=cycle_number,
            start_date=start_date,
            valid_days_count=0,
            is_completed=False
        )
        db.add(new_cycle)
        db.commit()
        logger.info(f"创建了新的周期记录，ID: {new_cycle.id}, 周期号: {cycle_number}, 开始时间: {start_date}")
        return new_cycle
    
    return current_cycle

def is_time_skipped(date_time: datetime, settings: models.CalendarSettings) -> bool:
    """判断给定时间是否应该被跳过"""
    # 获取设置的起始时间
    start_hour = settings.start_date.hour
    
    # 计算结束时间（默认跳过12小时，可配置）
    skip_hours = settings.skip_hours
    end_hour = (start_hour + skip_hours) % 24
    
    # 获取当前小时
    current_hour = date_time.hour
    
    # 判断是否在跳过时间段内
    if start_hour < end_hour:
        # 简单情况: 起始时间小于结束时间，例如8:00到20:00
        return start_hour <= current_hour < end_hour
    else:
        # 复杂情况: 起始时间大于结束时间，例如20:00到次日8:00
        return current_hour >= start_hour or current_hour < end_hour

def get_skip_period(date: datetime, settings: models.CalendarSettings) -> Dict[str, Any]:
    """获取给定日期的跳过时间段"""
    start_hour = settings.start_date.hour
    skip_hours = settings.skip_hours
    end_hour = (start_hour + skip_hours) % 24
    
    # 格式化时间
    start_time = f"{start_hour:02d}:00"
    end_time = f"{end_hour:02d}:00"
    
    return {
        "date": date.strftime("%Y-%m-%d"),
        "start_time": start_time,
        "end_time": end_time
    }

def calculate_calendar_data(
    db: Session,
    settings: models.CalendarSettings,
    start_date: datetime,
    end_date: datetime,
    current_cycle: Optional[models.CycleRecords] = None
) -> schemas.CalendarResponse:
    """计算日期范围内的日历数据"""
    # 确保日期没有时间部分
    start_date = datetime(start_date.year, start_date.month, start_date.day)
    end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

    logger.debug(f"计算日历数据 - 开始日期: {start_date}, 结束日期: {end_date}")

    # 获取当前周期，如果未提供
    if not current_cycle:
        current_cycle = db.query(models.CycleRecords)\
            .filter(models.CycleRecords.is_completed == False)\
            .order_by(models.CycleRecords.id.desc())\
            .first()

    # 获取指定日期范围内的历史周期
    historical_cycles = db.query(models.CycleRecords)\
        .filter(models.CycleRecords.is_completed == True)\
        .filter(
            # 周期开始日期在查询范围内，或者周期结束日期在查询范围内，或者查询范围在周期内
            (models.CycleRecords.start_date >= start_date) & (models.CycleRecords.start_date <= end_date) |
            (models.CycleRecords.end_date >= start_date) & (models.CycleRecords.end_date <= end_date) |
            (models.CycleRecords.start_date <= start_date) & (models.CycleRecords.end_date >= end_date)
        )\
        .order_by(models.CycleRecords.start_date.desc())\
        .all()

    logger.debug(f"找到 {len(historical_cycles)} 个历史周期在日期范围内")
    
    # 初始化结果
    days = []
    
    # 获取跳过时间段
    skip_periods = []
    if current_cycle:
        skip_periods = db.query(models.SkipPeriod)\
            .filter(models.SkipPeriod.cycle_id == current_cycle.id)\
            .all()
        
        logger.debug(f"获取到的跳过时间段: {skip_periods}")
        
        # 自动计算有效天数和有效小时数
        valid_days, valid_hours = calculate_valid_days_and_hours(current_cycle, skip_periods)
        
        # 更新周期记录
        current_cycle.valid_days_count = valid_days
        current_cycle.valid_hours_count = valid_hours
        db.commit()
    
    valid_days_count = current_cycle.valid_days_count if current_cycle else 0
    valid_hours_count = current_cycle.valid_hours_count if current_cycle else 0.0
    
    # 计算日期范围内的每一天
    current_date = start_date
    while current_date <= end_date:
        # 默认为不跳过
        is_skipped = False
        is_valid = False
        
        # 检查是否在周期时间范围内
        if current_cycle:
            cycle_start_date = current_cycle.start_date.date()
            current_date_only = current_date.date()
            
            # 如果周期已完成，检查是否在周期时间范围内
            if current_cycle.is_completed and current_cycle.end_date:
                cycle_end_date = current_cycle.end_date.date()
                is_valid = cycle_start_date <= current_date_only <= cycle_end_date
            else:
                # 如果周期未完成，检查是否在开始日期之后且不超过当前日期
                today = datetime.now().date()
                is_valid = cycle_start_date <= current_date_only <= today
        
        calendar_day = schemas.CalendarDay(
            date=current_date,
            is_skipped=is_skipped,
            is_valid_day=is_valid,
            is_valid=is_valid  # 添加is_valid字段
        )
        
        # 检查是否是周期开始日
        if current_cycle and current_date.date() == current_cycle.start_date.date():
            logger.debug(f"日期 {current_date.date()} 是周期开始日")
            # 周期开始日不需要特殊处理，在前端会单独标记
            pass
        
        # 检查是否在跳过时间段列表中
        for skip_period in skip_periods:
            # 使用只包含日期部分的比较，忽略时间部分
            skip_date = skip_period.date.date()
            current_date_only = current_date.date()
            
            if current_date_only == skip_date:
                logger.debug(f"日期 {current_date_only} 匹配跳过日期 {skip_date}")
                # 该日期有自定义跳过时间段
                is_skipped = True
                calendar_day.is_skipped = True
                calendar_day.is_valid_day = False
                calendar_day.is_valid = False  # 跳过的日期不是有效日期
                calendar_day.skip_period = {
                    "date": skip_period.date.strftime("%Y-%m-%d"),
                    "start_time": skip_period.start_time,
                    "end_time": skip_period.end_time
                }
                calendar_day.skip_period_id = skip_period.id
                break
        
        days.append(calendar_day)
        
        # 移动到下一天
        current_date += timedelta(days=1)
    
    # 创建响应
    return schemas.CalendarResponse(
        days=days,
        current_cycle=current_cycle,
        historical_cycles=historical_cycles,
        valid_days_count=valid_days_count,
        valid_hours_count=valid_hours_count
    )

def calculate_valid_days_and_hours(cycle: models.CycleRecords, skip_periods: List[models.SkipPeriod], end_time: Optional[datetime] = None) -> tuple[int, float]:
    """
    统一计算当前周期的有效天数和有效小时数
    
    Args:
        cycle: 周期记录
        skip_periods: 跳过时间段列表
        end_time: 结束时间，如果为None则使用当前时间或周期结束时间
    
    Returns:
        tuple: (有效天数, 有效小时数)
    """
    try:
        print(f"[DEBUG] calculate_valid_days_and_hours 开始计算")
        print(f"[DEBUG] cycle: {cycle}")
        print(f"[DEBUG] cycle.start_date: {cycle.start_date if cycle else None}")
        print(f"[DEBUG] cycle.end_date: {cycle.end_date if cycle else None}")
        print(f"[DEBUG] 传入的end_time: {end_time}")
        
        if not cycle or not cycle.start_date:
            print(f"[DEBUG] 周期或开始时间为空，返回 (0, 0.0)")
            return 0, 0.0
        
        # 确定结束时间的优先级：传入的end_time > 周期的end_date > 当前时间
        if end_time is None:
            if cycle.end_date:
                end_time = cycle.end_date
                print(f"[DEBUG] 使用周期结束时间: {end_time}")
            else:
                end_time = datetime.now()
                print(f"[DEBUG] 使用当前时间: {end_time}")
        else:
            print(f"[DEBUG] 使用传入的结束时间: {end_time}")
        
        print(f"[DEBUG] 开始时间: {cycle.start_date}")
        print(f"[DEBUG] 结束时间: {end_time}")
        
        # 检查周期是否已经开始
        if end_time < cycle.start_date:
            print(f"[DEBUG] 周期尚未开始，返回 (0, 0.0)")
            return 0, 0.0
            
        # 计算总时间差（小时）
        total_hours = (end_time - cycle.start_date).total_seconds() / 3600
        print(f"[DEBUG] 总小时数: {total_hours:.4f}")
        
        # 计算跳过的小时数
        skipped_hours = 0
        print(f"[DEBUG] 跳过时间段数量: {len(skip_periods)}")
        
        for period in skip_periods:
            try:
                # 获取跳过日期
                skip_date = period.date.date()
                print(f"[DEBUG] 处理跳过日期: {skip_date}")
                
                # 验证跳过日期是否在周期开始时间之后（防御性检查）
                cycle_start_date = cycle.start_date.date()
                if skip_date < cycle_start_date:
                    print(f"[DEBUG] 跳过日期 {skip_date} 在周期开始日期 {cycle_start_date} 之前，忽略此跳过时间段")
                    continue
                
                # 如果周期已完成，验证跳过日期是否在周期结束时间之前
                if hasattr(cycle, 'is_completed') and cycle.is_completed and hasattr(cycle, 'end_date') and cycle.end_date:
                    cycle_end_date = cycle.end_date.date()
                    if skip_date > cycle_end_date:
                        print(f"[DEBUG] 跳过日期 {skip_date} 在周期结束日期 {cycle_end_date} 之后，忽略此跳过时间段")
                        continue
                
                # 获取跳过时间段
                start_hour, start_minute = map(int, period.start_time.split(':'))
                end_hour, end_minute = map(int, period.end_time.split(':'))
                
                # 创建跳过开始和结束时间的datetime对象
                skip_start = datetime.combine(skip_date, datetime.min.time().replace(hour=start_hour, minute=start_minute))
                skip_end = datetime.combine(skip_date, datetime.min.time().replace(hour=end_hour, minute=end_minute))
                
                # 如果结束时间小于开始时间，说明跨天了
                if end_hour < start_hour or (end_hour == start_hour and end_minute < start_minute):
                    skip_end = skip_end + timedelta(days=1)
                
                print(f"[DEBUG] 跳过时段 - 开始: {skip_start}, 结束: {skip_end}")
                
                # 检查跳过时间段是否在周期时间范围内
                if skip_start > end_time or skip_end < cycle.start_date:
                    # 跳过时间段不在周期内，忽略
                    print(f"[DEBUG] 跳过时段不在周期范围内，忽略")
                    continue
                    
                # 调整跳过时间段的开始和结束时间，确保在周期时间范围内
                adjusted_skip_start = max(skip_start, cycle.start_date)
                adjusted_skip_end = min(skip_end, end_time)
                
                # 计算该时间段跳过的小时数
                skip_hours = (adjusted_skip_end - adjusted_skip_start).total_seconds() / 3600
                if skip_hours > 0:
                    skipped_hours += skip_hours
                
                print(f"[DEBUG] 调整后的跳过时段 - 开始: {adjusted_skip_start}, 结束: {adjusted_skip_end}, 跳过小时数: {skip_hours:.4f}")
            except Exception as e:
                print(f"[DEBUG] 计算跳过小时数时出错: {e}")
        
        # 计算有效小时数和有效天数
        valid_hours = max(0, total_hours - skipped_hours)
        import math
        valid_days = math.ceil(valid_hours / 24) if valid_hours > 0 else 0  # 向上取整
        
        print(f"[DEBUG] 计算结果 - 总小时: {total_hours:.4f}, 跳过小时: {skipped_hours:.4f}, 有效小时: {valid_hours:.4f}, 有效天数: {valid_days}")
        
        # 确保不超过26天和对应的小时数
        max_hours = 26 * 24  # 26天的最大小时数
        if valid_hours > max_hours:
            print(f"[DEBUG] 有效小时数 {valid_hours:.2f} 超过26天限制，调整为 {max_hours}")
            valid_hours = max_hours
        
        valid_days = min(valid_days, 26)
        
        # 确保有效小时数与有效天数一致（如果有效天数被限制为26，小时数也应该相应调整）
        if valid_days == 26 and valid_hours > max_hours:
            valid_hours = max_hours
            print(f"[DEBUG] 调整有效小时数为26天对应的最大值: {valid_hours}")
        
        print(f"[DEBUG] 最终结果 - 有效天数: {valid_days}, 有效小时数: {valid_hours:.4f}")
        
        # 当有效天数达到26天且周期未完成时，记录日志
        if valid_days == 26 and hasattr(cycle, 'is_completed') and not cycle.is_completed:
            print(f"[DEBUG] 周期 {cycle.cycle_number} 有效天数已达到26天，需要完成当前周期并开始新周期")
        
        return valid_days, valid_hours
    except Exception as e:
        print(f"[DEBUG] 计算有效天数和小时数 - 发生异常: {e}")
        import traceback
        traceback.print_exc()
        # 出错时返回0，避免破坏数据
        return 0, 0.0 