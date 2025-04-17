import React, { useEffect, useState } from 'react';
import { createTheme, ThemeProvider, CssBaseline } from '@mui/material';
import axios from 'axios';
import HomePage from './pages/HomePage';

// 定义主应用组件，封装了HomePage
const MainApp = () => {
  return (
    <HomePage />
  );
};

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
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
});

function App() {
  // 服务器状态检查
  const [serverConnected, setServerConnected] = useState<boolean>(false);
  const [serverCheckComplete, setServerCheckComplete] = useState<boolean>(false);
  const [apiBaseUrl, setApiBaseUrl] = useState<string>('');
  const [connectionError, setConnectionError] = useState<string>('');
  const [retryCount, setRetryCount] = useState<number>(0);

  // 从env-config.js中获取API URL
  const getApiUrl = () => {
    if (window._env_ && window._env_.REACT_APP_API_URL) {
      console.log('从环境配置读取API地址:', window._env_.REACT_APP_API_URL);
      return window._env_.REACT_APP_API_URL;
    }
    // 硬编码备用地址
    const serverIp = '101.126.143.26';
    console.log('使用硬编码的服务器IP:', serverIp);
    return `http://${serverIp}:8000`;
  };

  // 健康检查
  useEffect(() => {
    const checkServerConnection = async () => {
      try {
        // 获取API基础URL
        const baseUrl = getApiUrl();
        setApiBaseUrl(baseUrl);
        console.log('使用API基础URL:', baseUrl);

        // 先尝试直接连接到API根路径
        try {
          console.log('尝试连接API根路径...');
          const rootResponse = await fetch(`${baseUrl}/api`, {
            method: 'GET',
            headers: {'Content-Type': 'application/json'},
            // 确保我们可以检测到CORS错误
            mode: 'cors'
          });
          console.log('API根路径响应:', rootResponse.status);
        } catch (rootError) {
          console.warn('连接API根路径失败，将继续尝试健康检查:', rootError);
        }

        // 发送健康检查请求
        const healthCheckUrl = `${baseUrl}/api/health-check`;
        console.log('发送健康检查请求到:', healthCheckUrl);
        
        // 使用axios带超时设置
        const response = await axios.get(healthCheckUrl, {
          timeout: 5000, // 5秒超时
          headers: {'Content-Type': 'application/json'}
        });
        
        if (response.status === 200) {
          console.log('服务器连接成功，响应:', response.data);
          setServerConnected(true);
          setConnectionError('');
        } else {
          console.error('服务器返回错误状态码:', response.status);
          setServerConnected(false);
          setConnectionError(`服务器返回错误状态码: ${response.status}`);
        }
      } catch (error) {
        console.error('服务器连接失败:', error);
        setServerConnected(false);
        
        // 提供更详细的错误信息
        if (axios.isAxiosError(error)) {
          if (error.code === 'ECONNABORTED') {
            setConnectionError('连接超时，服务器没有及时响应');
          } else if (error.code === 'ERR_NETWORK') {
            setConnectionError('网络错误，可能是CORS问题或服务器未运行');
          } else if (error.response) {
            setConnectionError(`服务器错误: ${error.response.status} - ${error.response.statusText}`);
          } else {
            setConnectionError(`连接错误: ${error.message}`);
          }
        } else {
          setConnectionError(`未知错误: ${error instanceof Error ? error.message : '连接失败'}`);
        }
        
        // 如果连接失败且尝试次数少于3次，则自动重试
        if (retryCount < 3) {
          console.log(`连接失败，${5-retryCount}秒后自动重试...`);
          setTimeout(() => {
            setRetryCount(prev => prev + 1);
          }, 5000);
          return;
        }
      } finally {
        setServerCheckComplete(true);
      }
    };

    checkServerConnection();
  }, [retryCount]);

  // 手动重试
  const handleRetry = () => {
    setServerCheckComplete(false);
    setRetryCount(prev => prev + 1);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className="App">
        {!serverCheckComplete ? (
          // 正在检查服务器状态
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'center', 
            height: '100vh',
            padding: '20px',
            textAlign: 'center'
          }}>
            <h3>正在连接服务器...</h3>
            <p>请稍候，正在确认API服务状态</p>
            <p>尝试次数: {retryCount + 1}</p>
            <div className="loading-spinner" style={{
              border: '5px solid #f3f3f3',
              borderTop: '5px solid #3498db',
              borderRadius: '50%',
              width: '40px',
              height: '40px',
              animation: 'spin 1s linear infinite',
              marginTop: '20px'
            }}></div>
            <style>{`
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            `}</style>
          </div>
        ) : !serverConnected ? (
          // 服务器连接失败
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'center', 
            height: '100vh',
            padding: '20px',
            textAlign: 'center',
            color: '#d32f2f'
          }}>
            <h3>无法连接到服务器</h3>
            <p>API服务器连接失败，请检查网络连接或服务器状态</p>
            <p>尝试连接: <code>{apiBaseUrl}</code></p>
            {connectionError && <p>错误信息: {connectionError}</p>}
            <p>您可以尝试以下解决方案:</p>
            <ol style={{ textAlign: 'left' }}>
              <li>确认后端服务器是否运行 (<code>bash restart.sh</code>)</li>
              <li>检查浏览器控制台是否有CORS错误</li>
              <li>确认API地址配置是否正确</li>
            </ol>
            <button style={{
              marginTop: '20px',
              padding: '10px 15px',
              background: '#2196f3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }} onClick={handleRetry}>
              重试连接
            </button>
          </div>
        ) : (
          // 服务器连接成功，显示主界面
          <MainApp />
        )}
      </div>
    </ThemeProvider>
  );
}

export default App;
