import React, { useEffect } from 'react';
import { createTheme, ThemeProvider, CssBaseline } from '@mui/material';
import axios from 'axios';
import HomePage from './pages/HomePage';

// 创建主题
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: [
      'Roboto',
      'Arial',
      'sans-serif',
    ].join(','),
  },
});

function App() {
  useEffect(() => {
    // 心跳函数
    const sendHeartbeat = async () => {
      try {
        await axios.get('/api/health-check');
      } catch (error) {
        // 心跳请求失败时不需要特别处理
        console.debug('Heartbeat request failed:', error);
      }
    };

    // 立即发送一次心跳
    sendHeartbeat();

    // 设置定时器，每1分钟发送一次心跳
    const heartbeatInterval = setInterval(sendHeartbeat, 60 * 1000);

    // 清理函数
    return () => {
      clearInterval(heartbeatInterval);
    };
  }, []); // 空依赖数组，表示只在组件挂载时执行一次

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <HomePage />
    </ThemeProvider>
  );
}

export default App;
