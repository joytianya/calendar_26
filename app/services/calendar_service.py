from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import logging
from typing import List, Dict, Any, Optional

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
        valid_days = calculate_valid_days(current_cycle, skip_periods)
        
        # 计算有效小时数
        current_date = datetime.now()
        total_hours = (current_date - current_cycle.start_date).total_seconds() / 3600
        
        # 计算跳过的小时数
        skipped_hours = 0
        for period in skip_periods:
            try:
                # 获取跳过日期
                skip_date = period.date.date()
                logger.debug(f"处理跳过日期: {skip_date}, 时间段: {period.start_time}-{period.end_time}")
                
                # 获取跳过时间段
                start_hour, start_minute = map(int, period.start_time.split(':'))
                end_hour, end_minute = map(int, period.end_time.split(':'))
                
                # 计算跳过小时数
                skip_start = datetime.combine(skip_date, datetime.min.time().replace(hour=start_hour, minute=start_minute))
                skip_end = datetime.combine(skip_date, datetime.min.time().replace(hour=end_hour, minute=end_minute))
                
                # 如果结束时间小于开始时间，说明跨天了
                if end_hour < start_hour or (end_hour == start_hour and end_minute < start_minute):
                    skip_end = skip_end + timedelta(days=1)
                
                logger.debug(f"跳过时段计算 - 开始: {skip_start}, 结束: {skip_end}")
                
                # 检查跳过时间段是否在周期时间范围内
                if skip_start > current_date or skip_end < current_cycle.start_date:
                    # 跳过时间段不在周期内，忽略
                    logger.debug(f"跳过时段不在周期范围内，忽略")
                    continue
                    
                # 调整跳过时间段的开始和结束时间，确保在周期时间范围内
                adjusted_skip_start = max(skip_start, current_cycle.start_date)
                adjusted_skip_end = min(skip_end, current_date)
                
                # 计算该时间段跳过的小时数
                skip_hours = (adjusted_skip_end - adjusted_skip_start).total_seconds() / 3600
                skipped_hours += skip_hours
                logger.debug(f"调整后的跳过时段 - 开始: {adjusted_skip_start}, 结束: {adjusted_skip_end}, 跳过小时数: {skip_hours:.2f}")
            except Exception as e:
                logger.error(f"计算有效小时数时出错: {e}", exc_info=True)
        
        # 计算有效小时数
        valid_hours = total_hours - skipped_hours
        
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
        calendar_day = schemas.CalendarDay(
            date=current_date,
            is_skipped=is_skipped,
            is_valid_day=not is_skipped
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
        valid_days_count=valid_days_count,
        valid_hours_count=valid_hours_count
    )

def calculate_valid_days(cycle: models.CycleRecords, skip_periods: List[models.SkipPeriod]) -> int:
    """
    计算当前周期的有效天数
    
    基于从周期开始日期到当前日期之间的天数，减去跳过的天数
    计算规则：从用户设置的小时开始算起，排除跳过的时间，天数向下取整
    """
    try:
        if not cycle:
            return 0
        
        # 获取周期开始日期时间
        cycle_start = cycle.start_date
        logger.debug(f"计算有效天数 - 周期开始日期时间: {cycle_start}")
        
        # 获取当前日期时间
        current_date = datetime.now()
        logger.debug(f"计算有效天数 - 当前日期时间: {current_date}")
        
        # 检查周期是否已经开始
        if current_date < cycle_start:
            logger.debug(f"计算有效天数 - 周期尚未开始")
            return 0
            
        # 计算总时间差（小时）
        total_hours = (current_date - cycle_start).total_seconds() / 3600
        logger.debug(f"计算有效天数 - 总小时数: {total_hours:.2f}小时")
        
        # 计算跳过的小时数
        skipped_hours = 0
        skipped_dates = set()
        
        for period in skip_periods:
            try:
                # 获取跳过日期，确保使用正确的日期部分
                skip_date = period.date.date()
                skipped_dates.add(skip_date)
                logger.debug(f"处理跳过日期: {skip_date}")
                
                # 获取跳过时间段，以北京时间为准
                start_hour, start_minute = map(int, period.start_time.split(':'))
                end_hour, end_minute = map(int, period.end_time.split(':'))
                
                # 创建跳过开始和结束时间的datetime对象，使用北京时间
                # 注意：在组合日期和时间时，确保当日的00:00:00作为基准
                skip_start = datetime.combine(skip_date, datetime.min.time().replace(hour=start_hour, minute=start_minute))
                skip_end = datetime.combine(skip_date, datetime.min.time().replace(hour=end_hour, minute=end_minute))
                
                # 如果结束时间小于开始时间，说明跨天了
                if end_hour < start_hour or (end_hour == start_hour and end_minute < start_minute):
                    skip_end = skip_end + timedelta(days=1)
                
                logger.debug(f"跳过时段(北京时间) - 开始: {skip_start}, 结束: {skip_end}")
                
                # 检查跳过时间段是否在周期时间范围内
                if skip_start > current_date or skip_end < cycle_start:
                    # 跳过时间段不在周期内，忽略
                    logger.debug(f"跳过时段不在周期范围内，忽略")
                    continue
                    
                # 调整跳过时间段的开始和结束时间，确保在周期时间范围内
                adjusted_skip_start = max(skip_start, cycle_start)
                adjusted_skip_end = min(skip_end, current_date)
                
                # 计算该时间段跳过的小时数
                skip_hours = (adjusted_skip_end - adjusted_skip_start).total_seconds() / 3600
                skipped_hours += skip_hours
                
                logger.debug(f"计算有效天数 - 跳过日期: {skip_date}, 时段: {period.start_time}-{period.end_time}, 跳过小时: {skip_hours:.2f}")
            except Exception as e:
                logger.error(f"计算有效天数 - 处理跳过日期时出错: {e}, period: {period}", exc_info=True)
        
        # 计算有效小时数和有效天数
        valid_hours = total_hours - skipped_hours
        valid_days = int(valid_hours / 24)  # 向下取整
        
        logger.info(f"计算有效天数 - 总小时: {total_hours:.2f}, 跳过小时: {skipped_hours:.2f}, 有效小时: {valid_hours:.2f}, 有效天数: {valid_days}")
        
        # 确保不超过26天
        valid_days = min(valid_days, 26)
        
        # 当有效天数达到26天且周期未完成时，自动完成当前周期并开始新周期
        if valid_days == 26 and not cycle.is_completed:
            logger.info(f"周期 {cycle.cycle_number} 有效天数已达到26天，自动完成当前周期并开始新周期")
            try:
                from sqlalchemy.orm import Session
                from app.database.database import SessionLocal
                
                db = SessionLocal()
                try:
                    # 标记当前周期为已完成
                    cycle.is_completed = True
                    cycle.end_date = current_date
                    db.commit()
                    
                    # 获取用户设置的起始时间
                    settings = db.query(models.CalendarSettings).first()
                    start_date = current_date
                    
                    # 如果有设置，使用设置的开始时间
                    if settings:
                        # 使用当前日期，但使用设置中的时间部分
                        now = current_date
                        start_date = datetime(
                            now.year,
                            now.month,
                            now.day,
                            settings.start_date.hour,
                            settings.start_date.minute,
                            0
                        )
                    
                    # 创建新周期
                    new_cycle = models.CycleRecords(
                        cycle_number=cycle.cycle_number + 1,
                        start_date=start_date,
                        valid_days_count=0,
                        valid_hours_count=0.0,
                        is_completed=False
                    )
                    db.add(new_cycle)
                    db.commit()
                    logger.info(f"创建了新的周期记录，ID: {new_cycle.id}, 周期号: {new_cycle.cycle_number}, 开始时间: {start_date}")
                except Exception as e:
                    logger.error(f"自动完成周期并创建新周期时出错: {e}", exc_info=True)
                    db.rollback()
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"自动完成周期时导入SessionLocal出错: {e}", exc_info=True)
        
        return valid_days
    except Exception as e:
        logger.error(f"计算有效天数 - 发生异常: {e}", exc_info=True)
        # 出错时返回当前保存的有效天数，避免破坏数据
        return cycle.valid_days_count if cycle else 0 