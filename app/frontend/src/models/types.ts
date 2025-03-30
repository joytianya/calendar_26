// 日历设置类型
export interface CalendarSettings {
  id: number;
  start_date: string;
  skip_hours: number;
  created_at: string;
  updated_at: string;
}

export interface CalendarSettingsCreate {
  start_date: string;
  skip_hours: number;
}

// 跳过时间段类型
export interface SkipPeriod {
  id: number;
  cycle_id: number;
  date: string;
  start_time: string;
  end_time: string;
  created_at: string;
  updated_at: string;
}

export interface SkipPeriodCreate {
  cycle_id: number;
  date: string;
  start_time: string;
  end_time: string;
}

// 周期记录类型
export interface CycleRecord {
  id: number;
  cycle_number: number;
  start_date: string;
  end_date: string | null;
  skip_periods: any | null;
  valid_days_count: number;
  valid_hours_count: number;
  is_completed: boolean;
  created_at: string;
  updated_at: string;
  skip_period_records?: SkipPeriod[];
}

export interface CycleRecordUpdate {
  end_date?: string;
  valid_days_count?: number;
  is_completed?: boolean;
}

// 日历数据类型
export interface CalendarDay {
  date: string;
  is_skipped: boolean;
  skip_period?: {
    date: string;
    start_time: string;
    end_time: string;
  };
  skip_period_id?: number;
  is_valid_day: boolean;
}

export interface CalendarResponse {
  days: CalendarDay[];
  current_cycle: CycleRecord | null;
  valid_days_count: number;
  valid_hours_count: number;
} 