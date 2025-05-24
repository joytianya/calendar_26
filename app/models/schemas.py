from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, List, Any, Union

# 日历设置模型
class CalendarSettingsBase(BaseModel):
    start_date: datetime
    skip_hours: Optional[int] = 12

class CalendarSettingsCreate(CalendarSettingsBase):
    pass

class CalendarSettings(CalendarSettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 跳过时间段模型
class SkipPeriodBase(BaseModel):
    date: Union[datetime, str]  # 允许接收字符串或datetime对象
    start_time: str
    end_time: str

class SkipPeriodCreate(SkipPeriodBase):
    cycle_id: int

class SkipPeriod(SkipPeriodBase):
    id: int
    cycle_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 周期记录模型
class CycleRecordsBase(BaseModel):
    cycle_number: int
    start_date: datetime
    end_date: Optional[datetime] = None
    skip_periods: Optional[Dict[str, Any]] = None
    valid_days_count: int = 0
    valid_hours_count: float = 0.0
    is_completed: bool = False
    remark: Optional[str] = None

class CycleRecordsCreate(BaseModel):
    start_date: datetime
    cycle_number: Optional[int] = None
    remark: Optional[str] = None

class CycleRecordsUpdate(BaseModel):
    start_date: Optional[datetime] = None
    cycle_number: Optional[int] = None
    end_date: Optional[datetime] = None
    valid_days_count: Optional[int] = None
    is_completed: Optional[bool] = None
    remark: Optional[str] = None

class CycleRecords(CycleRecordsBase):
    id: int
    created_at: datetime
    updated_at: datetime
    skip_period_records: Optional[List[SkipPeriod]] = None

    class Config:
        from_attributes = True

# 日历数据响应模型
class CalendarDay(BaseModel):
    date: datetime
    is_skipped: bool
    skip_period: Optional[Dict[str, Any]] = None
    skip_period_id: Optional[int] = None
    is_valid_day: bool = True
    
class CalendarResponse(BaseModel):
    days: List[CalendarDay]
    current_cycle: Optional[CycleRecords] = None
    valid_days_count: int
    valid_hours_count: float = 0.0 