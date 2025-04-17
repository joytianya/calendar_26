import React, { useState, useEffect } from 'react';
import { 
  TextField, 
  Button, 
  Box, 
  Typography, 
  Paper,
  Alert,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress
} from '@mui/material';
import { CalendarSettings, CalendarSettingsCreate, CycleRecord } from '../models/types';
import { calendarSettingsApi, cyclesApi } from '../services/api';

interface SettingsFormProps {
  onSettingsSaved: () => void;
}

const SettingsForm: React.FC<SettingsFormProps> = ({ onSettingsSaved }) => {
  const [date, setDate] = useState<string>('');
  const [time, setTime] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const [existingSettings, setExistingSettings] = useState<boolean>(false);
  const [currentSettings, setCurrentSettings] = useState<CalendarSettings | null>(null);
  const [resetDialogOpen, setResetDialogOpen] = useState<boolean>(false);
  const [editMode, setEditMode] = useState<boolean>(false);
  
  // 自定义周期创建的状态
  const [cycleDate, setCycleDate] = useState<string>('');
  const [cycleTime, setCycleTime] = useState<string>('');
  const [cycleError, setCycleError] = useState<string | null>(null);
  const [cycleSuccess, setCycleSuccess] = useState<boolean>(false);
  
  // 添加周期历史记录的状态
  const [cycles, setCycles] = useState<CycleRecord[]>([]);
  const [cyclesLoading, setCyclesLoading] = useState<boolean>(false);
  const [cyclesError, setCyclesError] = useState<string | null>(null);
  
  // 获取所有周期记录
  const fetchCycles = async () => {
    try {
      setCyclesLoading(true);
      setCyclesError(null);
      console.log('开始获取所有周期记录...');
      const data = await cyclesApi.getAllCycles();
      console.log('成功获取周期记录:', data);
      
      // 确保数据是有序的 - 按周期号排序，最新的在前面
      const sortedData = [...data].sort((a, b) => b.cycle_number - a.cycle_number);
      console.log('排序后的周期记录:', sortedData);
      setCycles(sortedData);
    } catch (err) {
      console.error('获取周期历史记录失败:', err);
      setCyclesError('获取周期历史记录失败');
    } finally {
      setCyclesLoading(false);
    }
  };
  
  // 检查是否已有设置
  useEffect(() => {
    const checkExistingSettings = async () => {
      try {
        console.log('正在检查日历设置...');
        const settings = await calendarSettingsApi.getSettings();
        console.log('成功获取日历设置:', settings);
        setExistingSettings(true);
        setCurrentSettings(settings);
        
        // 提取日期和时间用于编辑模式
        const settingsDate = new Date(settings.start_date);
        setDate(settingsDate.toISOString().split('T')[0]);
        
        // 格式化时间为HH:MM
        const hours = settingsDate.getHours().toString().padStart(2, '0');
        const minutes = settingsDate.getMinutes().toString().padStart(2, '0');
        setTime(`${hours}:${minutes}`);
        
        // 获取周期记录
        fetchCycles();
      } catch (err) {
        // 没有找到设置，允许用户创建
        console.log('未找到日历设置:', err);
        setExistingSettings(false);
        setCurrentSettings(null);
      }
    };
    
    checkExistingSettings();
  }, []);
  
  // 处理表单提交
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // 验证输入
      if (!date) {
        setError('请选择开始日期');
        return;
      }
      
      if (!time) {
        setError('请选择开始时间');
        return;
      }
      
      // 构建日期时间字符串，格式为：YYYY-MM-DDTHH:MM:SS
      const dateTimeStr = `${date}T${time}:00`;
      
      // 创建设置对象
      const settings: CalendarSettingsCreate = {
        start_date: dateTimeStr,
        skip_hours: 12 // 默认跳过12小时
      };
      
      // 保存设置
      await calendarSettingsApi.createSettings(settings);
      
      setSuccess(true);
      setError(null);
      setExistingSettings(true);
      setEditMode(false);
      
      // 通知父组件设置已保存
      onSettingsSaved();
      
      // 3秒后清除成功消息
      setTimeout(() => {
        setSuccess(false);
      }, 3000);
      
    } catch (err) {
      console.error('保存设置失败:', err);
      setError('保存设置失败，请重试');
      setSuccess(false);
    }
  };
  
  // 处理重置日历对话框
  const handleResetDialogOpen = () => {
    setResetDialogOpen(true);
  };
  
  const handleResetDialogClose = () => {
    setResetDialogOpen(false);
  };
  
  // 处理重置日历
  const handleResetCalendar = async () => {
    try {
      // 调用API重置日历
      await calendarSettingsApi.resetCalendar();
      
      setResetDialogOpen(false);
      setExistingSettings(false);
      setCurrentSettings(null);
      setEditMode(false);
      
      // 通知父组件设置已重置
      onSettingsSaved();
      
      setSuccess(true);
      setError(null);
      
      // 3秒后清除成功消息
      setTimeout(() => {
        setSuccess(false);
      }, 3000);
    } catch (err) {
      console.error('重置日历失败:', err);
      setError('重置日历失败，请重试');
      setResetDialogOpen(false);
    }
  };
  
  // 处理创建自定义周期
  const handleCreateCycle = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // 验证输入
      if (!cycleDate) {
        setCycleError('请选择周期开始日期');
        return;
      }
      
      if (!cycleTime) {
        setCycleError('请选择周期开始时间');
        return;
      }
      
      // 构建日期时间字符串，格式为：YYYY-MM-DDTHH:MM:SS
      const dateTimeStr = `${cycleDate}T${cycleTime}:00`;
      
      // 创建新周期
      await cyclesApi.createCycle({ start_date: dateTimeStr });
      
      setCycleSuccess(true);
      setCycleError(null);
      
      // 重新获取周期列表
      fetchCycles();
      
      // 通知父组件周期已创建
      onSettingsSaved();
      
      // 清空表单
      setCycleDate('');
      setCycleTime('');
      
      // 3秒后清除成功消息
      setTimeout(() => {
        setCycleSuccess(false);
      }, 3000);
      
    } catch (err: any) {
      console.error('创建周期失败:', err);
      setCycleError(err.response?.data?.detail || '创建周期失败，请重试');
      setCycleSuccess(false);
    }
  };
  
  // 格式化日期部分（仅年月日）
  const formatDatePart = (dateStr: string | null): string => {
    if (!dateStr) return '进行中';
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  };
  
  // 格式化时间部分（仅时分）
  const formatTimePart = (dateStr: string | null): string => {
    if (!dateStr) return '--:--';
    const date = new Date(dateStr);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
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
  
  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        周期设置
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {editMode ? "设置已更新" : existingSettings ? "重置成功" : "设置已保存"}
        </Alert>
      )}
      
      {existingSettings && !editMode ? (
        <Box>
          <Alert severity="info" sx={{ mb: 2 }}>
            您已经设置过开始时间。在日历上点击日期可以设置跳过时间段。
          </Alert>
          
          {currentSettings && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="body1">
                当前开始时间: {cycles.length > 0 
                  ? new Date(cycles[0].start_date).toLocaleString('zh-CN') 
                  : new Date(currentSettings.start_date).toLocaleString('zh-CN')}
              </Typography>
            </Box>
          )}
          
          <Box display="flex" gap={2} flexDirection={{ xs: 'column', sm: 'row' }}>
            <Button 
              variant="contained" 
              color="primary"
              onClick={() => setEditMode(true)}
              sx={{ flex: 1, mb: { xs: 1, sm: 0 }, fontSize: { xs: '16px', sm: '14px' }, py: { xs: 1.5, sm: 1 } }}
              onTouchStart={() => setEditMode(true)}
            >
              修改开始时间
            </Button>
            
            <Button 
              variant="outlined" 
              color="error"
              onClick={handleResetDialogOpen}
              sx={{ flex: 1, fontSize: { xs: '16px', sm: '14px' }, py: { xs: 1.5, sm: 1 } }}
              onTouchStart={handleResetDialogOpen}
            >
              重置日历
            </Button>
          </Box>
        </Box>
      ) : (
        <Box component="form" onSubmit={handleSubmit}>
          <Box display="flex" flexDirection={{ xs: 'column', sm: 'row' }} gap={2} mb={2}>
            <TextField
              label="开始日期"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              fullWidth
              required
            />
            
            <TextField
              label="开始时间"
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              InputLabelProps={{ shrink: true }}
              fullWidth
              required
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            设置开始时间后，您可以在日历上点击日期来设置具体的跳过时间段。
          </Typography>
          
          <Box display="flex" gap={2}>
            <Button 
              type="submit" 
              variant="contained" 
              color="primary" 
              fullWidth
            >
              {editMode ? "更新设置" : "保存设置"}
            </Button>
            
            {editMode && (
              <Button 
                variant="outlined"
                onClick={() => setEditMode(false)}
                fullWidth
              >
                取消
              </Button>
            )}
          </Box>
        </Box>
      )}
      
      {/* 添加创建自定义周期部分 */}
      {existingSettings && (
        <>
          <Divider sx={{ my: 4 }} />
          
          {/* 显示所有周期的开始和结束时间 */}
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              当前周期记录
            </Typography>
            <Button 
              variant="outlined" 
              size="small"
              onClick={fetchCycles}
              onTouchStart={fetchCycles}
            >
              刷新数据
            </Button>
          </Box>
          
          {cyclesError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {cyclesError}
            </Alert>
          )}
          
          {cyclesLoading && (
            <Box display="flex" justifyContent="center" my={3}>
              <CircularProgress />
            </Box>
          )}
          
          {!cyclesLoading && cycles.length === 0 && (
            <Alert severity="info" sx={{ mb: 2 }}>
              暂无周期记录
            </Alert>
          )}
          
          {!cyclesLoading && cycles.length > 0 && (
            <Box sx={{ mt: 2, p: 2, border: '1px solid #e0e0e0', borderRadius: 1, bgcolor: '#fafafa' }}>
              <Box mb={1}>
                <Typography variant="subtitle1" fontWeight="bold">
                  周期 #{cycles[0].cycle_number}
                </Typography>
              </Box>
              <Box display="flex" flexDirection="column" gap={1}>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">开始日期时间:</Typography>
                  <Typography variant="body2" fontWeight="medium">
                    {formatDatePart(cycles[0].start_date)} {formatTimePart(cycles[0].start_date)}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">结束日期时间:</Typography>
                  <Typography variant="body2" fontWeight="medium">
                    {cycles[0].end_date ? `${formatDatePart(cycles[0].end_date)} ${formatTimePart(cycles[0].end_date)}` : '进行中'}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">有效天数:</Typography>
                  <Typography variant="body2" fontWeight="medium">
                    {cycles[0].valid_days_count}/26 天
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">有效小时数:</Typography>
                  <Typography variant="body2" fontWeight="medium">
                    {formatHoursAsDaysAndHours(cycles[0].valid_hours_count)}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">距离26天还剩:</Typography>
                  <Typography variant="body2" fontWeight="medium">
                    {calculateRemainingTime(cycles[0].valid_hours_count)}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">状态:</Typography>
                  <Typography 
                    variant="body2" 
                    fontWeight="medium" 
                    color={cycles[0].is_completed ? 'success.main' : 'primary.main'}
                  >
                    {cycles[0].is_completed ? '已完成' : '进行中'}
                  </Typography>
                </Box>
              </Box>
            </Box>
          )}
        </>
      )}
      
      {/* 重置日历确认对话框 */}
      <Dialog
        open={resetDialogOpen}
        onClose={handleResetDialogClose}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
        sx={{ 
          '& .MuiDialog-paper': { 
            width: { xs: '90%', sm: '400px' },
            p: { xs: 1, sm: 2 }
          }
        }}
      >
        <DialogTitle id="alert-dialog-title" sx={{ fontSize: { xs: '18px', sm: '20px' } }}>
          确认重置日历？
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="alert-dialog-description" sx={{ fontSize: { xs: '16px', sm: '14px' } }}>
            此操作将删除所有日历设置、周期记录和跳过时间段。此操作不可恢复，确定要继续吗？
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button 
            onClick={handleResetDialogClose} 
            color="primary"
            sx={{ fontSize: { xs: '16px', sm: '14px' }, py: { xs: 1, sm: 0.5 } }}
            onTouchStart={handleResetDialogClose}
          >
            取消
          </Button>
          <Button 
            onClick={handleResetCalendar} 
            color="error" 
            variant="contained"
            autoFocus
            sx={{ fontSize: { xs: '16px', sm: '14px' }, py: { xs: 1, sm: 0.5 } }}
            onTouchStart={handleResetCalendar}
          >
            确认重置
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default SettingsForm;