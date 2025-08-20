"""
Testing utilities for NVMe health monitoring.

This module provides functions to generate mock data and validate output
formats for testing the NVMe health monitoring utility.
"""

import random
import json
import csv
from io import StringIO
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path

from ..models.health_metrics import (
    HealthStatus, SelfTestType, SelfTestResult, TemperatureUnit
)


def generate_mock_smart_data(device_path: str, health_status: str = "good") -> Dict[str, Any]:
    """
    Generate mock SMART data for testing.
    
    Args:
        device_path: Device path for mock data
        health_status: Health status ('good', 'warning', 'critical')
        
    Returns:
        Mock SMART data dictionary
    """
    if health_status == "good":
        temp_celsius = random.uniform(35.0, 50.0)
    elif health_status == "warning":
        temp_celsius = random.uniform(65.0, 75.0)
    elif health_status == "critical":
        temp_celsius = random.uniform(75.0, 85.0)
    else:
        temp_celsius = 45.0
    
    if health_status == "good":
        health_enum = "good"
    elif health_status == "warning":
        health_enum = "warning"
    elif health_status == "critical":
        health_enum = "critical"
    else:
        health_enum = "good"
    
    base_data = {
        "device_path": device_path,
        "critical_warning": 0,
        "temperature": {
            "celsius": temp_celsius,
            "fahrenheit": (temp_celsius * 9/5) + 32,
            "kelvin": temp_celsius + 273.15,
            "sensor_name": "Composite"
        },
        "available_spare": 100.0,
        "available_spare_threshold": 10.0,
        "percentage_used": 1.0,
        "data_units_read": random.randint(1000000, 10000000),
        "data_units_written": random.randint(500000, 5000000),
        "host_read_commands": random.randint(10000000, 100000000),
        "host_write_commands": random.randint(5000000, 50000000),
        "controller_busy_time": random.randint(100, 10000),
        "power_cycles": random.randint(100, 1000),
        "power_on_hours": random.randint(1000, 50000),
        "unsafe_shutdowns": random.randint(0, 10),
        "media_errors": 0,
        "error_log_entries": 0,
        "health_status": health_enum
    }
    
    if health_status == "warning":
        base_data.update({
            "available_spare": 12.0,  # Fixed value to ensure warning status
            "percentage_used": 85.0,
            "media_errors": 3,
            "error_log_entries": 5
        })
    elif health_status == "critical":
        base_data.update({
            "critical_warning": 1,  # Fixed value to ensure critical status
            "available_spare": 3.0,
            "percentage_used": 97.0,
            "media_errors": 25,
            "error_log_entries": 50,
            "unsafe_shutdowns": 20
        })
    
    return base_data


def generate_mock_error_logs(device_path: str, error_count: int = 0) -> List[Dict[str, Any]]:
    """
    Generate mock error log entries for testing.
    
    Args:
        device_path: Device path for mock data
        error_count: Number of error entries to generate
        
    Returns:
        List of mock error log entries
    """
    if error_count == 0:
        return []
    
    error_types = [
        "Data Integrity Error",
        "Media Error", 
        "Internal Error",
        "Command Timeout",
        "Write Fault",
        "Read Error",
        "Controller Error"
    ]
    
    severities = ["info", "warning", "error", "critical"]
    
    errors = []
    base_time = datetime.utcnow() - timedelta(days=30)
    
    for i in range(error_count):
        error_time = base_time + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        error = {
            "error_count": i + 1,
            "submission_queue_id": random.randint(0, 15),
            "command_id": random.randint(1, 65535),
            "status_field": f"0x{random.randint(0, 255):02x}",
            "parameter_error_location": f"0x{random.randint(0, 255):02x}",
            "lba": random.randint(0, 1000000000),
            "namespace_id": random.randint(1, 4),
            "vendor_specific_info": f"0x{random.randint(0, 255):02x}",
            "transport_type": "pcie",
            "command_specific": random.randint(0, 255),
            "transport_address": f"0000:{random.randint(1,99):02d}:00.0",
            "transport_service_id": "none",
            "subsystem_nqn": f"nqn.2014-08.org.nvmexpress:uuid:{random.randint(1000,9999)}",
            "timestamp": error_time,
            "error_type": random.choice(error_types),
            "severity": random.choice(severities),
            "description": f"Mock error entry {i + 1} for testing"
        }
        
        errors.append(error)
    
    return errors


def generate_mock_self_test_data(device_path: str, test_count: int = 3) -> List[Dict[str, Any]]:
    """
    Generate mock self-test data for testing.
    
    Args:
        device_path: Device path for mock data
        test_count: Number of test entries to generate
        
    Returns:
        List of mock self-test entries
    """
    test_types = [SelfTestType.SHORT, SelfTestType.EXTENDED, SelfTestType.VENDOR_SPECIFIC]
    test_results = [SelfTestResult.COMPLETED_WITHOUT_ERROR, SelfTestResult.ABORTED_BY_HOST, SelfTestResult.UNKNOWN_FAILURE]
    
    tests = []
    base_time = datetime.utcnow() - timedelta(days=90)
    
    for i in range(test_count):
        test_time = base_time + timedelta(days=random.randint(0, 90))
        
        test = {
            "test_type": random.choice(test_types),
            "test_result": random.choice(test_results),
            "power_on_hours": random.randint(1000, 50000),
            "failing_lba": random.randint(0, 1000000) if random.choice([True, False]) else None,
            "status_code": str(random.randint(0, 255)),
            "segment_number": random.randint(0, 15) if random.choice([True, False]) else None,
            "valid_diagnostic_info": random.choice([True, False]),
            "timestamp": test_time
        }
        
        tests.append(test)
    
    return tests


def generate_mock_device_info(device_path: str) -> Dict[str, Any]:
    """
    Generate mock device information for testing.
    
    Args:
        device_path: Device path for mock data
        
    Returns:
        Mock device information dictionary
    """
    models = [
        "Samsung SSD 980 PRO 1TB",
        "WD Black SN850 2TB", 
        "Crucial P5 Plus 1TB",
        "Intel SSD 670p 512GB",
        "Seagate FireCuda 530 2TB"
    ]
    
    model = random.choice(models)
    total_capacity = random.choice([256, 512, 1024, 2048, 4096]) * 1024**3  # Convert GB to bytes
    
    return {
        "device_path": device_path,
        "controller_info": {
            "device_path": device_path,
            "model_number": model,
            "serial_number": f"S{random.randint(100000000000, 999999999999)}",
            "firmware_revision": f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "pci_vendor_id": f"0x{random.randint(0x1000, 0xFFFF):04x}",
            "pci_subsystem_vendor_id": f"0x{random.randint(0x1000, 0xFFFF):04x}",
            "ieee_oui_identifier": f"0x{random.randint(0x000000, 0xFFFFFF):06x}",
            "total_nvm_capacity": total_capacity,
            "unallocated_nvm_capacity": random.randint(0, total_capacity // 10),
            "controller_id": random.randint(1, 65535),
            "version": f"{random.randint(1, 2)}.{random.randint(0, 4)}",
            "rtd3_resume_latency": random.randint(1000, 100000),
            "rtd3_entry_latency": random.randint(1000, 100000),
            "optional_admin_commands": [f"cmd_{i}" for i in range(random.randint(1, 5))],
            "optional_nvm_commands": [f"nvm_cmd_{i}" for i in range(random.randint(1, 5))],
            "maximum_data_transfer_size": random.randint(4, 128)
        },
        "namespaces": [
            {
                "namespace_id": 1,
                "device_path": f"{device_path}n1",
                "size": random.randint(1000000000, 4000000000),
                "capacity": random.randint(1000000000, 4000000000),
                "utilization": random.randint(500000000, 2000000000),
                "formatted_lba_size": 512,
                "metadata_size": 0,
                "relative_performance": "Best"
            }
        ]
    }


def create_test_device_environment() -> Dict[str, Any]:
    """
    Create mock device environment for testing.
    
    Returns:
        Dictionary with mock device setup
    """
    devices = ["/dev/nvme0", "/dev/nvme1", "/dev/nvme2"]
    
    environment = {
        "devices": {},
        "temp_files": [],
        "cleanup_functions": []
    }
    
    for device in devices:
        health_status = random.choice(["good", "warning", "critical"])
        error_count = 0 if health_status == "good" else random.randint(1, 20)
        
        environment["devices"][device] = {
            "device_info": generate_mock_device_info(device),
            "smart_data": generate_mock_smart_data(device, health_status),
            "error_logs": generate_mock_error_logs(device, error_count),
            "self_test_data": generate_mock_self_test_data(device)
        }
    
    return environment


def validate_output_format(output_data: str, format_type: str) -> bool:
    """
    Validate output format correctness.
    
    Args:
        output_data: Generated output data
        format_type: Expected format ('json', 'csv', 'text')
        
    Returns:
        True if format is valid
    """
    try:
        if format_type == 'json':
            parsed = json.loads(output_data)
            
            if isinstance(parsed, dict):
                required_fields = ['device_info', 'timestamp']
                if 'devices' in parsed:
                    if not isinstance(parsed['devices'], list):
                        return False
                    if parsed['devices']:
                        sample_device = parsed['devices'][0]
                        return all(field in sample_device for field in required_fields)
                else:
                    return all(field in parsed for field in required_fields)
            
            return isinstance(parsed, (dict, list))
        
        elif format_type == 'csv':
            reader = csv.reader(StringIO(output_data))
            rows = list(reader)
            
            if len(rows) < 2:
                return False
            
            headers = rows[0]
            if not headers:
                return False
            
            for row in rows[1:]:
                if len(row) != len(headers):
                    return False
            
            return True
        
        elif format_type == 'text':
            lines = output_data.strip().split('\n')
            
            if not lines:
                return False
            
            has_headers = any('=' in line for line in lines[:5])
            has_content = len([line for line in lines if line.strip()]) > 3
            
            return has_headers and has_content
        
        else:
            return False
            
    except Exception:
        return False


def create_mock_health_snapshot(device_path: str, health_status: str = "good") -> Dict[str, Any]:
    """
    Create a complete mock health snapshot for testing.
    
    Args:
        device_path: Device path for mock data
        health_status: Health status ('good', 'warning', 'critical')
        
    Returns:
        Complete mock health snapshot dictionary
    """
    error_count = 0 if health_status == "good" else random.randint(1, 20)
    
    snapshot = {
        "device_info": generate_mock_device_info(device_path),
        "smart_data": generate_mock_smart_data(device_path, health_status),
        "error_logs": generate_mock_error_logs(device_path, error_count),
        "self_test_log": {
            "device_path": device_path,
            "entries": generate_mock_self_test_data(device_path)
        },
        "timestamp": datetime.utcnow(),
        "collection_duration_ms": random.uniform(500.0, 3000.0)
    }
    
    return snapshot


def generate_test_config() -> Dict[str, Any]:
    """
    Generate test configuration for testing.
    
    Returns:
        Test configuration dictionary
    """
    return {
        "nvme_cli": {
            "command_path": "nvme",
            "timeout_seconds": 10,
            "retry_attempts": 1
        },
        "thresholds": {
            "temperature": {
                "warning_celsius": 60,
                "critical_celsius": 80
            },
            "available_spare": {
                "warning_percent": 15,
                "critical_percent": 5
            }
        },
        "output": {
            "default_format": "json",
            "pretty_print": True
        },
        "logging": {
            "level": "DEBUG"
        }
    }
