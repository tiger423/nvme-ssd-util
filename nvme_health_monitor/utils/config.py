"""
Configuration management functions for NVMe health monitoring.

This module provides functions to load, validate, and manage configuration
settings for the NVMe health monitoring utility.
"""

import json
import yaml
import os
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path


def load_default_config() -> Dict[str, Any]:
    """
    Load default configuration settings.
    
    Returns:
        Dictionary with default configuration values
    """
    return {
        "nvme_cli": {
            "command_path": "nvme",
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_delay": 1.0
        },
        "thresholds": {
            "temperature": {
                "warning_celsius": 70,
                "critical_celsius": 85
            },
            "available_spare": {
                "warning_percent": 10,
                "critical_percent": 5
            },
            "percentage_used": {
                "warning_percent": 80,
                "critical_percent": 95
            },
            "media_errors": {
                "warning_count": 1,
                "critical_count": 10
            },
            "error_log_entries": {
                "warning_count": 5,
                "critical_count": 20
            }
        },
        "health_scoring": {
            "weights": {
                "temperature": 0.2,
                "spare_capacity": 0.3,
                "wear_level": 0.25,
                "error_rate": 0.25
            },
            "base_score": 100
        },
        "monitoring": {
            "default_interval_seconds": 300,
            "max_history_entries": 1000,
            "enable_trend_analysis": True,
            "anomaly_detection_threshold": 2.0
        },
        "output": {
            "default_format": "json",
            "include_timestamps": True,
            "pretty_print": True,
            "exclude_null_values": True
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file_rotation": {
                "max_bytes": 10485760,
                "backup_count": 5
            }
        },
        "devices": {
            "auto_discover": True,
            "include_patterns": ["/dev/nvme*"],
            "exclude_patterns": [],
            "require_admin": False
        }
    }


def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from JSON/YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file not found
        ValueError: If config file is invalid
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if config_file.suffix.lower() in ['.yaml', '.yml']:
            config = yaml.safe_load(content)
        elif config_file.suffix.lower() == '.json':
            config = json.loads(content)
        else:
            try:
                config = yaml.safe_load(content)
            except yaml.YAMLError:
                try:
                    config = json.loads(content)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Unable to parse configuration file as JSON or YAML: {e}")
        
        if not isinstance(config, dict):
            raise ValueError("Configuration file must contain a dictionary/object at root level")
        
        default_config = load_default_config()
        merged_config = _merge_configs(default_config, config)
        
        is_valid, errors = validate_config(merged_config)
        if not is_valid:
            raise ValueError(f"Invalid configuration: {'; '.join(errors)}")
        
        return merged_config
        
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise ValueError(f"Failed to parse configuration file: {e}")
    except Exception as e:
        raise ValueError(f"Error loading configuration file: {e}")


def validate_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid: bool, validation_errors: List[str])
    """
    errors = []
    
    required_sections = ['nvme_cli', 'thresholds', 'health_scoring', 'monitoring', 'output', 'logging', 'devices']
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required configuration section: {section}")
    
    if 'nvme_cli' in config:
        nvme_cli = config['nvme_cli']
        if 'timeout_seconds' in nvme_cli:
            if not isinstance(nvme_cli['timeout_seconds'], (int, float)) or nvme_cli['timeout_seconds'] <= 0:
                errors.append("nvme_cli.timeout_seconds must be a positive number")
        
        if 'retry_attempts' in nvme_cli:
            if not isinstance(nvme_cli['retry_attempts'], int) or nvme_cli['retry_attempts'] < 0:
                errors.append("nvme_cli.retry_attempts must be a non-negative integer")
    
    if 'thresholds' in config:
        thresholds = config['thresholds']
        
        if 'temperature' in thresholds:
            temp = thresholds['temperature']
            if 'warning_celsius' in temp and 'critical_celsius' in temp:
                if temp['warning_celsius'] >= temp['critical_celsius']:
                    errors.append("temperature.warning_celsius must be less than critical_celsius")
        
        for threshold_type in ['available_spare', 'percentage_used']:
            if threshold_type in thresholds:
                thresh = thresholds[threshold_type]
                for level in ['warning_percent', 'critical_percent']:
                    if level in thresh:
                        value = thresh[level]
                        if not isinstance(value, (int, float)) or not (0 <= value <= 100):
                            errors.append(f"{threshold_type}.{level} must be between 0 and 100")
    
    if 'health_scoring' in config:
        scoring = config['health_scoring']
        if 'weights' in scoring:
            weights = scoring['weights']
            total_weight = sum(weights.values())
            if abs(total_weight - 1.0) > 0.01:
                errors.append(f"health_scoring.weights must sum to 1.0 (current sum: {total_weight})")
    
    if 'monitoring' in config:
        monitoring = config['monitoring']
        if 'default_interval_seconds' in monitoring:
            interval = monitoring['default_interval_seconds']
            if not isinstance(interval, (int, float)) or interval <= 0:
                errors.append("monitoring.default_interval_seconds must be a positive number")
    
    if 'output' in config:
        output = config['output']
        if 'default_format' in output:
            valid_formats = ['json', 'csv', 'text', 'yaml']
            if output['default_format'] not in valid_formats:
                errors.append(f"output.default_format must be one of: {', '.join(valid_formats)}")
    
    if 'logging' in config:
        logging_config = config['logging']
        if 'level' in logging_config:
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if logging_config['level'] not in valid_levels:
                errors.append(f"logging.level must be one of: {', '.join(valid_levels)}")
    
    return len(errors) == 0, errors


def get_smart_thresholds(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract SMART attribute thresholds from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary mapping SMART attributes to threshold values
    """
    thresholds = config.get('thresholds', {})
    
    smart_thresholds = {}
    
    for attribute in ['temperature', 'available_spare', 'percentage_used', 'media_errors', 'error_log_entries']:
        if attribute in thresholds:
            smart_thresholds[attribute] = thresholds[attribute].copy()
        else:
            default_config = load_default_config()
            smart_thresholds[attribute] = default_config['thresholds'].get(attribute, {})
    
    return smart_thresholds


def update_thresholds(config: Dict[str, Any], attribute: str, warning: Any, critical: Any) -> Dict[str, Any]:
    """
    Update threshold values in configuration.
    
    Args:
        config: Configuration dictionary
        attribute: SMART attribute name
        warning: Warning threshold value
        critical: Critical threshold value
        
    Returns:
        Updated configuration dictionary
    """
    updated_config = config.copy()
    
    if 'thresholds' not in updated_config:
        updated_config['thresholds'] = {}
    
    if attribute not in updated_config['thresholds']:
        updated_config['thresholds'][attribute] = {}
    
    if attribute == 'temperature':
        if not isinstance(warning, (int, float)) or not isinstance(critical, (int, float)):
            raise ValueError("Temperature thresholds must be numeric")
        if warning >= critical:
            raise ValueError("Warning threshold must be less than critical threshold for temperature")
        
        updated_config['thresholds'][attribute]['warning_celsius'] = warning
        updated_config['thresholds'][attribute]['critical_celsius'] = critical
        
    elif attribute in ['available_spare', 'percentage_used']:
        if not isinstance(warning, (int, float)) or not isinstance(critical, (int, float)):
            raise ValueError("Percentage thresholds must be numeric")
        if not (0 <= warning <= 100) or not (0 <= critical <= 100):
            raise ValueError("Percentage thresholds must be between 0 and 100")
        
        updated_config['thresholds'][attribute]['warning_percent'] = warning
        updated_config['thresholds'][attribute]['critical_percent'] = critical
        
    elif attribute in ['media_errors', 'error_log_entries']:
        if not isinstance(warning, int) or not isinstance(critical, int):
            raise ValueError("Error count thresholds must be integers")
        if warning < 0 or critical < 0:
            raise ValueError("Error count thresholds must be non-negative")
        if warning > critical:
            raise ValueError("Warning threshold must be less than or equal to critical threshold for error counts")
        
        updated_config['thresholds'][attribute]['warning_count'] = warning
        updated_config['thresholds'][attribute]['critical_count'] = critical
    
    else:
        raise ValueError(f"Unknown threshold attribute: {attribute}")
    
    is_valid, errors = validate_config(updated_config)
    if not is_valid:
        raise ValueError(f"Updated configuration is invalid: {'; '.join(errors)}")
    
    return updated_config


def _merge_configs(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge user configuration with default configuration.
    
    Args:
        default: Default configuration dictionary
        user: User configuration dictionary
        
    Returns:
        Merged configuration dictionary
    """
    merged = default.copy()
    
    for key, value in user.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_configs(merged[key], value)
        else:
            merged[key] = value
    
    return merged
