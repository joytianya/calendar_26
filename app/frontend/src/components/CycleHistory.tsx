import React, { useState, useEffect, useCallback } from 'react';
import { 
  Paper, 
  Typography, 
  Box, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  CircularProgress,
  Alert,
  Chip,
  Collapse,
  Divider,
  Card,
  CardContent,
  Button
} from '@mui/material';
import { styled } from '@mui/material/styles';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import EventBusyIcon from '@mui/icons-material/EventBusy';
import RefreshIcon from '@mui/icons-material/Refresh';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import { CycleRecord, SkipPeriod } from '../models/types';
import { cyclesApi, calendarDataApi } from '../services/api';

// 创建自定义样式的表格行
const StyledTableRow = styled(TableRow)(({ theme }) => ({
  '&:nth-of-type(odd)': {
    backgroundColor: theme.palette.action.hover,
  },
  '&:hover': {
    backgroundColor: theme.palette.action.selected,
  },
}));

// 自定义跳过时间段卡片样式
const SkipPeriodCard = styled(Card)(({ theme }) => ({
  minWidth: 200,
  maxWidth: 300,
  flex: '1 0 30%',
  transition: 'transform 0.2s, box-shadow 0.2s',
  '&:hover': {
    transform: 'translateY(-5px)',
    boxShadow: theme.shadows[6],
  },
  borderRadius: '12px',
  border: `1px solid ${theme.palette.divider}`,
}));

// 自定义折叠区域容器
const CollapseContainer = styled(Box)(({ theme }) => ({
  background: theme.palette.background.default,
  borderRadius: theme.shape.borderRadius,
  padding: theme.spacing(2),
  boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.05)',
}));

// 自定义时间段显示样式
const TimeRangeChip = styled(Box)(({ theme }) => ({
  display: 'inline-flex',
  alignItems: 'center',
  padding: '4px 10px',
  borderRadius: '20px',
  backgroundColor: theme.palette.primary.light,
  color: theme.palette.primary.contrastText,
  fontSize: '0.875rem',
}));

// 自定义状态指示器
const StatusIndicator = styled('div')<{ status: 'completed' | 'active' }>(({ theme, status }) => ({
  width: '10px',
  height: '10px',
  borderRadius: '50%',
  marginRight: theme.spacing(1),
  backgroundColor: status === 'completed' ? theme.palette.success.main : theme.palette.primary.main,
  display: 'inline-block',
}));

// 自定义操作按钮
const ActionButton = styled(Button)(({ theme }) => ({
  minWidth: '120px',
  borderRadius: '20px',
  boxShadow: theme.shadows[2],
  fontWeight: 'bold',
  marginTop: theme.spacing(1),
  '&:hover': {
    boxShadow: theme.shadows[4],
  },
}));

// 格式化小时数
const formatHours = (hours: number | undefined): string => {
  if (hours === undefined || hours === null) return "0小时";
  
  const wholeDays = Math.floor(hours / 24);
  const remainingHours = Math.round((hours % 24) * 10) / 10; // 保留一位小数
  
  if (wholeDays > 0) {
    return `${wholeDays}天 ${remainingHours}小时`;
  } else {
    return `${remainingHours}小时`;
  }
};

// 周期记录行组件
const CycleRow: React.FC<{ cycle: CycleRecord }> = ({ cycle }) => {
  const [open, setOpen] = useState(false);
  const [skipPeriods, setSkipPeriods] = useState<SkipPeriod[]>([]);
  const [loading, setLoading] = useState(false);
  
  // 获取该周期的跳过时间段
  const fetchSkipPeriods = async () => {
    if (!open && skipPeriods.length === 0 && cycle.id) {
      try {
        setLoading(true);
        const data = await calendarDataApi.getSkipPeriods(cycle.id);
        setSkipPeriods(data);
      } catch (err) {
        console.error('获取跳过时间段失败:', err);
      } finally {
        setLoading(false);
      }
    }
  };
  
  // 切换展开/折叠状态
  const toggleOpen = () => {
    console.log('切换展开状态，当前:', open, '->新状态:', !open);
    const newOpenState = !open;
    setOpen(newOpenState);
    
    if (newOpenState) {
      fetchSkipPeriods();
    }
  };
  
  // 创建并返回中国标准时间的Date对象
  const createChinaDate = (dateStr: string | null): Date | null => {
    if (!dateStr) return null;
    // 创建标准的Date对象，会自动按照本地时区处理
    const date = new Date(dateStr);
    return date;
  };
  
  // 格式化日期部分（仅年月日）
  const formatDatePart = (dateStr: string | null): string => {
    if (!dateStr) return '进行中';
    const date = createChinaDate(dateStr);
    if (!date) return '无效日期';
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      timeZone: 'Asia/Shanghai' // 确保使用北京时间
    });
  };
  
  // 格式化时间部分（仅时分）
  const formatTimePart = (dateStr: string | null): string => {
    if (!dateStr) return '--:--';
    const date = createChinaDate(dateStr);
    if (!date) return '--:--';
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Shanghai' // 确保使用北京时间
    });
  };
  
  // 格式化日期（只显示日期部分）
  const formatDateOnly = (dateStr: string): string => {
    const date = createChinaDate(dateStr);
    if (!date) return '无效日期';
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      timeZone: 'Asia/Shanghai' // 确保使用北京时间
    });
  };
  
  // 格式化时间（只显示时间部分）
  const formatTimeOnly = (timeStr: string): string => {
    return timeStr.substring(0, 5); // 只取HH:MM部分
  };
  
  // 计算周期持续时间
  const calculateDuration = (cycle: CycleRecord): string => {
    if (!cycle.end_date) return '进行中';
    
    const startDate = createChinaDate(cycle.start_date);
    const endDate = createChinaDate(cycle.end_date);
    if (!startDate || !endDate) return '计算中...';
    
    const diffTime = Math.abs(endDate.getTime() - startDate.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return `${diffDays} 天`;
  };
  
  // 获取周期状态
  const getCycleStatus = (cycle: CycleRecord): React.ReactElement => {
    if (cycle.is_completed) {
      return (
        <Box display="flex" alignItems="center">
          <StatusIndicator status="completed" />
          <Chip 
            label="已完成" 
            color="success" 
            size="small" 
            sx={{ borderRadius: '16px' }}
          />
        </Box>
      );
    } else {
      return (
        <Box display="flex" alignItems="center">
          <StatusIndicator status="active" />
          <Chip 
            label="进行中" 
            color="primary" 
            size="small" 
            sx={{ borderRadius: '16px' }}
          />
        </Box>
      );
    }
  };
  
  // 计算跳过时间段的总小时数
  const calculateTotalSkippedHours = (periods: SkipPeriod[]): number => {
    return periods.reduce((total, period) => {
      const [startHour, startMinute] = period.start_time.split(':').map(Number);
      const [endHour, endMinute] = period.end_time.split(':').map(Number);
      
      let hours = 0;
      if (endHour > startHour || (endHour === startHour && endMinute >= startMinute)) {
        // 同一天内
        hours = (endHour - startHour) + (endMinute - startMinute) / 60;
      } else {
        // 跨天
        hours = (24 - startHour) + endHour + (endMinute - startMinute) / 60;
      }
      
      return total + hours;
    }, 0);
  };
  
  return (
    <React.Fragment>
      <StyledTableRow>
        <TableCell align="center">
          {cycle.cycle_number}
        </TableCell>
        <TableCell align="center">{formatDatePart(cycle.start_date)}</TableCell>
        <TableCell align="center">{formatTimePart(cycle.start_date)}</TableCell>
        <TableCell align="center">{formatDatePart(cycle.end_date)}</TableCell>
        <TableCell align="center">{calculateDuration(cycle)}</TableCell>
        <TableCell align="center">
          <Box display="flex" flexDirection="column">
            <Typography variant="body2">{cycle.valid_days_count} 天</Typography>
            <Typography variant="caption" color="text.secondary">
              {typeof cycle.valid_hours_count === 'number' 
                ? formatHours(cycle.valid_hours_count) 
                : '0小时'}
            </Typography>
          </Box>
        </TableCell>
        <TableCell align="center">
          {getCycleStatus(cycle)}
        </TableCell>
        <TableCell align="center">
          <ActionButton
            variant="contained"
            color={open ? "secondary" : "primary"}
            size="small"
            startIcon={open ? <VisibilityOffIcon /> : <VisibilityIcon />}
            onClick={toggleOpen}
          >
            {open ? '收起详情' : '查看详情'}
          </ActionButton>
        </TableCell>
      </StyledTableRow>
      
      {/* 折叠区域 - 显示跳过时间段信息 */}
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={8}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <CollapseContainer sx={{ margin: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" component="div" sx={{ display: 'flex', alignItems: 'center' }}>
                  <EventBusyIcon color="error" sx={{ mr: 1 }} />
                  跳过时间段 
                  <Chip 
                    label={`共${skipPeriods.length}个`} 
                    color="primary" 
                    size="small" 
                    sx={{ ml: 1, borderRadius: '16px' }}
                  />
                </Typography>
                {skipPeriods.length > 0 && (
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <AccessTimeIcon fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                      总计跳过：{formatHours(calculateTotalSkippedHours(skipPeriods))}
                    </Typography>
                  </Box>
                )}
              </Box>
              
              {loading ? (
                <Box display="flex" justifyContent="center" p={2}>
                  <CircularProgress size={24} />
                </Box>
              ) : skipPeriods.length === 0 ? (
                <Alert severity="info" sx={{ mb: 2 }}>
                  本周期没有跳过的时间段
                </Alert>
              ) : (
                <Box sx={{ 
                  display: 'flex', 
                  flexWrap: 'wrap', 
                  gap: 2, 
                  maxHeight: '350px', 
                  overflowY: 'auto',
                  mb: 2,
                  pb: 1
                }}>
                  {skipPeriods.map((period) => {
                    // 计算这个时间段跳过的小时数
                    const [startHour, startMinute] = period.start_time.split(':').map(Number);
                    const [endHour, endMinute] = period.end_time.split(':').map(Number);
                    
                    let hours = 0;
                    if (endHour > startHour || (endHour === startHour && endMinute >= startMinute)) {
                      // 同一天内
                      hours = (endHour - startHour) + (endMinute - startMinute) / 60;
                    } else {
                      // 跨天
                      hours = (24 - startHour) + endHour + (endMinute - startMinute) / 60;
                    }
                    
                    return (
                      <SkipPeriodCard key={period.id}>
                        <CardContent sx={{ p: 2 }}>
                          <Box display="flex" flexDirection="column" gap={1}>
                            <Box display="flex" alignItems="center" mb={1}>
                              <EventBusyIcon color="error" sx={{ mr: 1 }} />
                              <Typography variant="h6" component="div">
                                {formatDateOnly(period.date)}
                              </Typography>
                            </Box>
                            <Divider sx={{ mb: 1 }} />
                            <Box display="flex" alignItems="center" justifyContent="space-between">
                              <TimeRangeChip>
                                <AccessTimeIcon fontSize="small" sx={{ mr: 0.5 }} />
                                {formatTimeOnly(period.start_time)} - {formatTimeOnly(period.end_time)}
                              </TimeRangeChip>
                              <Chip 
                                label={`${hours.toFixed(1)}小时`} 
                                size="small" 
                                color="secondary"
                                variant="outlined"
                                sx={{ fontSize: '0.75rem' }}
                              />
                            </Box>
                          </Box>
                        </CardContent>
                      </SkipPeriodCard>
                    );
                  })}
                </Box>
              )}
            </CollapseContainer>
          </Collapse>
        </TableCell>
      </TableRow>
    </React.Fragment>
  );
};

const CycleHistory: React.FC = () => {
  const [cycles, setCycles] = useState<CycleRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // 刷新数据的间隔时间（毫秒）
  const REFRESH_INTERVAL = 30000; // 30秒
  
  // 获取周期历史记录
  const fetchCycles = useCallback(async () => {
    try {
      setLoading(true);
      const data = await cyclesApi.getAllCycles();
      // 确保每个周期记录都有valid_hours_count字段
      const processedData = data.map(cycle => ({
        ...cycle,
        valid_hours_count: cycle.valid_hours_count || 0
      }));
      setCycles(processedData);
      setError(null);
    } catch (err) {
      console.error('获取周期历史失败:', err);
      setError('获取周期历史失败，请检查网络连接并重试');
    } finally {
      setLoading(false);
    }
  }, []);
  
  // 初始加载
  useEffect(() => {
    fetchCycles();
    
    // 设置定时器，定期刷新数据
    const intervalId = setInterval(() => {
      fetchCycles();
    }, REFRESH_INTERVAL);
    
    // 清理函数，组件卸载时清除定时器
    return () => clearInterval(intervalId);
  }, [fetchCycles]);

  // 手动刷新数据
  const handleRefresh = () => {
    fetchCycles();
  };
  
  if (loading && cycles.length === 0) {
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
  
  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">
          周期历史记录
        </Typography>
        <Button 
          startIcon={<RefreshIcon />} 
          size="small" 
          onClick={handleRefresh}
          color="primary"
          variant="outlined"
        >
          刷新数据
        </Button>
      </Box>
      
      <Alert severity="info" sx={{ mb: 2 }}>
        点击右侧"查看详情"按钮可以查看该周期的跳过时间记录
      </Alert>
      
      {cycles.length === 0 ? (
        <Alert severity="info">
          暂无周期记录
        </Alert>
      ) : (
        <TableContainer sx={{ borderRadius: 2, overflow: 'hidden' }}>
          <Table aria-label="周期历史记录表" size="medium">
            <TableHead>
              <TableRow sx={{ backgroundColor: (theme) => theme.palette.primary.light }}>
                <TableCell width="8%" align="center" sx={{ color: 'white', fontWeight: 'bold' }}>周期</TableCell>
                <TableCell width="14%" align="center" sx={{ color: 'white', fontWeight: 'bold' }}>开始日期</TableCell>
                <TableCell width="8%" align="center" sx={{ color: 'white', fontWeight: 'bold' }}>开始时间</TableCell>
                <TableCell width="14%" align="center" sx={{ color: 'white', fontWeight: 'bold' }}>结束日期</TableCell>
                <TableCell width="10%" align="center" sx={{ color: 'white', fontWeight: 'bold' }}>持续时间</TableCell>
                <TableCell width="14%" align="center" sx={{ color: 'white', fontWeight: 'bold' }}>
                  <Box display="flex" flexDirection="column">
                    <Typography variant="body2" sx={{ color: 'white' }}>有效天数</Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>有效小时数</Typography>
                  </Box>
                </TableCell>
                <TableCell width="12%" align="center" sx={{ color: 'white', fontWeight: 'bold' }}>状态</TableCell>
                <TableCell width="20%" align="center" sx={{ color: 'white', fontWeight: 'bold' }}>操作</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {cycles.map((cycle) => (
                <CycleRow key={cycle.id} cycle={cycle} />
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Paper>
  );
};

export default CycleHistory; 