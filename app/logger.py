import logging
import os
import sys
from typing import Optional
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log messages based on level"""
    
    # ANSI color codes
    GREY = "\033[38;20m"
    YELLOW = "\033[33;20m"
    RED = "\033[31;20m"
    BOLD_RED = "\033[31;1m"
    CYAN = "\033[36;20m"
    GREEN = "\033[32;20m"
    BLUE = "\033[34;20m"
    MAGENTA = "\033[35;20m"
    RESET = "\033[0m"
    
    # Format for different log levels
    FORMATS = {
        logging.DEBUG: BLUE + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + RESET,
        logging.INFO: GREEN + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + RESET,
        logging.WARNING: YELLOW + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + RESET,
        logging.ERROR: RED + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + RESET,
        logging.CRITICAL: BOLD_RED + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + RESET
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a configured logger with colored console output and file output.
    
    Args:
        name (str): Name for the logger, typically __name__
        level (int, optional): Logging level. If None, uses LOG_LEVEL env var or defaults to INFO
        
    Returns:
        logging.Logger: Configured logger
    """
    if level is None:
        level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_name, logging.INFO)
    
    logger = logging.getLogger(name)
    
    # Only configure handlers if they don't exist already
    if not logger.handlers:
        logger.setLevel(level)
        
        # Create logs directory at project root
        # First get the project root directory (one level up from the app directory)
        project_root = Path(__file__).parents[1]
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Generate a log filename based on the module name
        # Replace dots with underscores to avoid directory nesting
        module_name = name.replace(".", "_")
        log_file = logs_dir / f"{module_name}.logs"
        
        # File handler with standard formatter
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter())
        logger.addHandler(console_handler)
        
        # Prevent propagation to the root logger
        logger.propagate = False
    
    return logger
