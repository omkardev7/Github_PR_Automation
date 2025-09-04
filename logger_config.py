import logging
import os
from datetime import datetime


def setup_logger(name: str) -> logging.Logger:
    
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger
    
    log_file = os.path.join(log_dir, f"code_review_agent_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def log_function_start(logger: logging.Logger, function_name: str, **kwargs):
  
    separator = "=" * 80
    logger.info(f"\n{separator}")
    logger.info(f"STARTING FUNCTION: {function_name}")
    if kwargs:
        for key, value in kwargs.items():
            logger.info(f"  {key}: {value}")
    logger.info(separator)


def log_function_end(logger: logging.Logger, function_name: str, success: bool = True, **kwargs):
    
    status = "SUCCESS" if success else "FAILURE"
    logger.info(f"ENDING FUNCTION: {function_name} - {status}")
    if kwargs:
        for key, value in kwargs.items():
            logger.info(f"  {key}: {value}")
    separator = "=" * 80
    logger.info(separator)


def log_step(logger: logging.Logger, step_name: str, **kwargs):
    
    logger.info(f"STEP: {step_name}")
    if kwargs:
        for key, value in kwargs.items():
            logger.info(f"  {key}: {value}")