"""
Data validation utilities for NVMe health monitoring.

This module provides functions to validate device paths, data formats,
and other input parameters for the NVMe health monitoring utility.
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional


def validate_device_path(device_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate NVMe device path format and accessibility.
    
    Args:
        device_path: Device path to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not device_path:
        return False, "Device path cannot be empty"
    
    if not isinstance(device_path, str):
        return False, "Device path must be a string"
    
    nvme_pattern = r'^/dev/nvme\d+$'
    if not re.match(nvme_pattern, device_path):
        return False, f"Invalid device path format. Expected /dev/nvmeN, got: {device_path}"
    
    device_file = Path(device_path)
    if not device_file.exists():
        return False, f"Device path does not exist: {device_path}"
    
    if not device_file.is_block_device():
        return False, f"Path is not a block device: {device_path}"
    
    try:
        if not os.access(device_path, os.R_OK):
            return False, f"No read permission for device: {device_path}"
    except OSError as e:
        return False, f"Cannot access device: {e}"
    
    return True, None


def validate_device_paths(device_paths: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate multiple device paths.
    
    Args:
        device_paths: List of device paths to validate
        
    Returns:
        Tuple of (valid_paths: List[str], invalid_paths: List[str])
    """
    valid_paths = []
    invalid_paths = []
    
    for device_path in device_paths:
        is_valid, error_msg = validate_device_path(device_path)
        if is_valid:
            valid_paths.append(device_path)
        else:
            invalid_paths.append(f"{device_path}: {error_msg}")
    
    return valid_paths, invalid_paths


def validate_temperature_value(temperature: Any, unit: str = "celsius") -> Tuple[bool, Optional[str]]:
    """
    Validate temperature value and unit.
    
    Args:
        temperature: Temperature value to validate
        unit: Temperature unit ('celsius', 'kelvin', 'fahrenheit')
        
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if temperature is None:
        return True, None
    
    if not isinstance(temperature, (int, float)):
        return False, "Temperature must be a number"
    
    valid_units = ['celsius', 'kelvin', 'fahrenheit']
    if unit not in valid_units:
        return False, f"Invalid temperature unit. Must be one of: {', '.join(valid_units)}"
    
    if unit == "celsius":
        if temperature < -273.15:
            return False, "Temperature cannot be below absolute zero (-273.15°C)"
        if temperature > 200:
            return False, "Temperature too high for NVMe device (>200°C)"
    elif unit == "kelvin":
        if temperature < 0:
            return False, "Kelvin temperature cannot be negative"
        if temperature > 473.15:
            return False, "Temperature too high for NVMe device (>473.15K)"
    elif unit == "fahrenheit":
        if temperature < -459.67:
            return False, "Temperature cannot be below absolute zero (-459.67°F)"
        if temperature > 392:
            return False, "Temperature too high for NVMe device (>392°F)"
    
    return True, None


def validate_percentage_value(percentage: Any, field_name: str = "percentage") -> Tuple[bool, Optional[str]]:
    """
    Validate percentage value (0-100).
    
    Args:
        percentage: Percentage value to validate
        field_name: Name of the field for error messages
        
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if percentage is None:
        return True, None
    
    if not isinstance(percentage, (int, float)):
        return False, f"{field_name} must be a number"
    
    if not (0 <= percentage <= 100):
        return False, f"{field_name} must be between 0 and 100, got: {percentage}"
    
    return True, None


def validate_smart_data_structure(smart_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate SMART data structure and values.
    
    Args:
        smart_data: SMART data dictionary to validate
        
    Returns:
        Tuple of (is_valid: bool, validation_errors: List[str])
    """
    errors = []
    
    required_fields = [
        'critical_warning', 'temperature', 'available_spare',
        'available_spare_threshold', 'percentage_used'
    ]
    
    for field in required_fields:
        if field not in smart_data:
            errors.append(f"Missing required SMART field: {field}")
    
    if 'critical_warning' in smart_data:
        cw = smart_data['critical_warning']
        if not isinstance(cw, int) or not (0 <= cw <= 255):
            errors.append("critical_warning must be an integer between 0 and 255")
    
    if 'temperature' in smart_data:
        temp = smart_data['temperature']
        if temp is not None:
            is_valid, error_msg = validate_temperature_value(temp, "kelvin")
            if not is_valid:
                errors.append(f"Invalid temperature: {error_msg}")
    
    percentage_fields = ['available_spare', 'available_spare_threshold', 'percentage_used']
    for field in percentage_fields:
        if field in smart_data:
            is_valid, error_msg = validate_percentage_value(smart_data[field], field)
            if not is_valid:
                errors.append(error_msg)
    
    numeric_fields = [
        'data_units_read', 'data_units_written', 'host_read_commands',
        'host_write_commands', 'controller_busy_time', 'power_cycles',
        'power_on_hours', 'unsafe_shutdowns', 'media_errors', 'num_err_log_entries'
    ]
    
    for field in numeric_fields:
        if field in smart_data:
            value = smart_data[field]
            if value is not None and (not isinstance(value, (int, float)) or value < 0):
                errors.append(f"{field} must be a non-negative number")
    
    return len(errors) == 0, errors


def validate_error_log_entry(error_entry: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate error log entry structure.
    
    Args:
        error_entry: Error log entry dictionary to validate
        
    Returns:
        Tuple of (is_valid: bool, validation_errors: List[str])
    """
    errors = []
    
    required_fields = ['error_count', 'sqid', 'cmdid', 'status_field']
    for field in required_fields:
        if field not in error_entry:
            errors.append(f"Missing required error log field: {field}")
    
    integer_fields = [
        'error_count', 'sqid', 'cmdid', 'status_field', 'parm_error_location',
        'lba', 'nsid', 'vs', 'cs', 'sct', 'sc'
    ]
    
    for field in integer_fields:
        if field in error_entry:
            value = error_entry[field]
            if value is not None and not isinstance(value, int):
                errors.append(f"{field} must be an integer")
            elif value is not None and value < 0:
                errors.append(f"{field} must be non-negative")
    
    boolean_fields = ['more', 'dnr']
    for field in boolean_fields:
        if field in error_entry:
            value = error_entry[field]
            if value is not None and not isinstance(value, bool):
                errors.append(f"{field} must be a boolean")
    
    if 'timestamp' in error_entry:
        timestamp = error_entry['timestamp']
        if timestamp is not None and not isinstance(timestamp, str):
            errors.append("timestamp must be a string")
    
    return len(errors) == 0, errors


def validate_output_format_type(format_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate output format type.
    
    Args:
        format_type: Output format type to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    valid_formats = ['json', 'csv', 'text', 'yaml', 'xml']
    
    if not isinstance(format_type, str):
        return False, "Format type must be a string"
    
    if format_type.lower() not in valid_formats:
        return False, f"Invalid format type. Must be one of: {', '.join(valid_formats)}"
    
    return True, None


def validate_file_path_writable(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a file path is writable.
    
    Args:
        file_path: File path to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not isinstance(file_path, str):
        return False, "File path must be a string"
    
    if not file_path.strip():
        return False, "File path cannot be empty"
    
    path = Path(file_path)
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        return False, f"Cannot create parent directory: {e}"
    
    if path.exists():
        if not path.is_file():
            return False, f"Path exists but is not a file: {file_path}"
        
        if not os.access(path, os.W_OK):
            return False, f"No write permission for file: {file_path}"
    else:
        try:
            path.touch()
            path.unlink()
        except (OSError, PermissionError) as e:
            return False, f"Cannot write to file path: {e}"
    
    return True, None


def validate_monitoring_interval(interval: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate monitoring interval value.
    
    Args:
        interval: Interval value to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not isinstance(interval, (int, float)):
        return False, "Monitoring interval must be a number"
    
    if interval <= 0:
        return False, "Monitoring interval must be positive"
    
    if interval < 1:
        return False, "Monitoring interval should be at least 1 second"
    
    if interval > 86400:
        return False, "Monitoring interval cannot exceed 24 hours (86400 seconds)"
    
    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe filesystem usage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    if not isinstance(filename, str):
        return "unknown_file"
    
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    sanitized = re.sub(r'[^\w\-_.]', '_', sanitized)
    
    sanitized = re.sub(r'_+', '_', sanitized)
    
    sanitized = sanitized.strip('_.')
    
    if not sanitized or sanitized in ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]:
        sanitized = f"file_{sanitized}"
    
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255-len(ext)] + ext
    
    return sanitized or "unknown_file"
