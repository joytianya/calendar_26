import logging
import logging.handlers
import os
from datetime import datetime

# 获取日志目录，优先使用环境变量，其次使用默认路径
default_log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
LOG_DIR = os.environ.get('LOG_DIR', default_log_dir)

# 确保日志目录存在
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 日期格式
date_str = datetime.now().strftime("%Y-%m-%d")

# 配置根日志记录器
def setup_logging():
    # 配置根日志记录器
    root_logger = logging.getLogger()
    
    # 获取日志级别，默认为INFO
    log_level_name = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    root_logger.setLevel(log_level)
    
    # 清除可能存在的处理程序
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台处理程序
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理程序
    file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(LOG_DIR, f'app_{date_str}.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # API访问日志
    api_logger = logging.getLogger('api')
    api_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(LOG_DIR, f'api_{date_str}.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    api_handler.setLevel(log_level)
    api_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    api_handler.setFormatter(api_formatter)
    api_logger.addHandler(api_handler)
    
    # 错误日志
    error_logger = logging.getLogger('error')
    error_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(LOG_DIR, f'error_{date_str}.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    error_handler.setFormatter(error_formatter)
    error_logger.addHandler(error_handler)
    
    logging.info(f"日志记录器配置完成。日志保存在 {LOG_DIR} 目录中，日志级别: {log_level_name}")
    
    return root_logger 