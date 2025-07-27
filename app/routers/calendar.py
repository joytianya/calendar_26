from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, date
import logging

from app.database.database import get_db
from app.models import models, schemas
from app.services import calendar_service
from app.services.calendar_service import calculate_valid_days_and_hours

router = APIRouter()

# 获取路由专用日志记录器
logger = logging.getLogger("api.calendar")

@router.post("/settings", response_model=schemas.CalendarSettings)
def create_settings(
    settings: schemas.CalendarSettingsCreate, 
    db: Session = Depends(get_db)
):
    """创建或更新日历设置"""
    # 记录是否为首次创建设置
    is_new_settings = False
    
    # 检查是否已有设置
    db_settings = db.query(models.CalendarSettings).first()
    if db_settings:
        # 更新现有设置
        logger.info(f"更新现有日历设置，ID: {db_settings.id}")
        for key, value in settings.dict().items():
            setattr(db_settings, key, value)
    else:
        # 创建新设置
        is_new_settings = True
        logger.info(f"创建新的日历设置")
        db_settings = models.CalendarSettings(**settings.dict())
        db.add(db_settings)
    
    db.commit()
    db.refresh(db_settings)
    logger.info(f"日历设置已保存，开始时间: {db_settings.start_date}")
    
    # 获取当前周期，不论是新建还是更新设置
    current_cycle = db.query(models.CycleRecords)\
        .filter(models.CycleRecords.is_completed == False)\
        .order_by(models.CycleRecords.id.desc())\
        .first()
    
    if current_cycle and settings.start_date:
        # 同步更新当前周期的开始时间
        before_date = current_cycle.start_date
        # 直接使用设置中的完整日期和时间
        current_cycle.start_date = settings.start_date
        logger.info(f"更新周期ID {current_cycle.id} 的开始时间: {before_date} -> {settings.start_date}")
        
        # 重新计算有效天数和小时数
        skip_periods = db.query(models.SkipPeriod)\
            .filter(models.SkipPeriod.cycle_id == current_cycle.id)\
            .all()
        valid_days, valid_hours = calculate_valid_days_and_hours(current_cycle, skip_periods)
        current_cycle.valid_days_count = valid_days
        current_cycle.valid_hours_count = valid_hours
        logger.info(f"更新周期ID {current_cycle.id} 的有效天数为: {valid_days}, 有效小时数为: {valid_hours:.2f}")
        
        db.commit()
    elif is_new_settings and settings.start_date:
        # 如果是首次创建设置，但没有周期记录，主动创建一个新周期
        logger.info(f"首次设置时间，没有周期记录，立即创建新周期")
        
        # 查找最后一个周期获取周期号
        last_cycle = db.query(models.CycleRecords)\
            .order_by(models.CycleRecords.cycle_number.desc())\
            .first()
        
        cycle_number = 1
        if last_cycle:
            cycle_number = last_cycle.cycle_number + 1
        
        # 直接使用设置中的完整开始时间
        new_cycle = models.CycleRecords(
            cycle_number=cycle_number,
            start_date=settings.start_date,  # 使用设置的完整时间
            valid_days_count=0,
            is_completed=False
        )
        db.add(new_cycle)
        db.commit()
        logger.info(f"创建了新周期，ID: {new_cycle.id}, 周期号: {cycle_number}, 开始时间: {settings.start_date}")
        return db_settings  # 提前返回，跳过check_and_create_cycle
    
    # 后续场景：更新设置但无现有周期，或其他情况，由check_and_create_cycle处理
    calendar_service.check_and_create_cycle(db)
    
    return db_settings

@router.get("/settings", response_model=schemas.CalendarSettings)
def get_settings(db: Session = Depends(get_db)):
    """获取日历设置"""
    settings = db.query(models.CalendarSettings).first()
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到日历设置，请先创建设置"
        )
    return settings

@router.get("/data", response_model=schemas.CalendarResponse)
def get_calendar_data(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """获取日历数据
    
    如果未指定开始和结束日期，则默认返回当前月份的数据
    """
    # 获取日历设置
    settings = db.query(models.CalendarSettings).first()
    
    # 如果未指定日期范围，默认返回当前月份
    if not start_date:
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
    else:
        # 处理带Z后缀的ISO格式时间字符串
        if start_date.endswith('Z'):
            start_date = start_date[:-1]  # 移除Z后缀
        start_date = datetime.fromisoformat(start_date.replace('.000', ''))
        
    if not end_date:
        # 默认显示一个月
        next_month = start_date.month + 1 if start_date.month < 12 else 1
        next_year = start_date.year if start_date.month < 12 else start_date.year + 1
        end_date = datetime(next_year, next_month, 1) - timedelta(days=1)
    else:
        # 处理带Z后缀的ISO格式时间字符串
        if end_date.endswith('Z'):
            end_date = end_date[:-1]  # 移除Z后缀
        end_date = datetime.fromisoformat(end_date.replace('.000', ''))
    
    # 如果没有设置，返回空日历数据
    if not settings:
        return {
            "days": [],
            "current_cycle": None,
            "valid_days_count": 0,
            "valid_hours_count": 0
        }
    
    # 获取当前周期
    current_cycle = db.query(models.CycleRecords)\
        .filter(models.CycleRecords.is_completed == False)\
        .order_by(models.CycleRecords.id.desc())\
        .first()
    
    # 计算日历数据
    calendar_data = calendar_service.calculate_calendar_data(
        db, settings, start_date, end_date, current_cycle
    )
    
    return calendar_data

@router.post("/increment-day")
def increment_valid_day(db: Session = Depends(get_db)):
    """增加有效天数计数，如果达到26天则完成当前周期并开始新周期"""
    # 获取当前进行中的周期
    current_cycle = db.query(models.CycleRecords)\
        .filter(models.CycleRecords.is_completed == False)\
        .order_by(models.CycleRecords.id.desc())\
        .first()
    
    if not current_cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到进行中的周期"
        )
    
    # 增加有效小时数 (增加24小时，相当于一天)
    current_cycle.valid_hours_count += 24
    
    # 从有效小时数重新计算有效天数
    current_cycle.valid_days_count = int(current_cycle.valid_hours_count / 24)
    
    # 检查是否达到26天
    if current_cycle.valid_days_count >= 26:
        # 完成当前周期
        current_cycle.is_completed = True
        current_cycle.end_date = datetime.now()
        
        # 获取用户设置的起始时间
        settings = db.query(models.CalendarSettings).first()
        start_date = datetime.now()
        
        # 如果有设置，使用设置的开始时间
        if settings:
            # 使用当前日期，但使用设置中的时间部分
            now = datetime.now()
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
            cycle_number=current_cycle.cycle_number + 1,
            start_date=start_date,
            valid_days_count=0,
            valid_hours_count=0,
            is_completed=False
        )
        db.add(new_cycle)
    
    db.commit()
    
    return {"message": "有效天数已更新", "valid_days_count": current_cycle.valid_days_count}

@router.post("/skip-period-validated", response_model=schemas.SkipPeriod)
def set_skip_period(
    skip_period_data: schemas.SkipPeriodCreate,
    db: Session = Depends(get_db)
):
    """设置特定日期的跳过时间段"""
    try:
        logger.info(f"设置跳过时间段 - 接收数据: {skip_period_data}")
        
        # 获取当前周期
        cycle = db.query(models.CycleRecords).filter(models.CycleRecords.id == skip_period_data.cycle_id).first()
        if not cycle:
            logger.warning(f"未找到周期 ID: {skip_period_data.cycle_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到ID为{skip_period_data.cycle_id}的周期"
            )
        
        # 处理日期字符串并考虑时区
        input_date = skip_period_data.date
        logger.info(f"输入日期原始值: {input_date}")
        
        # 提取日期部分并处理时区问题
        if isinstance(input_date, str):
            try:
                # 检查是否包含时区信息
                has_timezone = '+' in input_date or 'Z' in input_date
                
                # 仅提取日期部分（YYYY-MM-DD）
                if 'T' in input_date:
                    date_part = input_date.split('T')[0]
                else:
                    date_part = input_date.split(' ')[0]
                
                date_parts = date_part.split('-')
                
                if len(date_parts) != 3:
                    raise ValueError(f"无效的日期格式: {input_date}")
                
                year, month, day = map(int, date_parts)
                
                # 如果日期字符串包含Z（UTC时间），自动加一天
                # 这是一个简单的方法来处理UTC和北京时间之间的转换问题
                if 'Z' in input_date:
                    # 记录调整前的日期
                    before_date = f"{year}-{month:02d}-{day:02d}"
                    
                    # 创建日期并加一天
                    date_obj = datetime(year, month, day)
                    date_obj = date_obj + timedelta(days=1)
                    year, month, day = date_obj.year, date_obj.month, date_obj.day
                    
                    # 记录调整后的日期
                    after_date = f"{year}-{month:02d}-{day:02d}"
                    logger.info(f"检测到UTC时间格式，自动加一天: {before_date} -> {after_date}")
                
                # 明确记录用户选择的日期（可能已经调整过）
                logger.info(f"最终使用的日期 (YYYY-MM-DD): {year}-{month:02d}-{day:02d}")
                
                # 使用中午12点创建日期，避免时区问题
                date_only = datetime(year, month, day, 12, 0, 0)
                
                if has_timezone:
                    logger.info(f"输入包含时区信息: {input_date}")
                    logger.info(f"处理后的日期: {date_only}")
                
                logger.info(f"从字符串解析的日期: {date_only}")
            except Exception as e:
                logger.error(f"解析日期字符串失败: {str(e)}, 原始日期: {input_date}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无法解析日期: {input_date}, 错误: {str(e)}"
                )
        else:
            # 处理datetime对象
            try:
                # 如果是datetime对象，记录原始值并提取日期部分
                logger.info(f"输入是datetime对象: {input_date}")
                if hasattr(input_date, 'tzinfo') and input_date.tzinfo is not None:
                    logger.info(f"输入datetime带时区: {input_date.tzinfo}")
                    # 如果是UTC时区，将其转换为北京时间的日期（加8小时）
                    if str(input_date.tzinfo) == 'UTC':
                        # 转换为北京时间 (UTC+8)，通常是加一天
                        beijing_date = input_date + timedelta(days=1)
                        logger.info(f"UTC日期对象自动加一天: {input_date.date()} -> {beijing_date.date()}")
                        date_only = datetime(
                            beijing_date.year,
                            beijing_date.month,
                            beijing_date.day,
                            12, 0, 0
                        )
                    else:
                        # 使用原始日期部分
                        date_only = datetime(
                            input_date.year,
                            input_date.month,
                            input_date.day,
                            12, 0, 0
                        )
                else:
                    # 无时区信息，直接使用
                    date_only = datetime(
                        input_date.year,
                        input_date.month,
                        input_date.day,
                        12, 0, 0
                    )
                logger.info(f"使用的日期: {date_only}")
            except Exception as e:
                logger.error(f"从datetime对象提取日期失败: {str(e)}, 原始日期: {input_date}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无法处理日期对象: {str(e)}"
                )
        
        logger.info(f"处理日期 - 输入: {input_date}, 处理后: {date_only}")
        
        # 验证跳过日期是否在周期开始时间之后
        skip_date = date_only.date()
        cycle_start_date = cycle.start_date.date()
        
        logger.info(f"[VALIDATION] 验证跳过日期: {skip_date}, 周期开始日期: {cycle_start_date}")
        
        if skip_date < cycle_start_date:
            error_msg = f"跳过日期 {skip_date} 不能在周期开始时间 {cycle_start_date} 之前"
            logger.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # 如果周期已完成，验证跳过日期是否在周期结束时间之前
        if cycle.is_completed and cycle.end_date:
            cycle_end_date = cycle.end_date.date()
            if skip_date > cycle_end_date:
                error_msg = f"跳过日期 {skip_date} 不能在周期结束时间 {cycle_end_date} 之后"
                logger.warning(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
        
        logger.info(f"跳过日期验证通过: {skip_date} 在周期范围内")
        
        # 检查是否已存在该日期的跳过时间段
        existing_skip_periods = db.query(models.SkipPeriod)\
            .filter(models.SkipPeriod.cycle_id == skip_period_data.cycle_id)\
            .all()
        
        # 手动筛选匹配的日期记录
        found_record = None
        for record in existing_skip_periods:
            record_date = record.date.date()
            input_date_only = date_only.date()
            
            logger.debug(f"比较日期 - 记录: {record_date}, 输入: {input_date_only}")
            
            if record_date == input_date_only:
                found_record = record
                logger.info(f"找到匹配记录 ID: {record.id}")
                break
        
        if found_record:
            # 更新现有记录
            found_record.start_time = skip_period_data.start_time
            found_record.end_time = skip_period_data.end_time
            db.commit()
            db.refresh(found_record)
            result = found_record
            logger.info(f"更新现有记录 ID: {found_record.id}")
        else:
            # 创建新记录，确保使用正确的日期
            new_skip_period = models.SkipPeriod(
                cycle_id=skip_period_data.cycle_id,
                date=date_only,
                start_time=skip_period_data.start_time,
                end_time=skip_period_data.end_time
            )
            db.add(new_skip_period)
            db.commit()
            db.refresh(new_skip_period)
            result = new_skip_period
            logger.info(f"创建新记录 ID: {new_skip_period.id}")
        
        # 获取所有跳过时间段
        skip_periods = db.query(models.SkipPeriod)\
            .filter(models.SkipPeriod.cycle_id == cycle.id)\
            .all()
        
        # 重新计算有效天数和小时数
        valid_days, valid_hours = calculate_valid_days_and_hours(cycle, skip_periods)
        cycle.valid_days_count = valid_days
        cycle.valid_hours_count = valid_hours
        logger.info(f"更新周期ID {cycle.id} 的有效天数为: {valid_days}, 有效小时数为: {valid_hours:.2f}")
        
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"设置跳过时间段失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置跳过时间段失败: {str(e)}"
        )

@router.get("/skip-periods/{cycle_id}", response_model=List[schemas.SkipPeriod])
def get_skip_periods(
    cycle_id: int,
    db: Session = Depends(get_db)
):
    """获取特定周期的所有跳过时间段"""
    skip_periods = db.query(models.SkipPeriod)\
        .filter(models.SkipPeriod.cycle_id == cycle_id)\
        .all()
    
    return skip_periods

@router.delete("/skip-periods/{period_id}", response_model=dict)
async def delete_skip_period(
    period_id: int,
    db: Session = Depends(get_db)
):
    """
    删除指定的跳过周期
    """
    try:
        logger.info(f"正在尝试删除跳过周期, ID: {period_id}")
        # 检查是否存在该跳过周期
        period = db.query(models.SkipPeriod).filter(models.SkipPeriod.id == period_id).first()
        if not period:
            logger.warning(f"找不到跳过周期, ID: {period_id}")
            raise HTTPException(status_code=404, detail=f"找不到ID为{period_id}的跳过周期")
            
        # 记录要删除的跳过周期信息
        logger.info(f"准备删除跳过周期: ID={period_id}, 日期={period.date}, 周期ID={period.cycle_id}")
        
        # 获取当前周期 - 用于后续更新有效天数
        current_cycle = db.query(models.CycleRecords).filter(models.CycleRecords.id == period.cycle_id).first()
        if not current_cycle:
            logger.warning(f"找不到对应的周期记录, 周期ID: {period.cycle_id}")
            raise HTTPException(status_code=404, detail=f"找不到ID为{period.cycle_id}的周期记录")
        
        # 保存删除前的信息
        period_data = {
            "id": period_id,
            "date": period.date.isoformat(),
            "start_time": period.start_time,
            "end_time": period.end_time,
            "cycle_id": period.cycle_id
        }
        
        # 删除跳过周期
        db.delete(period)
        db.commit()
        logger.info(f"成功删除跳过周期, ID: {period_id}")
        
        # 获取更新后的跳过周期列表
        remaining_skip_periods = db.query(models.SkipPeriod).filter(models.SkipPeriod.cycle_id == current_cycle.id).all()
        logger.info(f"剩余跳过周期数量: {len(remaining_skip_periods)}")
        
        # 重新计算有效天数和小时数
        valid_days, valid_hours = calculate_valid_days_and_hours(current_cycle, remaining_skip_periods)
        logger.info(f"重新计算的有效天数: {valid_days}, 有效小时数: {valid_hours:.2f}")
        
        # 更新周期记录的有效天数
        current_cycle.valid_days_count = valid_days
        current_cycle.valid_hours_count = valid_hours
        db.commit()
        logger.info(f"已更新周期ID {current_cycle.id} 的有效天数为 {valid_days}, 有效小时数为 {valid_hours:.2f}")
        
        # 返回删除结果
        return {
            "success": True,
            "message": f"成功删除跳过时间段 ID: {period_id}",
            "deleted_period": period_data
        }
    except HTTPException as e:
        # 直接重新抛出HTTP异常
        raise e
    except Exception as e:
        error_msg = f"删除跳过周期时发生错误: {str(e)}"
        logger.error(error_msg, exc_info=True)
        # 回滚事务
        db.rollback()
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/reset", status_code=status.HTTP_200_OK)
def reset_calendar(db: Session = Depends(get_db)):
    """重置日历，删除所有设置和周期记录"""
    try:
        # 删除所有跳过时间段
        db.query(models.SkipPeriod).delete()
        
        # 删除所有周期记录
        db.query(models.CycleRecords).delete()
        
        # 删除日历设置
        db.query(models.CalendarSettings).delete()
        
        db.commit()
        return {"message": "日历已重置，所有数据已清除"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置日历失败: {str(e)}"
        ) 