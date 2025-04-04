import React, { useState, useEffect } from 'react';
import { Container, Box, Typography, Tab, Tabs, Alert, Dialog, DialogContent, DialogActions, Button, Snackbar, Paper } from '@mui/material';
import Calendar from '../components/Calendar';
import SettingsForm from '../components/SettingsForm';
import CycleHistory from '../components/CycleHistory';
import { calendarSettingsApi, cyclesApi, calendarDataApi } from '../services/api';
import { CycleRecord } from '../models/types';

// 选项卡接口
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

// 选项卡面板组件
const TabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      {...other}
      style={{ width: '100%' }}
    >
      {value === index && <Box sx={{ py: 3, width: '100%' }}>{children}</Box>}
    </div>
  );
};

const HomePage: React.FC = () => {
  const [tabValue, setTabValue] = useState<number>(0);
  const [currentCycle, setCurrentCycle] = useState<CycleRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showSettingsError, setShowSettingsError] = useState<boolean>(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState<boolean>(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [cycleComplete, setCycleComplete] = useState<boolean>(false);
  
  // 获取设置和当前周期
  const fetchInitialData = async () => {
    try {
      // 获取设置
      await calendarSettingsApi.getSettings();
      setShowSettingsError(false);
      
      // 获取当前周期
      try {
        const cycleData = await cyclesApi.getCurrentCycle();
        console.log('获取到当前周期数据:', cycleData);
        setCurrentCycle(cycleData);
        setError(null);
      } catch (err: any) {
        console.error('获取当前周期失败:', err);
        // 如果是404错误，可能是没有当前周期，这是正常情况
        if (err.response?.status === 404) {
          setCurrentCycle(null);
          setShowSettingsError(true);
        } else {
          setError('获取数据失败，请检查网络连接并重试');
        }
      }
    } catch (err: any) {
      console.log('未找到设置，需要创建', err);
      setShowSettingsError(true);
      setCurrentCycle(null);
    }
  };
  
  // 第一次加载时获取数据
  useEffect(() => {
    console.log('HomePage组件挂载，开始获取数据');
    fetchInitialData();
  }, []);
  
  // 处理选项卡切换
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  // 处理设置保存
  const handleSettingsSaved = () => {
    fetchInitialData();
    // 保存设置后切换到日历选项卡
    setTabValue(0);
  };
  
  // 处理日期点击
  const handleDayClick = (day: Date) => {
    // 保存选择的日期
    setSelectedDate(day);
    
    // 打开确认对话框
    setConfirmDialogOpen(true);
  };
  
  // 处理确认有效天数
  const handleConfirmValidDay = async () => {
    try {
      const response = await calendarDataApi.incrementValidDay();
      
      // 刷新当前周期
      try {
        const cycleData = await cyclesApi.getCurrentCycle();
        setCurrentCycle(cycleData);
        
        // 检查是否周期完成
        if (response.valid_days_count >= 26) {
          setCycleComplete(true);
        }
      } catch (err) {
        // 如果获取当前周期失败，可能是因为刚刚完成了一个周期并创建了新周期
        fetchInitialData();
      }
      
      setConfirmDialogOpen(false);
    } catch (err) {
      console.error('增加有效天数失败:', err);
      setError('增加有效天数失败，请重试');
    }
  };
  
  // 处理周期完成回调
  const handleCycleCompleted = () => {
    // 刷新数据获取新周期
    fetchInitialData();
    setCycleComplete(true);
  };
  
  // 处理周期更新回调
  const handleCycleUpdated = () => {
    // 刷新当前周期数据
    fetchInitialData();
  };
  
  return (
    <Container maxWidth="lg" sx={{ py: 4, display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        26天周期日历系统
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2, width: '100%' }}>
          {error}
        </Alert>
      )}
      
      {showSettingsError && (
        <Alert severity="warning" sx={{ mb: 2, width: '100%' }}>
          请先设置日历起始时间和跳过规则
        </Alert>
      )}
      
      <Paper elevation={2} sx={{ width: '100%', mb: 3, overflow: 'hidden' }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          variant="fullWidth"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="日历" />
          <Tab label="设置" />
          <Tab label="历史记录" />
        </Tabs>
      </Paper>
      
      <Box sx={{ width: '100%' }}>
        <TabPanel value={tabValue} index={0}>
          {currentCycle ? (
            <Calendar 
              onDayClick={handleDayClick}
              currentCycle={currentCycle}
              onCycleCompleted={handleCycleCompleted}
              onCycleUpdated={handleCycleUpdated}
            />
          ) : (
            <Paper elevation={3} sx={{ p: 3, textAlign: 'center' }}>
              <Typography>
                未找到当前周期，请先完成设置
              </Typography>
            </Paper>
          )}
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <SettingsForm onSettingsSaved={handleSettingsSaved} />
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          <CycleHistory />
        </TabPanel>
      </Box>
      
      {/* 确认对话框 */}
      <Dialog open={confirmDialogOpen} onClose={() => setConfirmDialogOpen(false)}>
        <DialogContent>
          <Typography>
            确认标记 {selectedDate?.toLocaleDateString()} 为有效天数？
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
            当前周期已累计: {currentCycle?.valid_days_count || 0} 天
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialogOpen(false)}>取消</Button>
          <Button onClick={handleConfirmValidDay} variant="contained" color="primary">
            确认
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 周期完成提醒 */}
      <Snackbar
        open={cycleComplete}
        autoHideDuration={6000}
        onClose={() => setCycleComplete(false)}
        message="恭喜！当前周期已完成26天，新的周期已开始"
      />
    </Container>
  );
};

export default HomePage; 