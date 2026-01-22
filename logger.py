"""Advanced logging system for CS:GO Trading Bot"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️ ',
        'WARNING': '⚠️ ',
        'ERROR': '❌',
        'CRITICAL': '🚨'
    }

    def format(self, record):
        """Format log record with colors and emojis"""
        # Add color
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}"
                f"{self.EMOJIS.get(levelname, '')} "
                f"{levelname}"
                f"{self.COLORS['RESET']}"
            )

        return super().format(record)


class TradingBotLogger:
    """Logger with file rotation and console output"""

    def __init__(
        self,
        name: str = 'csgo_bot',
        log_level: str = 'INFO',
        log_file: Optional[str] = None,
        max_bytes: int = 10485760,  # 10 MB
        backup_count: int = 5,
        console_enabled: bool = True,
        file_enabled: bool = True
    ):
        """
        Initialize logger

        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file
            max_bytes: Max size of log file before rotation
            backup_count: Number of backup files to keep
            console_enabled: Enable console logging
            file_enabled: Enable file logging
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.handlers.clear()  # Clear existing handlers

        # Console handler
        if console_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, log_level.upper()))
            console_formatter = ColoredFormatter(
                '%(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # File handler with rotation
        if file_enabled and log_file:
            # Create log directory
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, log_level.upper()))
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)

    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)

    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)

    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)

    def trade_signal(self, item: str, action: str, confidence: float, price: float):
        """Log trade signal"""
        emoji_map = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '🟡',
            'WAIT': '⚪'
        }

        emoji = emoji_map.get(action, '❓')
        self.info(
            f"{emoji} {action} Signal: {item} | "
            f"Price: ${price:.2f} | Confidence: {confidence:.0f}%"
        )

    def api_request(self, endpoint: str, status_code: int, duration: float):
        """Log API request"""
        if status_code == 200:
            self.debug(f"API Request: {endpoint} | Status: {status_code} | {duration:.2f}s")
        elif status_code == 429:
            self.warning(f"Rate limit hit: {endpoint}")
        else:
            self.error(f"API Error: {endpoint} | Status: {status_code}")

    def data_collected(self, item: str, count: int, avg_price: float):
        """Log data collection"""
        self.info(f"Collected {count} listings for {item} | Avg: ${avg_price:.2f}")

    def prediction(self, item: str, current: float, predicted: float, change_pct: float):
        """Log price prediction"""
        direction = "📈" if change_pct > 0 else "📉"
        self.info(
            f"{direction} Prediction for {item}: "
            f"${current:.2f} → ${predicted:.2f} ({change_pct:+.1f}%)"
        )

    def backtesting_result(self, profit: float, roi: float, trades: int):
        """Log backtesting results"""
        emoji = "💰" if profit > 0 else "💸"
        self.info(
            f"{emoji} Backtest: Profit ${profit:.2f} | "
            f"ROI: {roi:.1f}% | Trades: {trades}"
        )


# Global logger instance
_global_logger: Optional[TradingBotLogger] = None


def get_logger(
    name: str = 'csgo_bot',
    log_level: str = 'INFO',
    log_file: Optional[str] = None,
    **kwargs
) -> TradingBotLogger:
    """
    Get global logger instance

    Args:
        name: Logger name
        log_level: Logging level
        log_file: Path to log file
        **kwargs: Additional arguments for TradingBotLogger

    Returns:
        Global TradingBotLogger instance
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = TradingBotLogger(
            name=name,
            log_level=log_level,
            log_file=log_file,
            **kwargs
        )

    return _global_logger


def setup_logger_from_config(config) -> TradingBotLogger:
    """
    Setup logger from configuration

    Args:
        config: Config instance

    Returns:
        Configured TradingBotLogger instance
    """
    return get_logger(
        name='csgo_bot',
        log_level=config.get('logging.level', 'INFO'),
        log_file=config.get('logging.file_path') if config.get('logging.file_enabled') else None,
        max_bytes=config.get('logging.file_max_bytes', 10485760),
        backup_count=config.get('logging.file_backup_count', 5),
        console_enabled=config.get('logging.console_enabled', True),
        file_enabled=config.get('logging.file_enabled', True)
    )
