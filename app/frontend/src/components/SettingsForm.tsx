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
  Divider
} from '@mui/material';
import { CalendarSettings, CalendarSettingsCreate } from '../models/types';
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
  
  // 检查是否已有设置
  useEffect(() => {
    const checkExistingSettings = async () => {
      try {
        const settings = await calendarSettingsApi.getSettings();
        setExistingSettings(true);
        setCurrentSettings(settings);
        
        // 提取日期和时间用于编辑模式
        const settingsDate = new Date(settings.start_date);
        setDate(settingsDate.toISOString().split('T')[0]);
        
        // 格式化时间为HH:MM
        const hours = settingsDate.getHours().toString().padStart(2, '0');
        const minutes = settingsDate.getMinutes().toString().padStart(2, '0');
        setTime(`${hours}:${minutes}`);
      } catch (err) {
        // 没有找到设置，允许用户创建
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
                当前开始时间: {new Date(currentSettings.start_date).toLocaleString('zh-CN')}
              </Typography>
            </Box>
          )}
          
          <Box display="flex" gap={2}>
            <Button 
              variant="contained" 
              color="primary"
              onClick={() => setEditMode(true)}
              sx={{ flex: 1 }}
            >
              修改开始时间
            </Button>
            
            <Button 
              variant="outlined" 
              color="error"
              onClick={handleResetDialogOpen}
              sx={{ flex: 1 }}
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
          
          <Typography variant="h6" gutterBottom>
            创建自定义开始时间的周期
          </Typography>
          
          {cycleError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {cycleError}
            </Alert>
          )}
          
          {cycleSuccess && (
            <Alert severity="success" sx={{ mb: 2 }}>
              周期已成功创建
            </Alert>
          )}
          
          <Box component="form" onSubmit={handleCreateCycle}>
            <Box display="flex" flexDirection={{ xs: 'column', sm: 'row' }} gap={2} mb={2}>
              <TextField
                label="周期开始日期"
                type="date"
                value={cycleDate}
                onChange={(e) => setCycleDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
                fullWidth
                required
              />
              
              <TextField
                label="周期开始时间"
                type="time"
                value={cycleTime}
                onChange={(e) => setCycleTime(e.target.value)}
                InputLabelProps={{ shrink: true }}
                fullWidth
                required
              />
            </Box>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              您可以为每个周期设置不同的开始时间，系统会使用这个时间作为新周期的起点。
            </Typography>
            
            <Button 
              type="submit" 
              variant="contained" 
              color="secondary" 
              fullWidth
            >
              创建新周期
            </Button>
          </Box>
        </>
      )}
      
      {/* 重置日历确认对话框 */}
      <Dialog
        open={resetDialogOpen}
        onClose={handleResetDialogClose}
      >
        <DialogTitle>确定要重置日历？</DialogTitle>
        <DialogContent>
          <DialogContentText>
            重置日历将删除所有现有的日历数据，包括当前周期和历史记录。此操作不可撤销。
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleResetDialogClose}>取消</Button>
          <Button onClick={handleResetCalendar} color="error" variant="contained">
            确认重置
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default SettingsForm;