"""
Logging configuration functions for NVMe health monitoring.

This module provides functions to set up and configure logging for the
NVMe health monitoring utility, including device-specific loggers.
"""

import logging
import logging.handlers
import os
import re
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from ..models.health_metrics import HealthSnapshot


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('nvme_health_monitor')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    if logger.handlers:
        logger.handlers.clear()
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.propagate = False
    
    return logger


def create_device_logger(device_path: str) -> logging.Logger:
    """
    Create device-specific logger.
    
    Args:
        device_path: NVMe device path
        
    Returns:
        Device-specific logger instance
    """
    sanitized_device = _sanitize_device_path(device_path)
    logger_name = f'nvme_health_monitor.device.{sanitized_device}'
    
    logger = logging.getLogger(logger_name)
    
    if logger.handlers:
        return logger
    
    parent_logger = logging.getLogger('nvme_health_monitor')
    logger.setLevel(parent_logger.level)
    
    device_formatter = logging.Formatter(
        f'%(asctime)s - {device_path} - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(parent_logger.level)
    console_handler.setFormatter(device_formatter)
    logger.addHandler(console_handler)
    
    for handler in parent_logger.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            log_dir = Path(handler.baseFilename).parent
            device_log_file = log_dir / f'device_{sanitized_device}.log'
            
            device_file_handler = logging.handlers.RotatingFileHandler(
                device_log_file,
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding='utf-8'
            )
            device_file_handler.setLevel(logging.DEBUG)
            device_file_handler.setFormatter(device_formatter)
            logger.addHandler(device_file_handler)
            break
    
    logger.propagate = False
    
    return logger


def log_command_execution(logger: logging.Logger, command: list, result: Dict[str, Any]) -> None:
    """
    Log nvme-cli command execution details.
    
    Args:
        logger: Logger instance
        command: Command arguments list
        result: Command execution result
    """
    sanitized_command = _sanitize_command(command)
    
    if result.get('success', False):
        execution_time = result.get('execution_time', 0)
        logger.debug(f"Command executed successfully: {' '.join(sanitized_command)} (took {execution_time:.3f}s)")
        
        if result.get('stdout'):
            output_size = len(result['stdout'])
            logger.debug(f"Command output size: {output_size} bytes")
    else:
        error_msg = result.get('error', 'Unknown error')
        return_code = result.get('return_code', -1)
        
        logger.error(f"Command failed: {' '.join(sanitized_command)}")
        logger.error(f"Return code: {return_code}")
        logger.error(f"Error: {error_msg}")
        
        if result.get('stderr'):
            logger.error(f"Stderr: {result['stderr']}")


def log_health_collection(logger: logging.Logger, device_path: str, snapshot: HealthSnapshot) -> None:
    """
    Log health data collection summary.
    
    Args:
        logger: Logger instance
        device_path: Device path
        snapshot: Collected health snapshot
    """
    logger.info(f"Health data collected for {device_path}")
    
    if snapshot.smart_data:
        smart = snapshot.smart_data
        logger.info(f"SMART status: {smart.health_status.value}")
        
        if smart.temperature:
            logger.info(f"Temperature: {smart.temperature.celsius}°C")
        
        if smart.available_spare_percent is not None:
            logger.info(f"Available spare: {smart.available_spare_percent}%")
        
        if smart.percentage_used is not None:
            logger.info(f"Percentage used: {smart.percentage_used}%")
        
        if smart.critical_warning and smart.critical_warning > 0:
            logger.warning(f"Critical warning detected: {smart.critical_warning}")
        
        if smart.media_errors and smart.media_errors > 0:
            logger.warning(f"Media errors detected: {smart.media_errors}")
    
    error_count = len(snapshot.error_logs) if snapshot.error_logs else 0
    if error_count > 0:
        logger.warning(f"Error log entries: {error_count}")
        
        recent_errors = 0
        if snapshot.error_logs:
            cutoff_time = datetime.utcnow().timestamp() - (7 * 24 * 3600)
            recent_errors = sum(1 for log in snapshot.error_logs 
                              if log.timestamp and log.timestamp.timestamp() > cutoff_time)
        
        if recent_errors > 0:
            logger.warning(f"Recent errors (7 days): {recent_errors}")
    
    if snapshot.self_test_log and snapshot.self_test_log.entries:
        latest_test = snapshot.self_test_log.entries[0]
        logger.info(f"Latest self-test: {latest_test.test_type.value} - {latest_test.result.value}")
    
    collection_time = snapshot.timestamp
    logger.debug(f"Collection completed at {collection_time.isoformat()}")


def configure_cli_logging(verbose: int) -> None:
    """
    Configure logging for CLI usage based on verbosity level.
    
    Args:
        verbose: Verbosity level (0=ERROR, 1=WARNING, 2=INFO, 3=DEBUG)
    """
    level_map = {
        0: 'ERROR',
        1: 'WARNING', 
        2: 'INFO',
        3: 'DEBUG'
    }
    
    log_level = level_map.get(verbose, 'INFO')
    
    logger = setup_logging(log_level)
    
    if verbose == 0:
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(logging.ERROR)
    
    logger.info(f"Logging configured with level: {log_level}")


def create_monitoring_logger(output_dir: str) -> logging.Logger:
    """
    Create logger for continuous monitoring with timestamped files.
    
    Args:
        output_dir: Directory for log files
        
    Returns:
        Monitoring logger instance
    """
    logger_name = 'nvme_health_monitor.monitoring'
    logger = logging.getLogger(logger_name)
    
    if logger.handlers:
        logger.handlers.clear()
    
    logger.setLevel(logging.INFO)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = output_path / f'monitoring_{timestamp}.log'
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=50 * 1024 * 1024,
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.propagate = False
    
    return logger


def _sanitize_device_path(device_path: str) -> str:
    """
    Sanitize device path for use in filenames and logger names.
    
    Args:
        device_path: Original device path
        
    Returns:
        Sanitized device path
    """
    sanitized = re.sub(r'[^\w\-_.]', '_', device_path)
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')
    
    return sanitized or 'unknown_device'


def _sanitize_command(command: list) -> list:
    """
    Sanitize command arguments for logging (remove sensitive data).
    
    Args:
        command: Original command arguments
        
    Returns:
        Sanitized command arguments
    """
    sanitized = []
    
    for arg in command:
        if isinstance(arg, str):
            if any(sensitive in arg.lower() for sensitive in ['password', 'key', 'secret', 'token']):
                sanitized.append('[REDACTED]')
            else:
                sanitized.append(arg)
        else:
            sanitized.append(str(arg))
    
    return sanitized
