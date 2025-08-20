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
    base_data = {
        "critical_warning": 0,
        "temperature": 318,
        "available_spare": 100,
        "available_spare_threshold": 10,
        "percentage_used": 1,
        "data_units_read": random.randint(1000000, 10000000),
        "data_units_written": random.randint(500000, 5000000),
        "host_read_commands": random.randint(10000000, 100000000),
        "host_write_commands": random.randint(5000000, 50000000),
        "controller_busy_time": random.randint(100, 10000),
        "power_cycles": random.randint(100, 1000),
        "power_on_hours": random.randint(1000, 50000),
        "unsafe_shutdowns": random.randint(0, 10),
        "media_errors": 0,
        "num_err_log_entries": 0,
        "warning_temp_time": 0,
        "critical_comp_time": 0
    }
    
    if health_status == "warning":
        base_data.update({
            "temperature": random.randint(343, 358),
            "available_spare": random.randint(5, 15),
            "percentage_used": random.randint(80, 94),
            "media_errors": random.randint(1, 5),
            "num_err_log_entries": random.randint(1, 10),
            "warning_temp_time": random.randint(1, 100)
        })
    elif health_status == "critical":
        base_data.update({
            "critical_warning": random.randint(1, 7),
            "temperature": random.randint(358, 373),
            "available_spare": random.randint(0, 5),
            "percentage_used": random.randint(95, 100),
            "media_errors": random.randint(10, 100),
            "num_err_log_entries": random.randint(20, 200),
            "unsafe_shutdowns": random.randint(10, 50),
            "critical_comp_time": random.randint(1, 1000)
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
            "sqid": random.randint(0, 15),
            "cmdid": random.randint(1, 65535),
            "status_field": random.randint(0, 255),
            "parm_error_location": random.randint(0, 255),
            "lba": random.randint(0, 1000000000),
            "nsid": random.randint(1, 4),
            "vs": random.randint(0, 255),
            "trtype": "pcie",
            "cs": random.randint(0, 255),
            "sct": random.randint(0, 7),
            "sc": random.randint(0, 255),
            "more": False,
            "dnr": random.choice([True, False]),
            "timestamp": error_time.isoformat(),
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
    test_results = [SelfTestResult.COMPLETED, SelfTestResult.ABORTED, SelfTestResult.FAILED]
    
    tests = []
    base_time = datetime.utcnow() - timedelta(days=90)
    
    for i in range(test_count):
        test_time = base_time + timedelta(days=random.randint(0, 90))
        
        test = {
            "self_test_result": random.choice(test_results).value,
            "self_test_code": random.choice(test_types).value,
            "segment_number": 0,
            "valid_diagnostic_information": True,
            "power_on_hours": random.randint(1000, 50000),
            "nsid": random.randint(1, 4) if random.choice([True, False]) else None,
            "flba": random.randint(0, 1000000) if random.choice([True, False]) else None,
            "status_code_type": random.randint(0, 7),
            "status_code": random.randint(0, 255),
            "completion_timestamp": test_time.isoformat()
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
    
    vendors = ["Samsung", "Western Digital", "Crucial", "Intel", "Seagate"]
    
    model = random.choice(models)
    vendor = random.choice(vendors)
    
    return {
        "device_path": device_path,
        "controller_info": {
            "pci_vendor_id": f"0x{random.randint(0x1000, 0xFFFF):04x}",
            "pci_subsystem_vendor_id": f"0x{random.randint(0x1000, 0xFFFF):04x}",
            "serial_number": f"S{random.randint(100000000000, 999999999999)}",
            "model_name": model,
            "firmware_revision": f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "recommended_arbitration_burst": random.randint(1, 16),
            "ieee_oui_identifier": f"0x{random.randint(0x000000, 0xFFFFFF):06x}",
            "multi_interface_capabilities": random.randint(0, 255),
            "controller_id": random.randint(1, 65535),
            "version": f"{random.randint(1, 2)}.{random.randint(0, 4)}",
            "rtd3_resume_latency": random.randint(1000, 100000),
            "rtd3_entry_latency": random.randint(1000, 100000),
            "optional_admin_commands": random.randint(0, 65535),
            "optional_nvm_commands": random.randint(0, 65535),
            "maximum_data_transfer_size": random.randint(4, 128),
            "warning_composite_temperature_threshold": random.randint(343, 358),
            "critical_composite_temperature_threshold": random.randint(358, 373),
            "total_capacity_gb": random.choice([256, 512, 1024, 2048, 4096])
        },
        "namespaces": [
            {
                "nsid": 1,
                "size": random.randint(1000000000, 4000000000),
                "capacity": random.randint(1000000000, 4000000000),
                "utilization": random.randint(500000000, 2000000000),
                "format": "512B + 0B"
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
            "entries": generate_mock_self_test_data(device_path)
        },
        "timestamp": datetime.utcnow().isoformat(),
        "collection_duration_seconds": random.uniform(0.5, 3.0)
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
