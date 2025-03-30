from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database.database import get_db
from app.models import models, schemas
from app.services.calendar_service import calculate_valid_days

router = APIRouter()

@router.get("/", response_model=List[schemas.CycleRecords])
def get_all_cycles(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取所有周期记录"""
    cycles = db.query(models.CycleRecords)\
        .order_by(models.CycleRecords.cycle_number.desc())\
        .offset(skip).limit(limit).all()
    return cycles

@router.get("/current", response_model=schemas.CycleRecords)
def get_current_cycle(db: Session = Depends(get_db)):
    """获取当前进行中的周期"""
    cycle = db.query(models.CycleRecords)\
        .filter(models.CycleRecords.is_completed == False)\
        .order_by(models.CycleRecords.id.desc())\
        .first()
    
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到进行中的周期"
        )
    
    # 获取跳过时间段
    skip_periods = db.query(models.SkipPeriod)\
        .filter(models.SkipPeriod.cycle_id == cycle.id)\
        .all()
    
    # 自动计算有效天数
    cycle.valid_days_count = calculate_valid_days(cycle, skip_periods)
    db.commit()
    
    return cycle

@router.get("/{cycle_id}", response_model=schemas.CycleRecords)
def get_cycle_by_id(cycle_id: int, db: Session = Depends(get_db)):
    """根据ID获取特定周期记录"""
    cycle = db.query(models.CycleRecords).filter(models.CycleRecords.id == cycle_id).first()
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到ID为{cycle_id}的周期记录"
        )
    return cycle

@router.put("/{cycle_id}", response_model=schemas.CycleRecords)
def update_cycle(
    cycle_id: int, 
    cycle_update: schemas.CycleRecordsUpdate,
    db: Session = Depends(get_db)
):
    """更新周期记录"""
    db_cycle = db.query(models.CycleRecords).filter(models.CycleRecords.id == cycle_id).first()
    if not db_cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到ID为{cycle_id}的周期记录"
        )
    
    # 更新字段
    for key, value in cycle_update.dict(exclude_unset=True).items():
        setattr(db_cycle, key, value)
    
    db.commit()
    db.refresh(db_cycle)
    
    # 如果当前周期被标记为完成，检查是否需要创建新周期
    if cycle_update.is_completed and db_cycle.is_completed:
        # 检查是否已有未完成的周期
        existing_cycle = db.query(models.CycleRecords)\
            .filter(models.CycleRecords.is_completed == False)\
            .first()
        
        if not existing_cycle:
            # 创建新周期
            new_cycle = models.CycleRecords(
                cycle_number=db_cycle.cycle_number + 1,
                start_date=datetime.now(),
                valid_days_count=0,
                is_completed=False
            )
            db.add(new_cycle)
            db.commit()
    
    return db_cycle

@router.delete("/{cycle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cycle(cycle_id: int, db: Session = Depends(get_db)):
    """删除周期记录（通常不推荐，仅用于测试或特殊情况）"""
    db_cycle = db.query(models.CycleRecords).filter(models.CycleRecords.id == cycle_id).first()
    if not db_cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到ID为{cycle_id}的周期记录"
        )
    
    db.delete(db_cycle)
    db.commit()
    
    return None

@router.post("/{cycle_id}/complete", response_model=schemas.CycleRecords)
def complete_cycle(cycle_id: int, db: Session = Depends(get_db)):
    """完成当前周期并自动开始新周期"""
    # 查找当前周期
    db_cycle = db.query(models.CycleRecords).filter(models.CycleRecords.id == cycle_id).first()
    if not db_cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到ID为{cycle_id}的周期记录"
        )
    
    # 检查是否已完成
    if db_cycle.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该周期已经完成"
        )
    
    # 标记当前周期为已完成
    db_cycle.is_completed = True
    db_cycle.end_date = datetime.now()
    db.commit()
    db.refresh(db_cycle)
    
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
        cycle_number=db_cycle.cycle_number + 1,
        start_date=start_date,
        valid_days_count=0,
        is_completed=False
    )
    db.add(new_cycle)
    db.commit()
    db.refresh(new_cycle)
    
    return new_cycle

@router.post("/", response_model=schemas.CycleRecords)
def create_cycle(
    cycle_data: schemas.CycleRecordsCreate,
    db: Session = Depends(get_db)
):
    """创建新的周期记录，允许用户自定义开始时间"""
    # 检查是否有未完成的周期
    existing_cycle = db.query(models.CycleRecords)\
        .filter(models.CycleRecords.is_completed == False)\
        .first()
    
    if existing_cycle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已存在一个进行中的周期，请先完成当前周期"
        )
    
    # 确定周期编号
    if cycle_data.cycle_number is None:
        # 查找最后一个周期获取周期号
        last_cycle = db.query(models.CycleRecords)\
            .order_by(models.CycleRecords.cycle_number.desc())\
            .first()
        
        cycle_number = 1
        if last_cycle:
            cycle_number = last_cycle.cycle_number + 1
    else:
        cycle_number = cycle_data.cycle_number
    
    # 创建新周期
    new_cycle = models.CycleRecords(
        cycle_number=cycle_number,
        start_date=cycle_data.start_date,
        valid_days_count=0,
        is_completed=False
    )
    db.add(new_cycle)
    db.commit()
    db.refresh(new_cycle)
    
    return new_cycle 