"""
NVMe Health Monitor - Core NVMe Interface

This module provides the core interface for executing nvme-cli commands
and interacting with NVMe devices. All NVMe operations go through this interface.
"""

import json
import os
import re
import stat
import subprocess
from typing import Any, Dict, List, Optional

from ..models.exceptions import (
    NVMeCommandError,
    NVMeDeviceNotFoundError,
    NVMePermissionError,
    NVMeTimeoutError
)


def check_nvme_cli_availability() -> bool:
    """
    Check if nvme-cli is installed and accessible.
    
    Returns:
        bool: True if nvme-cli is available, False otherwise
        
    Implementation Notes:
        - Use subprocess.run() with 'which nvme' or 'nvme version'
        - Handle FileNotFoundError
        - Return boolean result
        - Log availability status
    """
    try:
        result = subprocess.run(
            ['which', 'nvme'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_result = subprocess.run(
                ['nvme', 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return version_result.returncode == 0
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def execute_nvme_command(command_args: List[str], timeout: int = 30) -> Dict[str, Any]:
    """
    Execute nvme-cli command and return parsed result.
    
    Args:
        command_args: List of command arguments (e.g., ['nvme', 'list', '--output-format=json'])
        timeout: Command timeout in seconds
        
    Returns:
        Dict containing:
            - success: bool
            - data: Dict (parsed JSON output)
            - raw_output: str
            - error_message: str (if failed)
            - return_code: int
            
    Raises:
        NVMeCommandError: If command execution fails
        NVMeTimeoutError: If command times out
        
    Implementation Notes:
        - Use subprocess.run() with capture_output=True, text=True
        - Parse JSON output if command succeeds
        - Handle various error conditions
        - Log command execution details
        - Validate JSON output structure
    """
    if not check_nvme_cli_availability():
        raise NVMeCommandError("nvme-cli is not available - please install nvme-cli")
    
    try:
        result = subprocess.run(
            command_args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        
        response = {
            'success': result.returncode == 0,
            'raw_output': result.stdout,
            'error_message': result.stderr if result.returncode != 0 else '',
            'return_code': result.returncode,
            'data': {}
        }
        
        if result.returncode != 0:
            if 'permission denied' in result.stderr.lower() or 'operation not permitted' in result.stderr.lower():
                raise NVMePermissionError(
                    f"Permission denied executing command: {' '.join(command_args)}",
                    required_permissions="root or nvme group membership"
                )
            else:
                raise NVMeCommandError(
                    f"Command failed: {' '.join(command_args)}",
                    command=command_args,
                    return_code=result.returncode,
                    stderr_output=result.stderr
                )
        
        if result.stdout.strip():
            try:
                response['data'] = json.loads(result.stdout)
            except json.JSONDecodeError:
                response['data'] = {'raw_text': result.stdout}
        
        return response
        
    except subprocess.TimeoutExpired:
        raise NVMeTimeoutError(
            f"Command timed out after {timeout}s: {' '.join(command_args)}",
            timeout_duration=timeout
        )
    except FileNotFoundError:
        raise NVMeCommandError("nvme-cli not found - please install nvme-cli")


def validate_device_path(device_path: str) -> bool:
    """
    Validate NVMe device path format and existence.
    
    Args:
        device_path: Device path (e.g., '/dev/nvme0')
        
    Returns:
        bool: True if valid device path, False otherwise
        
    Implementation Notes:
        - Check path format (should match /dev/nvme\d+)
        - Check if device file exists
        - Check if device is accessible
        - Validate it's actually an NVMe device
    """
    if not device_path:
        return False
    
    nvme_pattern = re.compile(r'^/dev/nvme\d+$')
    if not nvme_pattern.match(device_path):
        return False
    
    if not os.path.exists(device_path):
        return False
    
    try:
        stat_result = os.stat(device_path)
        return stat.S_ISBLK(stat_result.st_mode) or stat.S_ISCHR(stat_result.st_mode)
    except (OSError, PermissionError):
        return False


def list_nvme_devices() -> List[Dict[str, Any]]:
    """
    List all available NVMe devices on the system.
    
    Returns:
        List of dictionaries containing device information:
            - device_path: str
            - node: str
            - serial_number: str
            - model: str
            - namespace: str
            - usage: str
            - format: str
            - firmware_revision: str
            
    Raises:
        NVMeCommandError: If device listing fails
        
    Implementation Notes:
        - Execute 'nvme list --output-format=json'
        - Parse JSON response
        - Handle empty device list
        - Filter out invalid entries
        - Sort devices by device path
    """
    command = ['nvme', 'list', '--output-format=json']
    
    try:
        result = execute_nvme_command(command)
        
        if not result['success']:
            raise NVMeCommandError(
                "Failed to list NVMe devices",
                command=command,
                return_code=result['return_code'],
                stderr_output=result['error_message']
            )
        
        devices_data = result['data']
        devices = []
        
        if 'Devices' in devices_data and isinstance(devices_data['Devices'], list):
            for device in devices_data['Devices']:
                if isinstance(device, dict) and 'DevicePath' in device:
                    device_info = {
                        'device_path': device.get('DevicePath', ''),
                        'node': device.get('Node', ''),
                        'serial_number': device.get('SerialNumber', ''),
                        'model': device.get('ModelNumber', ''),
                        'namespace': device.get('Namespace', ''),
                        'usage': device.get('UsedBytes', ''),
                        'format': device.get('PhysicalSize', ''),
                        'firmware_revision': device.get('Firmware', '')
                    }
                    
                    if validate_device_path(device_info['device_path']):
                        devices.append(device_info)
        
        devices.sort(key=lambda x: x['device_path'])
        return devices
        
    except (NVMeCommandError, NVMePermissionError, NVMeTimeoutError):
        raise
    except Exception as e:
        raise NVMeCommandError(f"Unexpected error listing devices: {str(e)}")


def get_device_namespaces(device_path: str) -> List[Dict[str, Any]]:
    """
    Get namespace information for a specific NVMe device.
    
    Args:
        device_path: NVMe device path (e.g., '/dev/nvme0')
        
    Returns:
        List of namespace dictionaries containing:
            - nsid: int
            - size: int
            - capacity: int
            - utilization: int
            - format: str
            
    Raises:
        NVMeDeviceNotFoundError: If device not found
        NVMeCommandError: If command fails
        
    Implementation Notes:
        - Execute 'nvme list-ns {device} --output-format=json'
        - Parse namespace information
        - Handle devices with no namespaces
        - Validate namespace data
    """
    if not validate_device_path(device_path):
        raise NVMeDeviceNotFoundError(f"Invalid or non-existent device: {device_path}")
    
    command = ['nvme', 'list-ns', device_path, '--output-format=json']
    
    try:
        result = execute_nvme_command(command)
        
        if not result['success']:
            raise NVMeCommandError(
                f"Failed to get namespaces for device {device_path}",
                command=command,
                return_code=result['return_code'],
                stderr_output=result['error_message'],
                device_path=device_path
            )
        
        namespaces_data = result['data']
        namespaces = []
        
        if isinstance(namespaces_data, list):
            for ns_data in namespaces_data:
                if isinstance(ns_data, dict):
                    namespace_info = {
                        'nsid': ns_data.get('nsid', 0),
                        'size': ns_data.get('size', 0),
                        'capacity': ns_data.get('capacity', 0),
                        'utilization': ns_data.get('utilization', 0),
                        'format': ns_data.get('format', '')
                    }
                    namespaces.append(namespace_info)
        
        return namespaces
        
    except (NVMeCommandError, NVMePermissionError, NVMeTimeoutError, NVMeDeviceNotFoundError):
        raise
    except Exception as e:
        raise NVMeCommandError(f"Unexpected error getting namespaces: {str(e)}", device_path=device_path)


def get_smart_log(device_path: str, namespace_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Retrieve SMART log data from NVMe device.
    
    Args:
        device_path: NVMe device path
        namespace_id: Optional namespace ID
        
    Returns:
        Dictionary containing SMART data fields
        
    Raises:
        NVMeDeviceNotFoundError: If device not found
        NVMeCommandError: If SMART log retrieval fails
        
    Implementation Notes:
        - Execute 'nvme smart-log {device} --output-format=json'
        - Add namespace parameter if provided
        - Parse SMART data fields
        - Convert temperature from Kelvin to Celsius
        - Validate critical SMART attributes
    """
    if not validate_device_path(device_path):
        raise NVMeDeviceNotFoundError(f"Invalid or non-existent device: {device_path}")
    
    command = ['nvme', 'smart-log', device_path, '--output-format=json']
    
    if namespace_id is not None:
        command.extend(['--namespace-id', str(namespace_id)])
    
    try:
        result = execute_nvme_command(command)
        
        if not result['success']:
            raise NVMeCommandError(
                f"Failed to get SMART log for device {device_path}",
                command=command,
                return_code=result['return_code'],
                stderr_output=result['error_message'],
                device_path=device_path
            )
        
        smart_data = result['data']
        
        if 'temperature' in smart_data and smart_data['temperature'] > 273:
            smart_data['temperature_celsius'] = smart_data['temperature'] - 273
        
        return smart_data
        
    except (NVMeCommandError, NVMePermissionError, NVMeTimeoutError, NVMeDeviceNotFoundError):
        raise
    except Exception as e:
        raise NVMeCommandError(f"Unexpected error getting SMART log: {str(e)}", device_path=device_path)


def get_error_log(device_path: str, max_entries: int = 64) -> List[Dict[str, Any]]:
    """
    Retrieve error log entries from NVMe device.
    
    Args:
        device_path: NVMe device path
        max_entries: Maximum number of error entries to retrieve
        
    Returns:
        List of error log entry dictionaries
        
    Raises:
        NVMeDeviceNotFoundError: If device not found
        NVMeCommandError: If error log retrieval fails
        
    Implementation Notes:
        - Execute 'nvme error-log {device} --log-entries={max_entries} --output-format=json'
        - Parse error log entries
        - Handle empty error logs
        - Sort entries by timestamp/sequence
        - Filter out invalid entries
    """
    if not validate_device_path(device_path):
        raise NVMeDeviceNotFoundError(f"Invalid or non-existent device: {device_path}")
    
    command = ['nvme', 'error-log', device_path, f'--log-entries={max_entries}', '--output-format=json']
    
    try:
        result = execute_nvme_command(command)
        
        if not result['success']:
            raise NVMeCommandError(
                f"Failed to get error log for device {device_path}",
                command=command,
                return_code=result['return_code'],
                stderr_output=result['error_message'],
                device_path=device_path
            )
        
        error_data = result['data']
        error_entries = []
        
        if 'errors' in error_data and isinstance(error_data['errors'], list):
            error_entries = error_data['errors']
        elif isinstance(error_data, list):
            error_entries = error_data
        
        valid_entries = []
        for entry in error_entries:
            if isinstance(entry, dict) and 'error_count' in entry:
                valid_entries.append(entry)
        
        return valid_entries
        
    except (NVMeCommandError, NVMePermissionError, NVMeTimeoutError, NVMeDeviceNotFoundError):
        raise
    except Exception as e:
        raise NVMeCommandError(f"Unexpected error getting error log: {str(e)}", device_path=device_path)


def get_self_test_log(device_path: str) -> List[Dict[str, Any]]:
    """
    Retrieve device self-test log from NVMe device.
    
    Args:
        device_path: NVMe device path
        
    Returns:
        List of self-test result dictionaries
        
    Raises:
        NVMeDeviceNotFoundError: If device not found
        NVMeCommandError: If self-test log retrieval fails
        
    Implementation Notes:
        - Execute 'nvme self-test-log {device} --output-format=json'
        - Parse self-test results
        - Handle devices without self-test capability
        - Sort results by completion time
        - Decode test result status codes
    """
    if not validate_device_path(device_path):
        raise NVMeDeviceNotFoundError(f"Invalid or non-existent device: {device_path}")
    
    command = ['nvme', 'self-test-log', device_path, '--output-format=json']
    
    try:
        result = execute_nvme_command(command)
        
        if not result['success']:
            raise NVMeCommandError(
                f"Failed to get self-test log for device {device_path}",
                command=command,
                return_code=result['return_code'],
                stderr_output=result['error_message'],
                device_path=device_path
            )
        
        self_test_data = result['data']
        test_results = []
        
        if 'self_test_result' in self_test_data and isinstance(self_test_data['self_test_result'], list):
            test_results = self_test_data['self_test_result']
        elif isinstance(self_test_data, list):
            test_results = self_test_data
        
        valid_results = []
        for result_entry in test_results:
            if isinstance(result_entry, dict):
                valid_results.append(result_entry)
        
        return valid_results
        
    except (NVMeCommandError, NVMePermissionError, NVMeTimeoutError, NVMeDeviceNotFoundError):
        raise
    except Exception as e:
        raise NVMeCommandError(f"Unexpected error getting self-test log: {str(e)}", device_path=device_path)


def get_controller_info(device_path: str) -> Dict[str, Any]:
    """
    Retrieve controller identification information.
    
    Args:
        device_path: NVMe device path
        
    Returns:
        Dictionary containing controller information
        
    Raises:
        NVMeDeviceNotFoundError: If device not found
        NVMeCommandError: If controller info retrieval fails
        
    Implementation Notes:
        - Execute 'nvme id-ctrl {device} --output-format=json'
        - Parse controller identification data
        - Extract key device information
        - Handle vendor-specific fields
        - Validate required fields
    """
    if not validate_device_path(device_path):
        raise NVMeDeviceNotFoundError(f"Invalid or non-existent device: {device_path}")
    
    command = ['nvme', 'id-ctrl', device_path, '--output-format=json']
    
    try:
        result = execute_nvme_command(command)
        
        if not result['success']:
            raise NVMeCommandError(
                f"Failed to get controller info for device {device_path}",
                command=command,
                return_code=result['return_code'],
                stderr_output=result['error_message'],
                device_path=device_path
            )
        
        controller_data = result['data']
        
        required_fields = ['vid', 'ssvid', 'sn', 'mn', 'fr']
        for field in required_fields:
            if field not in controller_data:
                controller_data[field] = ''
        
        return controller_data
        
    except (NVMeCommandError, NVMePermissionError, NVMeTimeoutError, NVMeDeviceNotFoundError):
        raise
    except Exception as e:
        raise NVMeCommandError(f"Unexpected error getting controller info: {str(e)}", device_path=device_path)


def start_device_self_test(device_path: str, test_type: str, namespace_id: Optional[int] = None) -> bool:
    """
    Start device self-test operation.
    
    Args:
        device_path: NVMe device path
        test_type: Test type ('short', 'extended', 'vendor')
        namespace_id: Optional namespace ID
        
    Returns:
        bool: True if test started successfully
        
    Raises:
        NVMeDeviceNotFoundError: If device not found
        NVMeCommandError: If self-test start fails
        ValueError: If invalid test type
        
    Implementation Notes:
        - Map test_type to nvme-cli codes (1h=short, 2h=extended, eh=vendor)
        - Execute 'nvme device-self-test {device} --self-test-code={code}'
        - Add namespace parameter if provided
        - Validate test type parameter
        - Check if device supports self-test
    """
    if not validate_device_path(device_path):
        raise NVMeDeviceNotFoundError(f"Invalid or non-existent device: {device_path}")
    
    test_codes = {
        'short': '1',
        'extended': '2',
        'vendor': 'e'
    }
    
    if test_type not in test_codes:
        raise ValueError(f"Invalid test type: {test_type}. Must be one of: {list(test_codes.keys())}")
    
    command = ['nvme', 'device-self-test', device_path, f'--self-test-code={test_codes[test_type]}']
    
    if namespace_id is not None:
        command.extend(['--namespace-id', str(namespace_id)])
    
    try:
        result = execute_nvme_command(command)
        
        if not result['success']:
            raise NVMeCommandError(
                f"Failed to start {test_type} self-test for device {device_path}",
                command=command,
                return_code=result['return_code'],
                stderr_output=result['error_message'],
                device_path=device_path
            )
        
        return True
        
    except (NVMeCommandError, NVMePermissionError, NVMeTimeoutError, NVMeDeviceNotFoundError):
        raise
    except Exception as e:
        raise NVMeCommandError(f"Unexpected error starting self-test: {str(e)}", device_path=device_path)


def abort_device_self_test(device_path: str) -> bool:
    """
    Abort running device self-test operation.
    
    Args:
        device_path: NVMe device path
        
    Returns:
        bool: True if test aborted successfully
        
    Raises:
        NVMeDeviceNotFoundError: If device not found
        NVMeCommandError: If self-test abort fails
        
    Implementation Notes:
        - Execute 'nvme device-self-test {device} --self-test-code=fh'
        - Check if test is currently running
        - Handle case where no test is running
    """
    if not validate_device_path(device_path):
        raise NVMeDeviceNotFoundError(f"Invalid or non-existent device: {device_path}")
    
    command = ['nvme', 'device-self-test', device_path, '--self-test-code=f']
    
    try:
        result = execute_nvme_command(command)
        
        if not result['success']:
            raise NVMeCommandError(
                f"Failed to abort self-test for device {device_path}",
                command=command,
                return_code=result['return_code'],
                stderr_output=result['error_message'],
                device_path=device_path
            )
        
        return True
        
    except (NVMeCommandError, NVMePermissionError, NVMeTimeoutError, NVMeDeviceNotFoundError):
        raise
    except Exception as e:
        raise NVMeCommandError(f"Unexpected error aborting self-test: {str(e)}", device_path=device_path)


def get_self_test_status(device_path: str) -> Dict[str, Any]:
    """
    Get current self-test operation status.
    
    Args:
        device_path: NVMe device path
        
    Returns:
        Dictionary containing:
            - is_running: bool
            - test_type: str
            - progress_percent: int
            - estimated_completion: Optional[datetime]
            
    Raises:
        NVMeDeviceNotFoundError: If device not found
        NVMeCommandError: If status retrieval fails
        
    Implementation Notes:
        - Get SMART log to check self-test status
        - Parse device self-test status field
        - Calculate progress and estimated completion
        - Handle devices without self-test capability
    """
    if not validate_device_path(device_path):
        raise NVMeDeviceNotFoundError(f"Invalid or non-existent device: {device_path}")
    
    try:
        smart_data = get_smart_log(device_path)
        
        status = {
            'is_running': False,
            'test_type': 'none',
            'progress_percent': 0,
            'estimated_completion': None
        }
        
        if 'device_self_test' in smart_data:
            dst_status = smart_data['device_self_test']
            
            if isinstance(dst_status, dict):
                status['is_running'] = dst_status.get('status', 0) != 0
                
                test_code = dst_status.get('current_operation', 0)
                if test_code == 1:
                    status['test_type'] = 'short'
                elif test_code == 2:
                    status['test_type'] = 'extended'
                elif test_code == 14:
                    status['test_type'] = 'vendor'
                
                status['progress_percent'] = dst_status.get('completion', 0)
        
        return status
        
    except (NVMeCommandError, NVMePermissionError, NVMeTimeoutError, NVMeDeviceNotFoundError):
        raise
    except Exception as e:
        raise NVMeCommandError(f"Unexpected error getting self-test status: {str(e)}", device_path=device_path)
