import React, { useState, useEffect } from 'react';
import { Calendar as BigCalendar, momentLocalizer } from 'react-big-calendar';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import moment from 'moment';
import 'moment/locale/zh-cn';
import { CalendarResponse, CycleRecord, SkipPeriodCreate } from '../models/types';
import { calendarDataApi, cyclesApi } from '../services/api';
import { 
  Box, 
  Typography, 
  Paper, 
  Alert, 
  CircularProgress, 
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Button,
  TextField,
  Snackbar
} from '@mui/material';
import axios from 'axios';

// 配置 moment 本地化
moment.locale('zh-cn');
const localizer = momentLocalizer(moment);

interface CalendarProps {
  onDayClick?: (day: Date) => void;
  currentCycle: CycleRecord | null;
  onCycleCompleted?: () => void;
  onCycleUpdated?: () => void;
}

interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  allDay: boolean;
  resource?: {
    isSkipped: boolean;
    isStartDay: boolean;
  };
}

// 获取API基础URL
const getApiUrl = () => {
  if (window._env_ && window._env_.REACT_APP_API_URL) {
    return window._env_.REACT_APP_API_URL;
  }
  return process.env.REACT_APP_API_URL || 'http://localhost:8000';
};

const Calendar: React.FC<CalendarProps> = ({ onDayClick, currentCycle, onCycleCompleted, onCycleUpdated }) => {
  const [calendarData, setCalendarData] = useState<CalendarResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isMobile, setIsMobile] = useState<boolean>(window.innerWidth < 768);
  
  // 跳过时间段对话框状态
  const [skipDialogOpen, setSkipDialogOpen] = useState<boolean>(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [skipStartTime, setSkipStartTime] = useState<string>('08:00');
  const [skipEndTime, setSkipEndTime] = useState<string>('20:00');
  const [saveLoading, setSaveLoading] = useState<boolean>(false);
  
  // 成功提示状态
  const [snackbarOpen, setSnackbarOpen] = useState<boolean>(false);
  const [snackbarMessage, setSnackbarMessage] = useState<string>('');
  
  // 周期完成对话框状态
  const [cycleCompletedDialogOpen, setCycleCompletedDialogOpen] = useState<boolean>(false);
  
  // 新增状态变量
  const [existingSkipPeriod, setExistingSkipPeriod] = useState<{id: number, date: string, start_time: string, end_time: string} | null>(null);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit' | 'delete'>('create');
  
  // 添加日历视图日期范围状态
  const [viewDate, setViewDate] = useState<Date>(new Date());
  
  // 添加窗口大小监听
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  // 获取日历数据
  const fetchCalendarData = async () => {
    try {
      setLoading(true);
      
      // 获取当前日期
      const now = new Date();
      
      // 如果有当前周期，使用周期开始日期作为起始日期
      let startDate, endDate;
      if (currentCycle && currentCycle.start_date) {
        const cycleStartDate = new Date(currentCycle.start_date);
        // 获取从周期开始日期所在月的第一天
        startDate = new Date(cycleStartDate.getFullYear(), cycleStartDate.getMonth(), 1);
        
        // 计算结束日期：从周期开始日期起至少显示26天
        const minEndDate = new Date(cycleStartDate);
        minEndDate.setDate(minEndDate.getDate() + 26);
        
        // 获取到minEndDate所在月份的最后一天
        endDate = new Date(minEndDate.getFullYear(), minEndDate.getMonth() + 1, 0);
        
        console.log('使用周期日期范围 - 开始:', startDate.toISOString(), '结束:', endDate.toISOString());
      } else {
        // 如果没有当前周期，获取当前月份的数据
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
        endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        console.log('使用当前月份范围 - 开始:', startDate.toISOString(), '结束:', endDate.toISOString());
      }
      
      try {
        console.log('获取日历数据 - 发送请求:', {
          startDate: startDate.toISOString(),
          endDate: endDate.toISOString()
        });

        // 移除健康检查逻辑，直接请求数据
        const data = await calendarDataApi.getCalendarData(
          startDate.toISOString(),
          endDate.toISOString()
        );
        
        console.log('获取日历数据 - 响应数据:', data);
        setCalendarData(data);
        
        // 检查是否已达到26天
        if (data.current_cycle && data.current_cycle.valid_days_count >= 26 && !data.current_cycle.is_completed) {
          setCycleCompletedDialogOpen(true);
        }
        
        setError(null);
      } catch (err: any) {
        console.error('获取日历数据失败:', err);
        // 如果是404错误（未找到设置），不显示错误而是显示空日历
        if (axios.isAxiosError(err) && err.response?.status === 404) {
          // 创建符合CalendarResponse类型的空对象
          setCalendarData({
            days: [],
            current_cycle: null,
            valid_days_count: 0,
            valid_hours_count: 0
          });
          setError(null);
        } else if (axios.isAxiosError(err) && err.code === 'ERR_NETWORK') {
          // 处理网络错误
          setError('无法连接到服务器，请检查网络连接或API地址配置');
          console.error('网络错误详情:', err);
        } else {
          setError(`获取日历数据失败: ${err.message || '未知错误'}`);
        }
      }
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchCalendarData();
  }, [currentCycle]);
  
  // 处理日期点击
  const handleDayClick = (date: Date) => {
    console.log('点击日期:', date);
    
    // 如果没有设置周期，则提示用户先设置周期
    if (!currentCycle) {
      setSnackbarMessage('请先在【周期设置】中设置开始时间');
      setSnackbarOpen(true);
      return;
    }
    
    // 确保使用北京时间，避免UTC转换问题
    const localDate = new Date(
      date.getFullYear(),
      date.getMonth(),
      date.getDate(),
      12, 0, 0 // 使用中午12点，确保不会有时区问题
    );
    
    console.log('处理后的日期对象:', localDate);
    console.log('ISO字符串:', localDate.toISOString());
    
    // 使用标准格式YYYY-MM-DD表示日期部分
    const formattedDateStr = `${localDate.getFullYear()}-${String(localDate.getMonth() + 1).padStart(2, '0')}-${String(localDate.getDate()).padStart(2, '0')}`;
    console.log('日期部分(北京时间):', formattedDateStr);
    
    // 存储选择的日期
    setSelectedDate(localDate);
    
    // 查找对应的日期数据
    const dayData = calendarData?.days.find(day => {
      // 提取日期部分，忽略时间部分
      const dayDateStr = day.date.split('T')[0];
      console.log('比较日期 - 日历日期:', dayDateStr, '点击日期:', formattedDateStr);
      
      return dayDateStr === formattedDateStr;
    });
    
    // 检查是否已有跳过时间段
    if (dayData?.skip_period) {
      // 已有跳过时间段，设置编辑模式
      setDialogMode('edit');
      
      // 保存默认时间
      const defaultStartTime = dayData.skip_period.start_time || '08:00';
      const defaultEndTime = dayData.skip_period.end_time || '20:00';
      
      // 从后端获取该日期对应的跳过时间段
      if (currentCycle) {
        const getSkipPeriodForDate = async () => {
          try {
            const periods = await calendarDataApi.getSkipPeriods(currentCycle.id);
            console.log('获取到的跳过时间段:', periods);
            
            // 使用已格式化的日期字符串进行比较
            const matchingPeriod = periods.find(p => {
              // 提取时间段日期的日期部分
              const periodDateStr = p.date.split('T')[0];
              console.log('比较跳过时间段 - 时间段日期:', periodDateStr, '点击日期:', formattedDateStr);
              return periodDateStr === formattedDateStr;
            });
            
            if (matchingPeriod) {
              console.log('找到匹配的跳过时段:', matchingPeriod);
              setExistingSkipPeriod({
                id: matchingPeriod.id,
                date: matchingPeriod.date,
                start_time: matchingPeriod.start_time,
                end_time: matchingPeriod.end_time
              });
              setSkipStartTime(matchingPeriod.start_time);
              setSkipEndTime(matchingPeriod.end_time);
            } else {
              // 没有找到匹配的时间段，使用默认值
              setExistingSkipPeriod(null);
              setSkipStartTime(defaultStartTime);
              setSkipEndTime(defaultEndTime);
            }
            
            // 打开设置对话框
            setSkipDialogOpen(true);
          } catch (err) {
            console.error('获取跳过时间段失败:', err);
            // 使用默认值
            setExistingSkipPeriod(null);
            setSkipStartTime(defaultStartTime);
            setSkipEndTime(defaultEndTime);
            
            // 仍然打开对话框
            setSkipDialogOpen(true);
          }
        };
        
        getSkipPeriodForDate();
      } else {
        // 没有当前周期，使用默认值
        setExistingSkipPeriod(null);
        setSkipStartTime(defaultStartTime);
        setSkipEndTime(defaultEndTime);
        
        // 打开设置对话框
        setSkipDialogOpen(true);
      }
    } else {
      // 没有跳过时间段，设置创建模式
      setDialogMode('create');
      setExistingSkipPeriod(null);
      // 设置默认时间
      setSkipStartTime('08:00');
      setSkipEndTime('20:00');
      
      // 打开设置对话框
      setSkipDialogOpen(true);
    }
  };
  
  // 处理保存跳过时间段
  const handleSaveSkipPeriod = async () => {
    if (!currentCycle || !selectedDate) return;
    
    try {
      setSaveLoading(true);
      setError(null); // 重置错误状态
      
      console.log('保存跳过时间段 - 选择的日期:', selectedDate);
      console.log('保存跳过时间段 - 选择的日期时区信息:', selectedDate.toString());
      
      // 构建日期字符串的函数，确保格式一致且使用北京时间
      const formatDateString = (date: Date) => {
        // 注意：确保使用date对象的getFullYear、getMonth和getDate方法
        // 这些方法会返回本地时间的年、月、日
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
      };
      
      // 获取纯日期字符串，不带时间部分
      const dateStr = formatDateString(selectedDate);
      
      // 显式记录最终要发送的日期字符串
      const dateToSave = dateStr;
      
      console.log('保存跳过时间段 - 格式化后的日期字符串:', dateStr);
      console.log('保存跳过时间段 - 最终发送到后端的日期:', dateToSave);
      
      const skipPeriodData: SkipPeriodCreate = {
        cycle_id: currentCycle.id,
        date: dateToSave,
        start_time: skipStartTime,
        end_time: skipEndTime
      };
      
      console.log('保存跳过时间段 - 完整发送数据:', skipPeriodData);
      
      // 发送请求前再次检查时区问题
      console.log(`发送到后端的日期: ${dateToSave}`);
      console.log(`用户选择的实际日期: ${selectedDate.getFullYear()}-${selectedDate.getMonth()+1}-${selectedDate.getDate()}`);
      
      // 直接发送保存请求，不进行服务器连接测试
      const result = await calendarDataApi.setSkipPeriod(skipPeriodData);
      console.log('保存跳过时间段 - 成功结果:', result);
      
      // 关闭对话框
      setSkipDialogOpen(false);
      
      // 显示成功提示
      setSnackbarMessage(dialogMode === 'create' ? '跳过时间段设置成功' : '跳过时间段更新成功');
      setSnackbarOpen(true);
      
      // 重新获取当前周期数据（获取更新后的有效天数）
      if (onCycleUpdated) {
        onCycleUpdated();
      }
      
      // 重新获取日历数据以反映更改
      await fetchCalendarData();
      
      // 重置状态 - 在成功完成后再重置，而不是立即重置
      setTimeout(() => {
        setSelectedDate(null);
        setExistingSkipPeriod(null);
      }, 500);
      
    } catch (err) {
      console.error('保存跳过时间段失败:', err);
      // 根据错误类型设置不同的错误信息
      if (axios.isAxiosError(err)) {
        if (err.code === 'ERR_NETWORK') {
          setError('网络连接错误：无法连接到服务器，请确保后端服务正在运行');
        } else if (err.response) {
          // 服务器响应了，但状态码不是2xx
          setError(`服务器错误：${err.response.status} - ${err.response.data?.detail || err.message}`);
        } else if (err.request) {
          // 请求发出但没有收到响应
          setError('服务器没有响应，请检查网络连接并确保后端服务正在运行');
        } else {
          // 其他错误
          setError(`发送请求时出错：${err.message}`);
        }
      } else {
        // 非Axios错误
        setError(`保存跳过时间段失败：${err instanceof Error ? err.message : '未知错误'}`);
      }
      
      // 打开错误提示
      setSnackbarMessage(`保存失败：${err instanceof Error ? err.message : '未知错误'}`);
      setSnackbarOpen(true);
    } finally {
      setSaveLoading(false);
    }
  };

  // 处理删除跳过时间段
  const handleDeleteSkipPeriod = async () => {
    if (!existingSkipPeriod?.id) {
      setError('无法删除：没有找到有效的跳过时间段ID');
      return;
    }
    
    setSaveLoading(true);
    setError(null);
    
    try {
      const periodId = existingSkipPeriod.id;
      console.log(`尝试删除跳过时间段，ID: ${periodId}`);
      
      // 直接删除跳过时间段，不进行服务器连接测试
      const response = await calendarDataApi.deleteSkipPeriod(periodId);
      console.log('删除成功，响应:', response);
      
      // 关闭对话框
      setSkipDialogOpen(false);
      
      // 显示成功消息
      setSnackbarMessage(response.message || '跳过时间段已删除');
      setSnackbarOpen(true);
      
      // 刷新日历数据
      await fetchCalendarData();
      
      // 重置状态
      setSelectedDate(null);
      setExistingSkipPeriod(null);
      
    } catch (error) {
      console.error('删除跳过时间段失败:', error);
      if (axios.isAxiosError(error)) {
        if (error.code === 'ERR_NETWORK') {
          setError('网络连接错误：无法连接到服务器，请确保后端服务正在运行');
        } else if (error.response) {
          setError(`服务器错误：${error.response.status} - ${error.response.data?.detail || error.message}`);
        } else if (error.request) {
          setError('服务器没有响应，请检查网络连接并确保后端服务正在运行');
        } else {
          setError(`发送请求时出错：${error.message}`);
        }
      } else {
        setError(`删除跳过时间段失败：${error instanceof Error ? error.message : '未知错误'}`);
      }
      
      // 打开错误提示
      setSnackbarMessage(`删除失败：${error instanceof Error ? error.message : '未知错误'}`);
      setSnackbarOpen(true);
    } finally {
      setSaveLoading(false);
    }
  };
  
  // 处理周期完成
  const handleCycleCompleted = async () => {
    if (!currentCycle) return;
    
    try {
      // 调用API完成当前周期
      await cyclesApi.completeCycle(currentCycle.id);
      
      // 关闭对话框
      setCycleCompletedDialogOpen(false);
      
      // 通知父组件
      if (onCycleCompleted) {
        onCycleCompleted();
      }
      
      // 重新获取日历数据
      await fetchCalendarData();
      
      // 显示成功提示
      setSnackbarMessage('周期已完成，新周期已开始');
      setSnackbarOpen(true);
    } catch (err) {
      console.error('处理周期完成失败:', err);
      setError('处理周期完成失败，请重试');
    }
  };
  
  // 为日历准备事件
  const events: CalendarEvent[] = [];
  
  // 添加跳过时间段事件
  if (calendarData?.days) {
    console.log('准备渲染日历事件 - 所有日历数据：', calendarData.days);
    
    // 添加跳过时间段事件
    calendarData.days
      .filter(day => day.is_skipped && day.skip_period)
      .forEach(day => {
        // 提取日期部分（YYYY-MM-DD）
        const dateStr = day.date.split('T')[0];
        const [year, month, dayOfMonth] = dateStr.split('-').map(Number);
        
        // 创建日期对象，使用本地时间
        const date = new Date(year, month - 1, dayOfMonth);
        console.log('处理跳过时间段 - 日期:', {
          原始日期: day.date,
          日期字符串: dateStr,
          转换后日期: date.toISOString()
        });
        
        const skipPeriod = day.skip_period;
        if (skipPeriod) {
          // 解析时间
          const [startHour, startMinute] = skipPeriod.start_time.split(':').map(Number);
          const [endHour, endMinute] = skipPeriod.end_time.split(':').map(Number);
          
          // 创建事件的开始和结束时间
          const start = new Date(year, month - 1, dayOfMonth, startHour, startMinute);
          const end = new Date(year, month - 1, dayOfMonth, endHour, endMinute);
          
          console.log('跳过时间段事件:', {
            日期: dateStr,
            开始时间: start.toLocaleString(),
            结束时间: end.toLocaleString()
          });
          
          events.push({
            id: `skip-${dateStr}`,
            title: '跳过时段',
            start,
            end,
            allDay: false,
            resource: { 
              isSkipped: true,
              isStartDay: false
            }
          });
        }
      });
  }
  
  // 添加周期开始日期事件
  if (currentCycle) {
    // 解析周期开始日期
    const cycleStartStr = currentCycle.start_date.split('T')[0];
    const [year, month, day] = cycleStartStr.split('-').map(Number);
    const timeStr = currentCycle.start_date.split('T')[1].split('.')[0];
    const [hour, minute] = timeStr.split(':').map(Number);
    
    // 创建开始日期事件
    const startDate = new Date(year, month - 1, day, hour, minute);
    console.log('周期开始事件:', {
      原始日期: currentCycle.start_date,
      解析后日期: startDate.toLocaleString()
    });
    
    events.push({
      id: `start-${cycleStartStr}`,
      title: '周期开始',
      start: startDate,
      end: new Date(startDate.getTime() + 60 * 60 * 1000), // 1小时
      allDay: false,
      resource: { 
        isSkipped: false,
        isStartDay: true
      }
    });
  }
  
  console.log('最终生成的事件列表:', events);
  
  // 自定义事件样式
  const eventStyleGetter = (event: CalendarEvent) => {
    const isSkipped = event.resource?.isSkipped;
    const isStartDay = event.resource?.isStartDay;
    
    if (isStartDay) {
      return {
        style: {
          backgroundColor: '#43a047', // 更鲜明的绿色
          borderRadius: '3px',
          opacity: 1,
          color: 'white',
          border: '1px solid #2e7d32',
          display: 'block',
          fontWeight: 'bold',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
          padding: '2px 4px'
        }
      };
    }
    
    if (isSkipped) {
      return {
        style: {
          backgroundColor: '#fb8c00', // 更鲜明的橙色
          borderRadius: '3px',
          opacity: 1,
          color: 'white',
          border: '1px solid #ef6c00',
          display: 'block',
          fontWeight: 'bold',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
          padding: '2px 4px'
        }
      };
    }
    
    return {
      style: {
        backgroundColor: '#1976d2',
        borderRadius: '3px',
        opacity: 1,
        color: 'white',
        border: '1px solid #1565c0',
        display: 'block',
        fontWeight: 'bold',
        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
        padding: '2px 4px'
      }
    };
  };
  
  // 自定义日期单元格
  const dayPropGetter = (date: Date) => {
    // 将日期转换为YYYY-MM-DD格式进行比较
    const formatDate = (d: Date) => {
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    };
    
    const currentDateStr = formatDate(date);
    
    // 查找对应的日期数据
    const dayData = calendarData?.days.find(day => {
      const dayDateStr = day.date.split('T')[0];
      return dayDateStr === currentDateStr;
    });
    
    // 检查是否是周期开始日
    if (currentCycle) {
      const cycleStartStr = currentCycle.start_date.split('T')[0];
      if (cycleStartStr === currentDateStr) {
        return {
          className: 'start-day', // 应用到单元格的类
          style: {
            cursor: 'pointer'
          }
        };
      }
    }
    
    // 跳过的日期只有在已经设置了跳过时间段后才显示背景色
    if (dayData?.is_skipped && dayData.skip_period) {
      return {
        className: 'skipped-day', // 应用到单元格的类
        style: {
          cursor: 'pointer'
        }
      };
    }
    
    // 是否是当天
    const isToday = (
      date.getDate() === new Date().getDate() &&
      date.getMonth() === new Date().getMonth() &&
      date.getFullYear() === new Date().getFullYear()
    );
    
    if (isToday) {
      return {
        className: 'today', // 应用到单元格的类
        style: {
          cursor: 'pointer'
        }
      };
    }
    
    return {
      style: {
        cursor: 'pointer'
      }
    };
  };
  
  // 处理对话框关闭
  const handleDialogClose = () => {
    // 关闭对话框
    setSkipDialogOpen(false);
  };
  
  // 格式化显示小时数为天+小时格式
  const formatHoursAsDaysAndHours = (hours: number): string => {
    const days = Math.floor(hours / 24);
    const remainingHours = Math.floor(hours % 24);
    
    if (days > 0) {
      return `${days}天${remainingHours}小时`;
    } else {
      return `${remainingHours}小时`;
    }
  };
  
  // 计算还需要多少时间到达26天
  const calculateRemainingTime = (currentHours: number): string => {
    const targetHours = 26 * 24; // 26天的小时数
    const remainingHours = Math.max(0, targetHours - currentHours);
    
    const days = Math.floor(remainingHours / 24);
    const hours = Math.floor(remainingHours % 24);
    
    if (days > 0) {
      return `还需${days}天${hours}小时`;
    } else if (hours > 0) {
      return `还需${hours}小时`;
    } else {
      return "已达成目标";
    }
  };
  
  // 添加导航处理函数
  const handleNavigate = (newDate: Date) => {
    console.log('导航到新日期:', newDate);
    setViewDate(newDate);
    
    // 获取新日期的月份范围
    const startDate = new Date(newDate.getFullYear(), newDate.getMonth(), 1);
    const endDate = new Date(newDate.getFullYear(), newDate.getMonth() + 1, 0);
    
    // 重新获取选定月份的日历数据
    setLoading(true);
    calendarDataApi.getCalendarData(
      startDate.toISOString(),
      endDate.toISOString()
    )
    .then(data => {
      console.log('获取新月份日历数据成功:', data);
      setCalendarData(data);
      setError(null);
    })
    .catch(err => {
      console.error('获取新月份日历数据失败:', err);
      setError(`获取日历数据失败: ${err.message || '未知错误'}`);
    })
    .finally(() => {
      setLoading(false);
    });
  };
  
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }
  
  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }
  
  // 提取当前周期的跳过时间段
  const currentSkipPeriods = calendarData?.days
    .filter(day => day.is_skipped && day.skip_period)
    .map(day => ({
      date: day.date,
      startTime: day.skip_period?.start_time || '',
      endTime: day.skip_period?.end_time || '',
      id: day.skip_period_id
    })) || [];
  
  return (
    <>
      <Paper elevation={3} sx={{ p: { xs: 1, sm: 3 }, mb: 3 }}>
        {/* 当前周期信息显示 */}
        {currentCycle ? (
          <Box mb={3}>
            <Typography variant="h6" component="div">
              当前周期: #{currentCycle.cycle_number}
            </Typography>
            <Box display="flex" flexDirection={{ xs: 'column', sm: 'row' }} gap={1} mt={1}>
              <Typography variant="body1">
                开始时间: {new Date(currentCycle.start_date).toLocaleString('zh-CN')}
              </Typography>
              <Typography variant="body1" ml={{ xs: 0, sm: 2 }}>
                有效天数: {currentCycle.valid_days_count}/26 天
              </Typography>
              <Typography variant="body1" ml={{ xs: 0, sm: 2 }}>
                有效小时数: {formatHoursAsDaysAndHours(currentCycle.valid_hours_count)}
              </Typography>
              <Typography variant="body1" ml={{ xs: 0, sm: 2 }}>
                距离26天还剩: {calculateRemainingTime(currentCycle.valid_hours_count)}
              </Typography>
            </Box>
            
            {/* 当前周期的跳过时间段列表 */}
            {currentSkipPeriods.length > 0 && (
              <Box mt={2}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  已设置的跳过时间段:
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={1}>
                  {currentSkipPeriods.map((period, index) => (
                    <Box 
                      key={index} 
                      sx={{ 
                        p: 1, 
                        borderRadius: 1, 
                        bgcolor: '#fff8e1', 
                        border: '1px solid #ffecb3',
                        fontSize: '0.875rem'
                      }}
                    >
                      {new Date(period.date).toLocaleDateString('zh-CN')} {period.startTime}-{period.endTime}
                    </Box>
                  ))}
                </Box>
              </Box>
            )}
          </Box>
        ) : (
          <Alert severity="info" sx={{ mb: 3 }}>
            尚未设置周期。请先在设置选项卡中设置开始时间。
          </Alert>
        )}
      </Paper>
      
      <Paper 
        elevation={3} 
        sx={{ 
          p: 3, 
          height: 'auto',  // 改为自适应高度
          width: '100%',   // 确保宽度
          mb: 4,           // 增加底部边距
          overflowX: 'auto'  // 允许水平滚动
        }}
      >
        <Box 
          sx={{ 
            height: {
              xs: '65vh', // 移动设备上较小的高度
              sm: '65vh', // 平板上的高度
              md: '65vh'  // 桌面上的高度
            }, 
            width: '100%',
            '& .rbc-calendar': {
              border: '1px solid #e0e0e0',
              borderRadius: '4px',
            },
            '& .rbc-month-view': {
              border: '1px solid #e0e0e0',
            },
            '& .rbc-header': {
              fontWeight: 'bold',
              padding: '4px 0',
              borderBottom: '1px solid #e0e0e0',
            },
            '& .rbc-day-bg': {
              border: '1px solid #e0e0e0',
            },
            '& .rbc-month-row + .rbc-month-row': {
              borderTop: '1px solid #e0e0e0',
            },
            '& .rbc-date-cell': {
              padding: '2px 4px',
              fontSize: '14px',
              fontWeight: 'normal',
            },
            '& .rbc-day-bg + .rbc-day-bg': {
              borderLeft: '1px solid #e0e0e0', // 添加竖线分隔符
            },
            '& .rbc-toolbar': {
              marginBottom: '8px',
            },
            '& .rbc-toolbar button': {
              padding: '4px 8px',
              fontSize: '14px',
            },
            '& .start-day .rbc-date-cell': {
              color: '#2e7d32',
              fontWeight: 'bold',
            },
            '& .skipped-day .rbc-date-cell': {
              color: '#ef6c00',
              fontWeight: 'bold',
            },
            '& .today .rbc-date-cell': {
              color: '#1565c0',
              fontWeight: 'bold',
            },
            '& .start-day.rbc-day-bg': {
              backgroundColor: '#e8f5e9 !important', // 浅绿色背景
              border: '2px solid #4caf50 !important',
            },
            '& .skipped-day.rbc-day-bg': {
              backgroundColor: '#fff3e0 !important', // 浅橙色背景
              border: '2px solid #ff9800 !important',
            },
            '& .today.rbc-day-bg': {
              backgroundColor: '#e3f2fd !important', // 浅蓝色背景
              border: '2px solid #2196f3 !important',
            },
            '& .rbc-selected-cell': {
              backgroundColor: 'rgba(66, 165, 245, 0.2) !important',
            },
            '& .rbc-event': {
              borderRadius: '3px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
              padding: '2px 5px',
            },
            '& .rbc-off-range': {
              opacity: 0.5,
            }
          }}
        >
          <BigCalendar
            localizer={localizer}
            events={events}
            startAccessor={(event: CalendarEvent) => event.start}
            endAccessor={(event: CalendarEvent) => event.end}
            style={{ height: '100%', width: '100%' }}
            onSelectSlot={(slotInfo) => handleDayClick(slotInfo.start)}
            selectable
            eventPropGetter={eventStyleGetter}
            dayPropGetter={dayPropGetter}
            views={['month']}
            defaultView="month"
            date={viewDate}
            onNavigate={handleNavigate}
            messages={{
              today: '今天',
              previous: '上一月',
              next: '下一月',
              month: '月',
              agenda: '议程'
            }}
            components={{
              dateCellWrapper: (props) => {
                // 自定义日期单元格，添加触摸事件支持
                const { children, value } = props;
                return (
                  <div 
                    onClick={() => handleDayClick(value)}
                    onTouchStart={() => handleDayClick(value)}
                    style={{ height: '100%', width: '100%' }}
                  >
                    {children}
                  </div>
                );
              }
            }}
          />
        </Box>
      </Paper>
      
      {/* 跳过时间段设置对话框 */}
      <Dialog 
        open={skipDialogOpen} 
        onClose={handleDialogClose}
        fullScreen={isMobile}
        PaperProps={{
          sx: {
            width: isMobile ? '100%' : 'auto',
            maxWidth: isMobile ? '100%' : '500px',
            borderRadius: isMobile ? 0 : '8px',
            m: isMobile ? 0 : 2
          }
        }}
      >
        <DialogTitle sx={{ fontSize: isMobile ? '18px' : '16px', py: isMobile ? 2 : 1.5 }}>
          {dialogMode === 'create' ? '设置跳过时间段' : dialogMode === 'edit' ? '编辑跳过时间段' : '删除跳过时间段'}
        </DialogTitle>
        <DialogContent sx={{ pt: isMobile ? 2 : 1 }}>
          <Typography gutterBottom sx={{ fontSize: isMobile ? '16px' : '14px' }}>
            日期: {selectedDate?.toLocaleDateString('zh-CN') || ''}
          </Typography>
          
          <Box mt={2}>
            <TextField
              label="开始时间"
              type="time"
              value={skipStartTime}
              onChange={(e) => setSkipStartTime(e.target.value)}
              InputLabelProps={{ shrink: true }}
              fullWidth
              margin="normal"
              disabled={saveLoading}
              sx={{ '& input': { fontSize: isMobile ? '16px' : '14px' } }}
            />
            
            <TextField
              label="结束时间"
              type="time"
              value={skipEndTime}
              onChange={(e) => setSkipEndTime(e.target.value)}
              InputLabelProps={{ shrink: true }}
              fullWidth
              margin="normal"
              disabled={saveLoading}
              sx={{ '& input': { fontSize: isMobile ? '16px' : '14px' } }}
            />
          </Box>
          
          {saveLoading && (
            <Box display="flex" justifyContent="center" mt={2}>
              <CircularProgress size={24} />
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ px: isMobile ? 3 : 2, pb: isMobile ? 3 : 2 }}>
          <Button 
            onClick={handleDialogClose} 
            disabled={saveLoading}
            sx={{ fontSize: isMobile ? '16px' : '14px', py: isMobile ? 1 : 0.5 }}
            onTouchStart={handleDialogClose}
          >
            取消
          </Button>
          
          {existingSkipPeriod && (
            <Button 
              onClick={handleDeleteSkipPeriod} 
              onTouchStart={handleDeleteSkipPeriod}
              variant="outlined" 
              color="error"
              disabled={saveLoading}
              startIcon={saveLoading ? <CircularProgress size={16} /> : null}
              sx={{ fontSize: isMobile ? '16px' : '14px', py: isMobile ? 1 : 0.5 }}
            >
              {saveLoading ? '处理中...' : '删除'}
            </Button>
          )}
          
          <Button 
            onClick={handleSaveSkipPeriod}
            onTouchStart={handleSaveSkipPeriod}
            variant="contained" 
            color="primary"
            disabled={saveLoading}
            startIcon={saveLoading ? <CircularProgress size={16} /> : null}
            sx={{ fontSize: isMobile ? '16px' : '14px', py: isMobile ? 1 : 0.5 }}
          >
            {saveLoading ? '保存中...' : existingSkipPeriod ? '更新' : '保存'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 周期完成对话框 */}
      <Dialog
        open={cycleCompletedDialogOpen}
        onClose={() => setCycleCompletedDialogOpen(false)}
        fullScreen={isMobile}
        PaperProps={{
          sx: {
            width: isMobile ? '100%' : 'auto',
            maxWidth: isMobile ? '100%' : '500px',
            borderRadius: isMobile ? 0 : '8px'
          }
        }}
      >
        <DialogTitle sx={{ fontSize: isMobile ? '18px' : '16px' }}>周期已完成</DialogTitle>
        <DialogContent>
          <Typography sx={{ fontSize: isMobile ? '16px' : '14px' }}>
            恭喜您！当前26天周期已完成。是否开始新的周期？
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: isMobile ? 3 : 2, pb: isMobile ? 3 : 2 }}>
          <Button 
            onClick={() => setCycleCompletedDialogOpen(false)}
            onTouchStart={() => setCycleCompletedDialogOpen(false)}
            sx={{ fontSize: isMobile ? '16px' : '14px', py: isMobile ? 1 : 0.5 }}
          >
            取消
          </Button>
          <Button 
            onClick={handleCycleCompleted}
            onTouchStart={handleCycleCompleted} 
            variant="contained" 
            color="primary"
            sx={{ fontSize: isMobile ? '16px' : '14px', py: isMobile ? 1 : 0.5 }}
          >
            开始新周期
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 成功提示 */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        sx={{ 
          '& .MuiSnackbarContent-root': { 
            fontSize: isMobile ? '16px' : '14px',
            minWidth: isMobile ? '90%' : 'auto' 
          } 
        }}
      />
    </>
  );
};

export default Calendar; 