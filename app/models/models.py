from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, ForeignKey, Time, Float
from sqlalchemy.orm import relationship
from datetime import datetime, time

from app.database.database import Base

class CalendarSettings(Base):
    """日历设置模型"""
    __tablename__ = "calendar_settings"

    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(DateTime, nullable=False)
    skip_hours = Column(Integer, default=12)  # 默认跳过12小时
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class CycleRecords(Base):
    """周期记录模型"""
    __tablename__ = "cycle_records"

    id = Column(Integer, primary_key=True, index=True)
    cycle_number = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    skip_periods = Column(JSON, nullable=True)  # 存储跳过时段的JSON数据
    valid_days_count = Column(Integer, default=0)
    valid_hours_count = Column(Float, default=0.0)  # 添加有效小时数字段
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 与跳过时间段的关系
    skip_period_records = relationship("SkipPeriod", back_populates="cycle")

class SkipPeriod(Base):
    """跳过时间段模型"""
    __tablename__ = "skip_periods"
    
    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, ForeignKey("cycle_records.id"))
    date = Column(DateTime, nullable=False)
    start_time = Column(String, nullable=False)  # 存储为HH:MM格式
    end_time = Column(String, nullable=False)    # 存储为HH:MM格式
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    cycle = relationship("CycleRecords", back_populates="skip_period_records") 