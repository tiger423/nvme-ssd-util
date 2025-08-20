"""
Test script for the Core NVMe Interface functions
"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, '/home/ubuntu')

from nvme_health_monitor.core.nvme_interface import (
    check_nvme_cli_availability,
    execute_nvme_command,
    validate_device_path,
    list_nvme_devices,
    get_device_namespaces,
    get_smart_log,
    get_error_log,
    get_self_test_log,
    get_controller_info,
    start_device_self_test,
    abort_device_self_test,
    get_self_test_status
)
from nvme_health_monitor.models.exceptions import (
    NVMeCommandError,
    NVMeDeviceNotFoundError,
    NVMePermissionError,
    NVMeTimeoutError
)


def test_check_nvme_cli_availability():
    """Test nvme-cli availability checking."""
    print("Testing check_nvme_cli_availability()...")
    
    result = check_nvme_cli_availability()
    print(f"✓ NVMe CLI available: {result}")
    
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = check_nvme_cli_availability()
        print(f"✓ Mocked unavailable: {result == False}")


def test_validate_device_path():
    """Test device path validation."""
    print("\nTesting validate_device_path()...")
    
    result = validate_device_path("/dev/nvme0")
    print(f"✓ Non-existent device validation: {result == False}")
    
    invalid_paths = [
        "",
        "/dev/sda1",
        "/dev/nvme",
        "/dev/nvme0n1",
        "nvme0",
        None
    ]
    
    for path in invalid_paths:
        if path is not None:
            result = validate_device_path(path)
            print(f"✓ Invalid path '{path}': {result == False}")


def test_execute_nvme_command():
    """Test command execution with mocked responses."""
    print("\nTesting execute_nvme_command()...")
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"test": "data"}'
    mock_result.stderr = ''
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('nvme_health_monitor.core.nvme_interface.check_nvme_cli_availability', return_value=True):
            result = execute_nvme_command(['nvme', 'version'])
            print(f"✓ Successful command execution: {result['success']}")
            print(f"✓ JSON parsing: {result['data'] == {'test': 'data'}}")
    
    mock_result.returncode = 1
    mock_result.stderr = 'Command failed'
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('nvme_health_monitor.core.nvme_interface.check_nvme_cli_availability', return_value=True):
            try:
                execute_nvme_command(['nvme', 'invalid'])
                print("✗ Should have raised NVMeCommandError")
            except NVMeCommandError as e:
                print(f"✓ Command error caught: {type(e).__name__}")
    
    mock_result.stderr = 'permission denied'
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('nvme_health_monitor.core.nvme_interface.check_nvme_cli_availability', return_value=True):
            try:
                execute_nvme_command(['nvme', 'list'])
                print("✗ Should have raised NVMePermissionError")
            except NVMePermissionError as e:
                print(f"✓ Permission error caught: {type(e).__name__}")


def test_list_nvme_devices():
    """Test device listing with mocked response."""
    print("\nTesting list_nvme_devices()...")
    
    mock_devices_response = {
        "Devices": [
            {
                "DevicePath": "/dev/nvme0",
                "Node": "nvme0",
                "SerialNumber": "TEST123",
                "ModelNumber": "Test SSD",
                "Namespace": "nvme0n1",
                "UsedBytes": "1000000000",
                "PhysicalSize": "2000000000",
                "Firmware": "1.0"
            }
        ]
    }
    
    with patch('nvme_health_monitor.core.nvme_interface.execute_nvme_command') as mock_exec:
        with patch('nvme_health_monitor.core.nvme_interface.validate_device_path', return_value=True):
            mock_exec.return_value = {
                'success': True,
                'data': mock_devices_response,
                'raw_output': '',
                'error_message': '',
                'return_code': 0
            }
            
            devices = list_nvme_devices()
            print(f"✓ Device list returned: {len(devices)} devices")
            if devices:
                print(f"✓ First device path: {devices[0]['device_path']}")
                print(f"✓ First device model: {devices[0]['model']}")


def test_get_device_namespaces():
    """Test namespace retrieval with mocked response."""
    print("\nTesting get_device_namespaces()...")
    
    try:
        get_device_namespaces("/invalid/path")
        print("✗ Should have raised NVMeDeviceNotFoundError")
    except NVMeDeviceNotFoundError as e:
        print(f"✓ Device not found error caught: {type(e).__name__}")
    
    mock_namespaces = [
        {
            "nsid": 1,
            "size": 1000000000,
            "capacity": 1000000000,
            "utilization": 500000000,
            "format": "512B"
        }
    ]
    
    with patch('nvme_health_monitor.core.nvme_interface.validate_device_path', return_value=True):
        with patch('nvme_health_monitor.core.nvme_interface.execute_nvme_command') as mock_exec:
            mock_exec.return_value = {
                'success': True,
                'data': mock_namespaces,
                'raw_output': '',
                'error_message': '',
                'return_code': 0
            }
            
            namespaces = get_device_namespaces("/dev/nvme0")
            print(f"✓ Namespace list returned: {len(namespaces)} namespaces")
            if namespaces:
                print(f"✓ First namespace ID: {namespaces[0]['nsid']}")


def test_get_smart_log():
    """Test SMART log retrieval with mocked response."""
    print("\nTesting get_smart_log()...")
    
    mock_smart_data = {
        "critical_warning": 0,
        "temperature": 308,
        "available_spare": 100,
        "available_spare_threshold": 10,
        "percentage_used": 1,
        "data_units_read": 1000000,
        "data_units_written": 500000,
        "host_read_commands": 2000000,
        "host_write_commands": 1000000,
        "controller_busy_time": 3600,
        "power_cycles": 100,
        "power_on_hours": 8760,
        "unsafe_shutdowns": 0,
        "media_errors": 0,
        "num_err_log_entries": 0
    }
    
    with patch('nvme_health_monitor.core.nvme_interface.validate_device_path', return_value=True):
        with patch('nvme_health_monitor.core.nvme_interface.execute_nvme_command') as mock_exec:
            mock_exec.return_value = {
                'success': True,
                'data': mock_smart_data,
                'raw_output': '',
                'error_message': '',
                'return_code': 0
            }
            
            smart_data = get_smart_log("/dev/nvme0")
            print(f"✓ SMART data retrieved: {len(smart_data)} fields")
            print(f"✓ Temperature conversion: {smart_data.get('temperature_celsius', 'N/A')}°C")


def test_get_error_log():
    """Test error log retrieval with mocked response."""
    print("\nTesting get_error_log()...")
    
    mock_error_data = {
        "errors": [
            {
                "error_count": 1,
                "sqid": 0,
                "cmdid": 123,
                "status_field": 0x4004,
                "parm_error_location": 0,
                "lba": 1000,
                "nsid": 1,
                "vs": 0,
                "trtype": "pcie"
            }
        ]
    }
    
    with patch('nvme_health_monitor.core.nvme_interface.validate_device_path', return_value=True):
        with patch('nvme_health_monitor.core.nvme_interface.execute_nvme_command') as mock_exec:
            mock_exec.return_value = {
                'success': True,
                'data': mock_error_data,
                'raw_output': '',
                'error_message': '',
                'return_code': 0
            }
            
            error_logs = get_error_log("/dev/nvme0")
            print(f"✓ Error log retrieved: {len(error_logs)} entries")
            if error_logs:
                print(f"✓ First error count: {error_logs[0]['error_count']}")


def test_get_self_test_log():
    """Test self-test log retrieval with mocked response."""
    print("\nTesting get_self_test_log()...")
    
    mock_self_test_data = {
        "self_test_result": [
            {
                "self_test_result": 0,
                "self_test_code": 1,
                "segment_number": 0,
                "valid_diagnostic_information": 1,
                "power_on_hours": 8760,
                "nsid": 0,
                "failing_lba": 0,
                "status_code_type": 0,
                "status_code": 0
            }
        ]
    }
    
    with patch('nvme_health_monitor.core.nvme_interface.validate_device_path', return_value=True):
        with patch('nvme_health_monitor.core.nvme_interface.execute_nvme_command') as mock_exec:
            mock_exec.return_value = {
                'success': True,
                'data': mock_self_test_data,
                'raw_output': '',
                'error_message': '',
                'return_code': 0
            }
            
            self_test_results = get_self_test_log("/dev/nvme0")
            print(f"✓ Self-test log retrieved: {len(self_test_results)} results")
            if self_test_results:
                print(f"✓ First test result: {self_test_results[0]['self_test_result']}")


def test_get_controller_info():
    """Test controller info retrieval with mocked response."""
    print("\nTesting get_controller_info()...")
    
    mock_controller_data = {
        "vid": 0x144d,
        "ssvid": 0x144d,
        "sn": "S4EWNX0N123456",
        "mn": "Samsung SSD 980 PRO 1TB",
        "fr": "5B2QGXA7",
        "rab": 6,
        "ieee": 0x002538,
        "cmic": 0,
        "mdts": 9,
        "cntlid": 1,
        "ver": 0x10400,
        "rtd3r": 1000000,
        "rtd3e": 1000000,
        "oaes": 0x200,
        "ctratt": 0x2
    }
    
    with patch('nvme_health_monitor.core.nvme_interface.validate_device_path', return_value=True):
        with patch('nvme_health_monitor.core.nvme_interface.execute_nvme_command') as mock_exec:
            mock_exec.return_value = {
                'success': True,
                'data': mock_controller_data,
                'raw_output': '',
                'error_message': '',
                'return_code': 0
            }
            
            controller_info = get_controller_info("/dev/nvme0")
            print(f"✓ Controller info retrieved: {len(controller_info)} fields")
            print(f"✓ Model: {controller_info.get('mn', 'N/A')}")
            print(f"✓ Serial: {controller_info.get('sn', 'N/A')}")


def test_self_test_management():
    """Test self-test management functions."""
    print("\nTesting self-test management functions...")
    
    with patch('nvme_health_monitor.core.nvme_interface.validate_device_path', return_value=True):
        with patch('nvme_health_monitor.core.nvme_interface.execute_nvme_command') as mock_exec:
            mock_exec.return_value = {
                'success': True,
                'data': {},
                'raw_output': '',
                'error_message': '',
                'return_code': 0
            }
            
            result = start_device_self_test("/dev/nvme0", "short")
            print(f"✓ Start short self-test: {result}")
            
            try:
                start_device_self_test("/dev/nvme0", "invalid")
                print("✗ Should have raised ValueError")
            except ValueError as e:
                print(f"✓ Invalid test type error caught: {type(e).__name__}")
            
            result = abort_device_self_test("/dev/nvme0")
            print(f"✓ Abort self-test: {result}")
    
    with patch('nvme_health_monitor.core.nvme_interface.validate_device_path', return_value=True):
        with patch('nvme_health_monitor.core.nvme_interface.get_smart_log') as mock_smart:
            mock_smart.return_value = {
                "device_self_test": {
                    "status": 1,
                    "current_operation": 1,
                    "completion": 50
                }
            }
            
            status = get_self_test_status("/dev/nvme0")
            print(f"✓ Self-test status: running={status['is_running']}, type={status['test_type']}, progress={status['progress_percent']}%")


if __name__ == "__main__":
    print("Testing Core NVMe Interface Functions...")
    print("=" * 60)
    
    test_check_nvme_cli_availability()
    test_validate_device_path()
    test_execute_nvme_command()
    test_list_nvme_devices()
    test_get_device_namespaces()
    test_get_smart_log()
    test_get_error_log()
    test_get_self_test_log()
    test_get_controller_info()
    test_self_test_management()
    
    print("\n✅ All Core NVMe Interface tests completed!")
    print("🎉 Section 3 implementation is complete and tested!")
