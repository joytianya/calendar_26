import axios from 'axios';
import { 
  CalendarResponse, 
  CalendarSettings, 
  CalendarSettingsCreate,
  CycleRecord,
  CycleRecordUpdate,
  SkipPeriod,
  SkipPeriodCreate
} from '../models/types';

// 声明window._env_的类型
declare global {
  interface Window {
    _env_?: {
      REACT_APP_API_URL?: string;
    };
  }
}

// 从window._env_对象中读取API地址，或使用默认值
const getApiUrl = () => {
  if (window._env_ && window._env_.REACT_APP_API_URL) {
    return window._env_.REACT_APP_API_URL;
  }
  // 本地开发环境默认地址
  return process.env.REACT_APP_API_URL || 'http://localhost:8000';
};

// 设置API基础URL，支持本地开发和生产环境
const API_BASE_URL = getApiUrl();

// 处理API URL格式，确保末尾有/api
const getBaseUrl = () => {
  let baseUrl = API_BASE_URL;
  // 如果baseUrl已经包含/api，则不添加
  if (!baseUrl.endsWith('/api')) {
    // 如果baseUrl以/结尾，则直接添加api
    if (baseUrl.endsWith('/')) {
      baseUrl = baseUrl + 'api';
    } else {
      // 否则添加/api
      baseUrl = baseUrl + '/api';
    }
  }
  console.log('使用API基础地址:', baseUrl);
  return baseUrl;
};

// 创建axios实例
const api = axios.create({
  baseURL: getBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

// 日历设置相关API
export const calendarSettingsApi = {
  // 获取设置
  getSettings: async (): Promise<CalendarSettings> => {
    const response = await api.get<CalendarSettings>('/calendar/settings');
    return response.data;
  },
  
  // 创建或更新设置
  createSettings: async (settings: CalendarSettingsCreate): Promise<CalendarSettings> => {
    const response = await api.post<CalendarSettings>('/calendar/settings', settings);
    return response.data;
  },
  
  // 重置日历
  resetCalendar: async (): Promise<void> => {
    await api.post('/calendar/reset');
  },
};

// 日历数据相关API
export const calendarDataApi = {
  // 获取日历数据
  getCalendarData: async (startDate: string, endDate: string): Promise<CalendarResponse> => {
    const response = await api.get<CalendarResponse>('/calendar/data', {
      params: { start_date: startDate, end_date: endDate }
    });
    return response.data;
  },
  
  // 获取跳过时间段列表
  getSkipPeriods: async (cycleId: number): Promise<SkipPeriod[]> => {
    const response = await api.get<SkipPeriod[]>(`/calendar/skip-periods/${cycleId}`);
    return response.data;
  },
  
  // 设置跳过时间段
  setSkipPeriod: async (data: SkipPeriodCreate): Promise<SkipPeriod> => {
    console.log('API调用 - 设置跳过时间段，发送数据:', JSON.stringify(data));
    
    // 确保日期字段是纯日期字符串，不包含时间部分
    let requestData = { ...data };
    if (typeof data.date === 'string' && data.date.length === 10) {
      // 如果是纯日期字符串 (YYYY-MM-DD)，不做修改
      console.log('API调用 - 使用纯日期字符串:', data.date);
    } else if (typeof data.date === 'string' && data.date.includes('T')) {
      // 如果包含时间部分，只取日期部分
      requestData.date = data.date.split('T')[0];
      console.log('API调用 - 提取ISO日期字符串中的日期部分:', requestData.date);
    }
    
    console.log('API调用 - 最终发送数据:', JSON.stringify(requestData));
    const response = await api.post<SkipPeriod>('/calendar/skip-period', requestData);
    return response.data;
  },
  
  // 删除跳过时间段
  deleteSkipPeriod: async (periodId: number): Promise<{
    success: boolean;
    message: string;
    deleted_period: {
      id: number;
      date: string;
      start_time: string;
      end_time: string;
      cycle_id: number;
    };
  }> => {
    console.log(`准备删除跳过时间段，ID: ${periodId}`);
    try {
      const response = await api.delete(`/calendar/skip-periods/${periodId}`);
      console.log(`成功删除跳过时间段，响应:`, response.data);
      return response.data;
    } catch (error) {
      console.error(`删除跳过时间段失败，错误:`, error);
      if (axios.isAxiosError(error)) {
        console.error(`状态码: ${error.response?.status}, 错误信息: ${error.response?.data?.detail || error.message}`);
      }
      throw error;
    }
  },
  
  // 增加有效天数
  incrementValidDay: async (): Promise<{ message: string; valid_days_count: number }> => {
    const response = await api.post<{ message: string; valid_days_count: number }>('/calendar/increment-day');
    return response.data;
  }
};

// 周期记录相关API
export const cyclesApi = {
  // 获取所有周期记录
  getAllCycles: async (): Promise<CycleRecord[]> => {
    const response = await api.get<CycleRecord[]>('/cycles');
    return response.data;
  },
  
  // 获取当前周期
  getCurrentCycle: async (): Promise<CycleRecord> => {
    const response = await api.get<CycleRecord>('/cycles/current');
    return response.data;
  },
  
  // 获取特定周期
  getCycle: async (id: number): Promise<CycleRecord> => {
    const response = await api.get<CycleRecord>(`/cycles/${id}`);
    return response.data;
  },
  
  // 创建新周期
  createCycle: async (data: { start_date: string }): Promise<CycleRecord> => {
    const response = await api.post<CycleRecord>('/cycles', data);
    return response.data;
  },
  
  // 更新周期
  updateCycle: async (id: number, data: CycleRecordUpdate): Promise<CycleRecord> => {
    const response = await api.put<CycleRecord>(`/cycles/${id}`, data);
    return response.data;
  },
  
  // 完成周期并开始新周期
  completeCycle: async (id: number): Promise<CycleRecord> => {
    const response = await api.post<CycleRecord>(`/cycles/${id}/complete`);
    return response.data;
  },
};

export default api;