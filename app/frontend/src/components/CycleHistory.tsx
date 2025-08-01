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
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
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
const CycleRow: React.FC<{ cycle: CycleRecord, onRemarkUpdated: () => void, onDeleted: () => void, onCycleUpdated: (updatedCycle: CycleRecord) => void }> = ({ cycle, onRemarkUpdated, onDeleted, onCycleUpdated }) => {
  const [open, setOpen] = useState(false);
  const [skipPeriods, setSkipPeriods] = useState<SkipPeriod[]>([]);
  const [loading, setLoading] = useState(false);
  const [editRemarkOpen, setEditRemarkOpen] = useState(false);
  const [remarkValue, setRemarkValue] = useState(cycle.remark || '');
  const [remarkLoading, setRemarkLoading] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [editForm, setEditForm] = useState({
    cycle_number: cycle.cycle_number,
    start_date: cycle.start_date,
    end_date: cycle.end_date || '',
    remark: cycle.remark || '',
  });
  const [editLoading, setEditLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const isMobile = window.innerWidth < 960; // 检测是否为移动设备
  
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
  
  // 编辑备注保存
  const handleSaveRemark = async () => {
    setRemarkLoading(true);
    try {
      await cyclesApi.updateCycle(cycle.id, { remark: remarkValue });
      setEditRemarkOpen(false);
      onRemarkUpdated();
    } catch (err) {
      alert('备注保存失败');
    } finally {
      setRemarkLoading(false);
    }
  };

  // 编辑表单字段变更
  const handleEditChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEditForm({ ...editForm, [e.target.name]: e.target.value });
  };

  // 提交编辑
  const handleEditSubmit = async () => {
    setEditLoading(true);
    try {
      // 确保日期格式正确
      const updateData: any = {
        cycle_number: Number(editForm.cycle_number),
        start_date: editForm.start_date,
        remark: editForm.remark,
      };
      
      // 只有当end_date不为空时才包含它
      if (editForm.end_date && editForm.end_date.trim() !== '') {
        updateData.end_date = editForm.end_date;
      }
      
      console.log('提交编辑数据:', updateData);
      const updatedCycle = await cyclesApi.updateCycle(cycle.id, updateData);
      setEditOpen(false);
      onCycleUpdated(updatedCycle);
      onRemarkUpdated();
    } catch (err) {
      console.error('编辑保存失败:', err);
      alert('编辑保存失败');
    } finally {
      setEditLoading(false);
    }
  };

  // 删除周期
  const handleDelete = async () => {
    setDeleteLoading(true);
    try {
      await cyclesApi.deleteCycle(cycle.id);
      setDeleteOpen(false);
      onDeleted();
    } catch (err) {
      alert('删除失败');
    } finally {
      setDeleteLoading(false);
    }
  };
  
  // 移动端显示内容 - 跳过时间详情
  if (isMobile) {
    return (
      <>
        <Button
          variant="outlined"
          color="primary"
          fullWidth
          onClick={toggleOpen}
          onTouchStart={toggleOpen}
          startIcon={open ? <VisibilityOffIcon /> : <VisibilityIcon />}
          sx={{ borderRadius: '20px', py: 1 }}
        >
          {open ? '隐藏跳过时间段' : '查看跳过时间段'}
        </Button>
        
        <Collapse in={open} timeout="auto" unmountOnExit>
          <Box sx={{ mt: 2, mb: 1, p: 1, backgroundColor: '#f5f5f5', borderRadius: '10px' }}>
            {loading ? (
              <Box display="flex" justifyContent="center" py={2}>
                <CircularProgress size={24} />
              </Box>
            ) : skipPeriods.length === 0 ? (
              <Typography variant="body2" align="center" color="text.secondary" py={1}>
                此周期无跳过时间段记录
              </Typography>
            ) : (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  <AccessTimeIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                  跳过时间段记录 ({skipPeriods.length})
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 1 }}>
                  {skipPeriods.map((period) => (
                    <Box 
                      key={period.id} 
                      sx={{ 
                        p: 1, 
                        borderRadius: '8px', 
                        border: '1px solid #e0e0e0',
                        backgroundColor: 'white'
                      }}
                    >
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2" color="text.secondary">日期:</Typography>
                        <Typography variant="body2">
                          {formatDatePart(period.date)}
                        </Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2" color="text.secondary">时间段:</Typography>
                        <Typography variant="body2">
                          {period.start_time.substring(0, 5)} - {period.end_time.substring(0, 5)}
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                </Box>
              </Box>
            )}
          </Box>
        </Collapse>
      </>
    );
  }
  
  // 桌面端显示内容 - 表格行
  return (
    <>
      <StyledTableRow>
        <TableCell>{cycle.cycle_number}</TableCell>
        <TableCell>{formatDatePart(cycle.start_date)}</TableCell>
        <TableCell>{formatTimePart(cycle.start_date)}</TableCell>
        <TableCell>{cycle.end_date ? formatDatePart(cycle.end_date) : '进行中'}</TableCell>
        <TableCell>{cycle.end_date ? formatTimePart(cycle.end_date) : '--'}</TableCell>
        <TableCell>{cycle.valid_days_count}/26 天</TableCell>
        <TableCell>{formatHours(cycle.valid_hours_count)}</TableCell>
        <TableCell>
          {cycle.is_completed ? (
            <Chip label="已完成" color="success" size="small" />
          ) : (
            <Chip label="进行中" color="primary" size="small" />
          )}
        </TableCell>
        <TableCell>{cycle.remark ? cycle.remark : '-'}</TableCell>
        <TableCell>
          <Button
            variant="outlined"
            size="small"
            onClick={toggleOpen}
            startIcon={open ? <VisibilityOffIcon /> : <VisibilityIcon />}
          >
            {open ? '隐藏详情' : '查看详情'}
          </Button>
          
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ mt: 2, bgcolor: '#f5f5f5', p: 2, borderRadius: 1 }}>
              {loading ? (
                <Box display="flex" justifyContent="center" p={2}>
                  <CircularProgress size={24} />
                </Box>
              ) : skipPeriods.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  此周期无跳过时间段记录
                </Typography>
              ) : (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    <AccessTimeIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                    跳过时间段记录 ({skipPeriods.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 1 }}>
                    {skipPeriods.map((period) => (
                      <Box 
                        key={period.id} 
                        sx={{ 
                          p: 1, 
                          borderRadius: 1, 
                          border: '1px solid #e0e0e0',
                          bgcolor: 'background.paper'
                        }}
                      >
                        <Typography variant="body2">
                          日期: {formatDatePart(period.date)}
                        </Typography>
                        <Typography variant="body2">
                          时间: {period.start_time.substring(0, 5)} - {period.end_time.substring(0, 5)}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                </Box>
              )}
            </Box>
          </Collapse>
        </TableCell>
        <TableCell>
          <Button size="small" variant="outlined" onClick={() => setEditRemarkOpen(true)} sx={{ mr: 1 }}>
            编辑备注
          </Button>
          <Button size="small" variant="outlined" color="primary" onClick={() => setEditOpen(true)} sx={{ mr: 1 }}>
            编辑
          </Button>
          <Button size="small" variant="outlined" color="error" onClick={() => setDeleteOpen(true)}>
            删除
          </Button>
        </TableCell>
      </StyledTableRow>
      {/* 编辑备注弹窗 */}
      <Dialog open={editRemarkOpen} onClose={() => setEditRemarkOpen(false)}>
        <DialogTitle>编辑备注</DialogTitle>
        <DialogContent>
          <TextField
            label="备注"
            value={remarkValue}
            onChange={e => setRemarkValue(e.target.value)}
            fullWidth
            multiline
            minRows={2}
            autoFocus
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditRemarkOpen(false)}>取消</Button>
          <Button onClick={handleSaveRemark} disabled={remarkLoading} variant="contained" color="primary">
            保存
          </Button>
        </DialogActions>
      </Dialog>
      {/* 编辑所有字段弹窗 */}
      <Dialog open={editOpen} onClose={() => setEditOpen(false)}>
        <DialogTitle>编辑周期记录</DialogTitle>
        <DialogContent>
          <TextField
            label="周期编号"
            name="cycle_number"
            type="number"
            value={editForm.cycle_number}
            onChange={handleEditChange}
            fullWidth
            margin="dense"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="开始日期"
            name="start_date"
            type="date"
            value={editForm.start_date ? editForm.start_date.slice(0, 10) : ''}
            onChange={e => {
              const currentTime = editForm.start_date ? editForm.start_date.slice(11, 19) : '00:00:00';
              setEditForm({ ...editForm, start_date: e.target.value + 'T' + currentTime });
            }}
            fullWidth
            margin="dense"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="开始时间"
            name="start_time"
            type="time"
            value={editForm.start_date ? editForm.start_date.slice(11, 16) : ''}
            onChange={e => {
              const currentDate = editForm.start_date ? editForm.start_date.slice(0, 10) : new Date().toISOString().slice(0, 10);
              setEditForm({ ...editForm, start_date: currentDate + 'T' + e.target.value + ':00' });
            }}
            fullWidth
            margin="dense"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="结束日期"
            name="end_date"
            type="date"
            value={editForm.end_date && typeof editForm.end_date === 'string' && editForm.end_date.length >= 10 ? editForm.end_date.slice(0, 10) : ''}
            onChange={e => {
              if (e.target.value) {
                const currentTime = (editForm.end_date && typeof editForm.end_date === 'string' && editForm.end_date.length >= 19) ? editForm.end_date.slice(11, 19) : '00:00:00';
                setEditForm({ ...editForm, end_date: e.target.value + 'T' + currentTime });
              } else {
                setEditForm({ ...editForm, end_date: '' });
              }
            }}
            fullWidth
            margin="dense"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="结束时间"
            name="end_time"
            type="time"
            value={editForm.end_date && typeof editForm.end_date === 'string' && editForm.end_date.length >= 16 ? editForm.end_date.slice(11, 16) : ''}
            onChange={e => {
              const currentDate = (editForm.end_date && typeof editForm.end_date === 'string' && editForm.end_date.length >= 10) ? editForm.end_date.slice(0, 10) : editForm.start_date.slice(0, 10);
              setEditForm({ ...editForm, end_date: currentDate + 'T' + e.target.value + ':00' });
            }}
            fullWidth
            margin="dense"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="备注"
            name="remark"
            value={editForm.remark}
            onChange={handleEditChange}
            fullWidth
            margin="dense"
            multiline
            minRows={2}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditOpen(false)}>取消</Button>
          <Button onClick={handleEditSubmit} disabled={editLoading} variant="contained" color="primary">保存</Button>
        </DialogActions>
      </Dialog>
      {/* 删除确认弹窗 */}
      <Dialog open={deleteOpen} onClose={() => setDeleteOpen(false)}>
        <DialogTitle>确认删除</DialogTitle>
        <DialogContent>确定要删除该周期记录吗？此操作不可恢复。</DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteOpen(false)}>取消</Button>
          <Button onClick={handleDelete} disabled={deleteLoading} color="error" variant="contained">删除</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

// 移动端编辑组件
const MobileCycleEdit: React.FC<{ 
  cycle: CycleRecord, 
  onUpdated: () => void,
  onCycleUpdated: (updatedCycle: CycleRecord) => void
}> = ({ cycle, onUpdated, onCycleUpdated }) => {
  const [editRemarkOpen, setEditRemarkOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [remarkValue, setRemarkValue] = useState(cycle.remark || '');
  const [remarkLoading, setRemarkLoading] = useState(false);
  const [editForm, setEditForm] = useState({
    cycle_number: cycle.cycle_number,
    start_date: cycle.start_date,
    end_date: cycle.end_date || '',
    remark: cycle.remark || '',
  });
  const [editLoading, setEditLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const handleSaveRemark = async () => {
    setRemarkLoading(true);
    try {
      await cyclesApi.updateCycle(cycle.id, { remark: remarkValue });
      setEditRemarkOpen(false);
      onUpdated();
    } catch (err) {
      alert('备注保存失败');
    } finally {
      setRemarkLoading(false);
    }
  };

  const handleEditChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setEditForm(prev => ({ ...prev, [name]: value }));
  };

  const handleEditSubmit = async () => {
    setEditLoading(true);
    try {
      const updateData: any = {
        cycle_number: Number(editForm.cycle_number),
        start_date: editForm.start_date,
        remark: editForm.remark,
      };
      
      if (editForm.end_date && editForm.end_date.trim() !== '') {
        updateData.end_date = editForm.end_date;
      }
      
      const updatedCycle = await cyclesApi.updateCycle(cycle.id, updateData);
      setEditOpen(false);
      onCycleUpdated(updatedCycle);
      onUpdated();
    } catch (err) {
      alert('编辑保存失败');
    } finally {
      setEditLoading(false);
    }
  };

  const handleDelete = async () => {
    setDeleteLoading(true);
    try {
      await cyclesApi.deleteCycle(cycle.id);
      setDeleteOpen(false);
      onUpdated();
    } catch (err) {
      alert('删除失败');
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <>
      <Box mt={2} display="flex" gap={1} flexWrap="wrap">
        <Button 
          size="small" 
          variant="outlined" 
          onClick={() => setEditRemarkOpen(true)}
          sx={{ flex: 1 }}
        >
          编辑备注
        </Button>
        <Button 
          size="small" 
          variant="outlined" 
          color="primary" 
          onClick={() => setEditOpen(true)}
          sx={{ flex: 1 }}
        >
          编辑
        </Button>
        <Button 
          size="small" 
          variant="outlined" 
          color="error" 
          onClick={() => setDeleteOpen(true)}
          sx={{ flex: 1 }}
        >
          删除
        </Button>
      </Box>

      {/* 编辑备注弹窗 */}
      <Dialog open={editRemarkOpen} onClose={() => setEditRemarkOpen(false)} fullWidth>
        <DialogTitle>编辑备注</DialogTitle>
        <DialogContent>
          <TextField
            label="备注"
            value={remarkValue}
            onChange={e => setRemarkValue(e.target.value)}
            fullWidth
            multiline
            minRows={2}
            autoFocus
            margin="dense"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditRemarkOpen(false)}>取消</Button>
          <Button onClick={handleSaveRemark} disabled={remarkLoading} variant="contained" color="primary">
            保存
          </Button>
        </DialogActions>
      </Dialog>

      {/* 编辑所有字段弹窗 */}
      <Dialog open={editOpen} onClose={() => setEditOpen(false)} fullWidth>
        <DialogTitle>编辑周期记录</DialogTitle>
        <DialogContent>
          <TextField
            label="周期编号"
            name="cycle_number"
            type="number"
            value={editForm.cycle_number}
            onChange={handleEditChange}
            fullWidth
            margin="dense"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="开始日期"
            name="start_date"
            type="date"
            value={editForm.start_date ? editForm.start_date.slice(0, 10) : ''}
            onChange={e => {
              const currentTime = editForm.start_date ? editForm.start_date.slice(11, 19) : '00:00:00';
              setEditForm({ ...editForm, start_date: e.target.value + 'T' + currentTime });
            }}
            fullWidth
            margin="dense"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="开始时间"
            name="start_time"
            type="time"
            value={editForm.start_date ? editForm.start_date.slice(11, 16) : ''}
            onChange={e => {
              const currentDate = editForm.start_date ? editForm.start_date.slice(0, 10) : new Date().toISOString().slice(0, 10);
              setEditForm({ ...editForm, start_date: currentDate + 'T' + e.target.value + ':00' });
            }}
            fullWidth
            margin="dense"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="结束日期"
            name="end_date"
            type="date"
            value={editForm.end_date && typeof editForm.end_date === 'string' && editForm.end_date.length >= 10 ? editForm.end_date.slice(0, 10) : ''}
            onChange={e => {
              if (e.target.value) {
                const currentTime = (editForm.end_date && typeof editForm.end_date === 'string' && editForm.end_date.length >= 19) ? editForm.end_date.slice(11, 19) : '00:00:00';
                setEditForm({ ...editForm, end_date: e.target.value + 'T' + currentTime });
              } else {
                setEditForm({ ...editForm, end_date: '' });
              }
            }}
            fullWidth
            margin="dense"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="结束时间"
            name="end_time"
            type="time"
            value={editForm.end_date && typeof editForm.end_date === 'string' && editForm.end_date.length >= 16 ? editForm.end_date.slice(11, 16) : ''}
            onChange={e => {
              const currentDate = (editForm.end_date && typeof editForm.end_date === 'string' && editForm.end_date.length >= 10) ? editForm.end_date.slice(0, 10) : editForm.start_date.slice(0, 10);
              setEditForm({ ...editForm, end_date: currentDate + 'T' + e.target.value + ':00' });
            }}
            fullWidth
            margin="dense"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="备注"
            name="remark"
            value={editForm.remark}
            onChange={handleEditChange}
            fullWidth
            margin="dense"
            multiline
            minRows={2}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditOpen(false)}>取消</Button>
          <Button onClick={handleEditSubmit} disabled={editLoading} variant="contained" color="primary">保存</Button>
        </DialogActions>
      </Dialog>

      {/* 删除确认弹窗 */}
      <Dialog open={deleteOpen} onClose={() => setDeleteOpen(false)}>
        <DialogTitle>确认删除</DialogTitle>
        <DialogContent>确定要删除该周期记录吗？此操作不可恢复。</DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteOpen(false)}>取消</Button>
          <Button onClick={handleDelete} disabled={deleteLoading} color="error" variant="contained">删除</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

// 移动端显示的周期跳过时间段组件
const MobileCycleSkipPeriods: React.FC<{ cycle: CycleRecord }> = ({ cycle }) => {
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
  
  return (
    <>
      <Button
        variant="outlined"
        color="primary"
        fullWidth
        onClick={toggleOpen}
        onTouchStart={toggleOpen}
        startIcon={open ? <VisibilityOffIcon /> : <VisibilityIcon />}
        sx={{ borderRadius: '20px', py: 1 }}
      >
        {open ? '隐藏跳过时间段' : '查看跳过时间段'}
      </Button>
      
      <Collapse in={open} timeout="auto" unmountOnExit>
        <Box sx={{ mt: 2, mb: 1, p: 1, backgroundColor: '#f5f5f5', borderRadius: '10px' }}>
          {loading ? (
            <Box display="flex" justifyContent="center" py={2}>
              <CircularProgress size={24} />
            </Box>
          ) : skipPeriods.length === 0 ? (
            <Typography variant="body2" align="center" color="text.secondary" py={1}>
              此周期无跳过时间段记录
            </Typography>
          ) : (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                <AccessTimeIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                跳过时间段记录 ({skipPeriods.length})
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 1 }}>
                {skipPeriods.map((period) => (
                  <Box 
                    key={period.id} 
                    sx={{ 
                      p: 1, 
                      borderRadius: '8px', 
                      border: '1px solid #e0e0e0',
                      backgroundColor: 'white'
                    }}
                  >
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2" color="text.secondary">日期:</Typography>
                      <Typography variant="body2">
                        {formatDatePart(period.date)}
                      </Typography>
                    </Box>
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2" color="text.secondary">时间段:</Typography>
                      <Typography variant="body2">
                        {period.start_time.substring(0, 5)} - {period.end_time.substring(0, 5)}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            </Box>
          )}
        </Box>
      </Collapse>
    </>
  );
};

const CycleHistory: React.FC = () => {
  const [cycles, setCycles] = useState<CycleRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshFlag, setRefreshFlag] = useState(false);
  
  // 获取所有周期记录
  const fetchCycles = useCallback(async () => {
    try {
      setLoading(true);
      const data = await cyclesApi.getAllCycles();
      setCycles(data.sort((a, b) => b.cycle_number - a.cycle_number));
    } catch (err) {
      console.error('获取周期历史记录失败:', err);
      setError('加载周期历史记录失败，请刷新重试');
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    fetchCycles();
  }, [fetchCycles]);
  
  // 手动刷新数据
  const handleRefresh = () => {
    fetchCycles();
  };
  
  const handleRemarkUpdated = () => setRefreshFlag(f => !f);
  
  // 实时更新单个周期记录
  const handleCycleUpdated = (updatedCycle: CycleRecord) => {
    setCycles(prevCycles => 
      prevCycles.map(cycle => 
        cycle.id === updatedCycle.id ? updatedCycle : cycle
      )
    );
  };
  
  useEffect(() => {
    fetchCycles();
  }, [refreshFlag]);
  
  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">周期历史记录</Typography>
        <Button 
          startIcon={<RefreshIcon />} 
          onClick={handleRefresh}
          size="small"
          sx={{ 
            borderRadius: '20px',
            fontSize: { xs: '14px', sm: '14px' }
          }}
          onTouchStart={handleRefresh}
        >
          刷新
        </Button>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" py={4}>
          <CircularProgress />
        </Box>
      ) : cycles.length === 0 ? (
        <Alert severity="info">暂无周期历史记录</Alert>
      ) : (
        <>
          {/* 移动端视图 - 使用卡片布局替代表格 */}
          <Box sx={{ display: { xs: 'flex', md: 'none' }, flexDirection: 'column', gap: 2 }}>
            {cycles.map((cycle) => (
              <Card key={cycle.id} sx={{ mb: 2, p: 1 }}>
                <CardContent sx={{ p: 1 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
                      周期 #{cycle.cycle_number}
                    </Typography>
                    {cycle.is_completed ? (
                      <Chip label="已完成" color="success" size="small" />
                    ) : (
                      <Chip label="进行中" color="primary" size="small" />
                    )}
                  </Box>
                  
                  <Divider sx={{ my: 1 }} />
                  
                  <Box sx={{ '& > div': { py: 0.5 } }}>
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2" color="text.secondary">开始日期:</Typography>
                      <Typography variant="body2">
                        {new Date(cycle.start_date).toLocaleDateString('zh-CN')}
                      </Typography>
                    </Box>
                    
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2" color="text.secondary">开始时间:</Typography>
                      <Typography variant="body2">
                        {new Date(cycle.start_date).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                      </Typography>
                    </Box>
                    
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2" color="text.secondary">结束日期:</Typography>
                      <Typography variant="body2">
                        {cycle.end_date ? new Date(cycle.end_date).toLocaleDateString('zh-CN') : '进行中'}
                      </Typography>
                    </Box>
                    
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2" color="text.secondary">结束时间:</Typography>
                      <Typography variant="body2">
                        {cycle.end_date ? new Date(cycle.end_date).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : '--'}
                      </Typography>
                    </Box>
                    
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2" color="text.secondary">有效天数:</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {cycle.valid_days_count}/26 天
                      </Typography>
                    </Box>
                    
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2" color="text.secondary">有效小时数:</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {formatHours(cycle.valid_hours_count)}
                      </Typography>
                    </Box>
                  </Box>
                  <Divider sx={{ my: 1 }} />
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2" color="text.secondary">备注:</Typography>
                    <Typography variant="body2">{cycle.remark ? cycle.remark : '-'}</Typography>
                  </Box>
                  <Box mt={1}>
                    {/* 使用专门的移动端组件，而不是CycleRow */}
                    <MobileCycleSkipPeriods cycle={cycle} />
                    <MobileCycleEdit cycle={cycle} onUpdated={handleRemarkUpdated} onCycleUpdated={handleCycleUpdated} />
                  </Box>
                </CardContent>
              </Card>
            ))}
          </Box>
          
          {/* 桌面端视图 - 表格布局 */}
          <TableContainer sx={{ display: { xs: 'none', md: 'block' }, overflowX: 'auto' }}>
            <Table aria-label="周期历史记录表">
              <TableHead>
                <TableRow>
                  <TableCell>周期号</TableCell>
                  <TableCell>开始日期</TableCell>
                  <TableCell>开始时间</TableCell>
                  <TableCell>结束日期</TableCell>
                  <TableCell>结束时间</TableCell>
                  <TableCell>有效天数</TableCell>
                  <TableCell>有效小时数</TableCell>
                  <TableCell>状态</TableCell>
                  <TableCell>备注</TableCell>
                  <TableCell>详情</TableCell>
                  <TableCell>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {cycles.map((cycle) => (
                  <CycleRow key={cycle.id} cycle={cycle} onRemarkUpdated={handleRemarkUpdated} onDeleted={handleRefresh} onCycleUpdated={handleCycleUpdated} />
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Paper>
  );
};

export default CycleHistory; 