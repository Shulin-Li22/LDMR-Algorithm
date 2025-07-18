"""
日志管理器
提供统一的日志记录功能
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'SUCCESS': '\033[92m',  # 亮绿色
        'ENDC': '\033[0m'       # 结束颜色
    }
    
    def format(self, record):
        if hasattr(record, 'color'):
            color = record.color
        else:
            color = self.COLORS.get(record.levelname, '')
        
        if color:
            record.levelname = f"{color}{record.levelname}{self.COLORS['ENDC']}"
            record.msg = f"{color}{record.msg}{self.COLORS['ENDC']}"
        
        return super().format(record)


class LDMRLogger:
    """LDMR专用日志记录器"""
    
    def __init__(self, name: str = "LDMR", config: Optional[dict] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 控制台处理器
        if self.config.get('console_output', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self._get_log_level())
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # 文件处理器
        if self.config.get('save_logs', True):
            log_dir = Path(self.config.get('log_dir', 'logs'))
            log_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"ldmr_run_{timestamp}.log"
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def _get_log_level(self) -> int:
        """获取日志级别"""
        level_str = self.config.get('log_level', 'INFO').upper()
        return getattr(logging, level_str, logging.INFO)
    
    def debug(self, message: str):
        """调试信息"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """一般信息"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """警告信息"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """错误信息"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """严重错误"""
        self.logger.critical(message)
    
    def success(self, message: str):
        """成功信息（自定义级别）"""
        record = self.logger.makeRecord(
            self.logger.name, logging.INFO, "", 0, message, (), None
        )
        record.color = ColoredFormatter.COLORS['SUCCESS']
        self.logger.handle(record)


# 全局日志记录器实例
_logger = None

def setup_logger(config: Optional[dict] = None) -> LDMRLogger:
    """设置全局日志记录器"""
    global _logger
    _logger = LDMRLogger("LDMR", config)
    return _logger

def get_logger() -> LDMRLogger:
    """获取全局日志记录器"""
    global _logger
    if _logger is None:
        _logger = LDMRLogger("LDMR")
    return _logger


class ProgressIndicator:
    """进度指示器"""
    
    def __init__(self, total_steps: int, logger: Optional[LDMRLogger] = None):
        self.total_steps = total_steps
        self.current_step = 0
        self.logger = logger or get_logger()
        self.start_time = datetime.now()
    
    def update(self, step_name: str, increment: int = 1):
        """更新进度"""
        self.current_step += increment
        progress = min(self.current_step / self.total_steps * 100, 100)
        
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        
        if progress > 0:
            estimated_total = elapsed_time / (progress / 100)
            remaining_time = estimated_total - elapsed_time
            
            self.logger.info(
                f"[{progress:5.1f}%] {step_name} "
                f"(剩余: {remaining_time:.1f}s)"
            )
        else:
            self.logger.info(f"[{progress:5.1f}%] {step_name}")
    
    def finish(self, final_message: str = "完成"):
        """完成进度"""
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        self.logger.success(f"[100.0%] {final_message} (总耗时: {elapsed_time:.1f}s)")


def log_exception(logger: LDMRLogger, exception: Exception, context: str = ""):
    """记录异常信息"""
    import traceback
    
    error_msg = f"异常发生"
    if context:
        error_msg += f" in {context}"
    error_msg += f": {str(exception)}"
    
    logger.error(error_msg)
    logger.debug(f"异常详情:\n{traceback.format_exc()}")
