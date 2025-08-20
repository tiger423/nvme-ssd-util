# NVMe Health Monitor - Software Implementation Specification

## Overview
This document provides a detailed function-by-function implementation specification for a Python utility library that collects NVMe SSD health information using nvme-cli. Each function is designed as a standalone utility that can be implemented by different team members.

## Project Structure
```
nvme_health_monitor/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── nvme_interface.py
│   ├── data_collector.py
│   ├── data_processor.py
│   └── device_manager.py
├── models/
│   ├── __init__.py
│   ├── health_metrics.py
│   ├── device_info.py
│   └── exceptions.py
├── utils/
│   ├── __init__.py
│   ├── validation.py
│   ├── logging_config.py
│   └── config.py
├── output/
│   ├── __init__.py
│   ├── formatters.py
│   ├── reporters.py
│   └── exporters.py
└── cli.py
```

## Dependencies
```python
# requirements.txt
pydantic>=2.0.0
click>=8.0.0
rich>=13.0.0
pandas>=2.0.0
```

---

## 1. Exception Classes (`models/exceptions.py`)

### 1.1 Base Exception Class
```python
def create_nvme_base_exception() -> type:
    """
    Create base exception class for NVMe operations.
    
    Returns:
        type: Base exception class
        
    Implementation Notes:
        - Inherit from Exception
        - Add device_path attribute
        - Add timestamp attribute
        - Override __str__ method for better error messages
    """
```

### 1.2 Specific Exception Classes
```python
def create_nvme_command_error() -> type:
    """
    Create exception for nvme-cli command execution failures.
    
    Returns:
        type: Command error exception class
        
    Implementation Notes:
        - Inherit from NVMeBaseException
        - Add command attribute to store failed command
        - Add return_code attribute
        - Add stderr_output attribute
    """

def create_nvme_device_not_found_error() -> type:
    """
    Create exception for device not found errors.
    
    Returns:
        type: Device not found exception class
        
    Implementation Notes:
        - Inherit from NVMeBaseException
        - Add available_devices attribute
    """

def create_nvme_permission_error() -> type:
    """
    Create exception for permission denied errors.
    
    Returns:
        type: Permission error exception class
        
    Implementation Notes:
        - Inherit from NVMeBaseException
        - Add required_permissions attribute
    """

def create_nvme_timeout_error() -> type:
    """
    Create exception for command timeout errors.
    
    Returns:
        type: Timeout error exception class
        
    Implementation Notes:
        - Inherit from NVMeBaseException
        - Add timeout_duration attribute
    """
```

---

## 2. Data Models (`models/health_metrics.py`, `models/device_info.py`)

### 2.1 SMART Data Model
```python
def create_smart_data_model() -> type:
    """
    Create Pydantic model for SMART data.
    
    Returns:
        type: SMARTData model class
        
    Fields Required:
        - critical_warning: int
        - temperature: int (Celsius)
        - available_spare: int (percentage)
        - available_spare_threshold: int (percentage)
        - percentage_used: int
        - data_units_read: int
        - data_units_written: int
        - host_read_commands: int
        - host_write_commands: int
        - controller_busy_time: int
        - power_cycles: int
        - power_on_hours: int
        - unsafe_shutdowns: int
        - media_errors: int
        - num_err_log_entries: int
        
    Implementation Notes:
        - Use Pydantic BaseModel
        - Add validators for temperature conversion (Kelvin to Celsius)
        - Add computed fields for health status
        - Add method to check critical thresholds
    """

def create_error_log_entry_model() -> type:
    """
    Create Pydantic model for error log entries.
    
    Returns:
        type: ErrorLogEntry model class
        
    Fields Required:
        - error_count: int
        - sqid: int (submission queue ID)
        - cmdid: int (command ID)
        - status_field: int
        - parm_error_location: int
        - lba: int (logical block address)
        - nsid: int (namespace ID)
        - vs: int (vendor specific)
        - trtype: str (transport type)
        
    Implementation Notes:
        - Use Pydantic BaseModel
        - Add method to decode status field
        - Add severity classification
    """

def create_self_test_result_model() -> type:
    """
    Create Pydantic model for self-test results.
    
    Returns:
        type: SelfTestResult model class
        
    Fields Required:
        - self_test_result: int
        - self_test_code: int
        - segment_number: int
        - valid_diagnostic_information: int
        - power_on_hours: int
        - nsid: int
        - failing_lba: int
        - status_code_type: int
        - status_code: int
        
    Implementation Notes:
        - Use Pydantic BaseModel
        - Add method to decode test result codes
        - Add method to determine test status (passed/failed/in_progress)
    """

def create_device_info_model() -> type:
    """
    Create Pydantic model for device information.
    
    Returns:
        type: DeviceInfo model class
        
    Fields Required:
        - device_path: str
        - model_number: str
        - serial_number: str
        - firmware_revision: str
        - pci_vendor_id: str
        - pci_subsystem_vendor_id: str
        - ieee_oui_identifier: int
        - total_nvm_capacity: int
        - unallocated_nvm_capacity: int
        - controller_id: int
        - number_of_namespaces: int
        - namespace_size: int
        - namespace_capacity: int
        - namespace_utilization: int
        
    Implementation Notes:
        - Use Pydantic BaseModel
        - Add validators for capacity unit conversion
        - Add computed fields for human-readable sizes
    """

def create_health_snapshot_model() -> type:
    """
    Create comprehensive health snapshot model.
    
    Returns:
        type: HealthSnapshot model class
        
    Fields Required:
        - device_path: str
        - timestamp: datetime
        - smart_data: SMARTData
        - error_logs: List[ErrorLogEntry]
        - self_test_results: List[SelfTestResult]
        - device_info: DeviceInfo
        - collection_status: str
        - collection_errors: List[str]
        
    Implementation Notes:
        - Use Pydantic BaseModel
        - Add method to calculate overall health score
        - Add method to generate health summary
        - Add method to check for critical issues
    """
```

---

## 3. Core NVMe Interface (`core/nvme_interface.py`)

### 3.1 Command Execution Functions
```python
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
```

### 3.2 Device Discovery Functions
```python
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
```

### 3.3 Health Data Collection Functions
```python
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
```

### 3.4 Self-Test Management Functions
```python
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
```

---

## 4. Data Collection Orchestration (`core/data_collector.py`)

### 4.1 Single Device Collection Functions
```python
def collect_device_health_snapshot(device_path: str, include_self_test: bool = True) -> HealthSnapshot:
    """
    Collect complete health snapshot for a single device.
    
    Args:
        device_path: NVMe device path
        include_self_test: Whether to include self-test data
        
    Returns:
        HealthSnapshot: Complete health data snapshot
        
    Raises:
        NVMeDeviceNotFoundError: If device not found
        
    Implementation Notes:
        - Call all individual collection functions
        - Handle partial failures gracefully
        - Record collection errors in snapshot
        - Set collection timestamp
        - Validate collected data consistency
    """

def collect_smart_data_safe(device_path: str) -> Tuple[Optional[SMARTData], Optional[str]]:
    """
    Safely collect SMART data with error handling.
    
    Args:
        device_path: NVMe device path
        
    Returns:
        Tuple of (SMARTData or None, error_message or None)
        
    Implementation Notes:
        - Wrap get_smart_log() with try-catch
        - Return None and error message on failure
        - Log collection attempts and results
        - Handle permission errors gracefully
    """

def collect_error_logs_safe(device_path: str) -> Tuple[List[ErrorLogEntry], Optional[str]]:
    """
    Safely collect error logs with error handling.
    
    Args:
        device_path: NVMe device path
        
    Returns:
        Tuple of (error log entries list, error_message or None)
        
    Implementation Notes:
        - Wrap get_error_log() with try-catch
        - Return empty list and error message on failure
        - Handle devices without error log support
        - Limit number of entries to prevent memory issues
    """

def collect_device_info_safe(device_path: str) -> Tuple[Optional[DeviceInfo], Optional[str]]:
    """
    Safely collect device information with error handling.
    
    Args:
        device_path: NVMe device path
        
    Returns:
        Tuple of (DeviceInfo or None, error_message or None)
        
    Implementation Notes:
        - Wrap get_controller_info() with try-catch
        - Return None and error message on failure
        - Extract and validate required fields
        - Handle vendor-specific variations
    """
```

### 4.2 Multi-Device Collection Functions
```python
def collect_all_devices_health(parallel: bool = True, max_workers: int = 4) -> List[HealthSnapshot]:
    """
    Collect health data for all available NVMe devices.
    
    Args:
        parallel: Whether to collect data in parallel
        max_workers: Maximum number of worker threads
        
    Returns:
        List of HealthSnapshot objects for all devices
        
    Implementation Notes:
        - Discover all NVMe devices first
        - Use ThreadPoolExecutor for parallel collection
        - Handle individual device failures
        - Sort results by device path
        - Log collection summary
    """

def collect_devices_health_batch(device_paths: List[str], parallel: bool = True) -> List[HealthSnapshot]:
    """
    Collect health data for specified devices.
    
    Args:
        device_paths: List of device paths to collect from
        parallel: Whether to collect data in parallel
        
    Returns:
        List of HealthSnapshot objects
        
    Implementation Notes:
        - Validate all device paths first
        - Use concurrent.futures for parallel execution
        - Maintain order of input device list
        - Handle timeout for slow devices
        - Aggregate collection statistics
    """
```

---

## 5. Data Processing and Validation (`core/data_processor.py`)

### 5.1 Data Validation Functions
```python
def validate_smart_data(smart_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate SMART data for completeness and sanity.
    
    Args:
        smart_data: Raw SMART data dictionary
        
    Returns:
        Tuple of (is_valid: bool, validation_errors: List[str])
        
    Implementation Notes:
        - Check for required SMART fields
        - Validate value ranges (temperature, percentages, etc.)
        - Check for impossible values
        - Validate data type consistency
        - Return detailed validation errors
    """

def validate_error_log_entry(error_entry: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate error log entry data.
    
    Args:
        error_entry: Raw error log entry dictionary
        
    Returns:
        Tuple of (is_valid: bool, validation_errors: List[str])
        
    Implementation Notes:
        - Check for required error log fields
        - Validate field value ranges
        - Check status field consistency
        - Validate LBA and namespace ID values
        - Return specific validation errors
    """

def sanitize_device_info(device_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize and normalize device information.
    
    Args:
        device_info: Raw device information dictionary
        
    Returns:
        Sanitized device information dictionary
        
    Implementation Notes:
        - Trim whitespace from string fields
        - Normalize capacity units
        - Handle missing optional fields
        - Convert hex values to integers
        - Standardize field names
    """
```

### 5.2 Data Transformation Functions
```python
def convert_temperature_kelvin_to_celsius(kelvin_temp: int) -> int:
    """
    Convert temperature from Kelvin to Celsius.
    
    Args:
        kelvin_temp: Temperature in Kelvin
        
    Returns:
        Temperature in Celsius
        
    Implementation Notes:
        - Handle zero/invalid temperatures
        - Validate reasonable temperature ranges
        - Round to nearest integer
        - Handle overflow/underflow
    """

def convert_capacity_to_bytes(capacity: int, unit: str) -> int:
    """
    Convert capacity value to bytes.
    
    Args:
        capacity: Capacity value
        unit: Unit string ('KB', 'MB', 'GB', 'TB', etc.)
        
    Returns:
        Capacity in bytes
        
    Raises:
        ValueError: If unit is not recognized
        
    Implementation Notes:
        - Support both decimal (1000) and binary (1024) units
        - Handle case-insensitive unit strings
        - Validate capacity ranges
        - Handle integer overflow
    """

def calculate_health_score(smart_data: SMARTData, error_count: int) -> int:
    """
    Calculate overall health score (0-100) based on SMART data and errors.
    
    Args:
        smart_data: Validated SMART data
        error_count: Number of error log entries
        
    Returns:
        Health score (0=critical, 100=excellent)
        
    Implementation Notes:
        - Weight different SMART attributes appropriately
        - Consider critical warning flags
        - Factor in error count
        - Use industry-standard thresholds
        - Return integer score 0-100
    """
```

### 5.3 Threshold Checking Functions
```python
def check_critical_thresholds(smart_data: SMARTData) -> List[Dict[str, Any]]:
    """
    Check SMART data against critical thresholds.
    
    Args:
        smart_data: Validated SMART data
        
    Returns:
        List of threshold violations with details:
            - attribute: str
            - current_value: Any
            - threshold: Any
            - severity: str ('warning', 'critical')
            - message: str
            
    Implementation Notes:
        - Define industry-standard thresholds
        - Check temperature limits
        - Check spare capacity thresholds
        - Check wear leveling indicators
        - Prioritize violations by severity
    """

def check_error_patterns(error_logs: List[ErrorLogEntry]) -> List[Dict[str, Any]]:
    """
    Analyze error logs for concerning patterns.
    
    Args:
        error_logs: List of error log entries
        
    Returns:
        List of detected patterns:
            - pattern_type: str
            - description: str
            - severity: str
            - affected_entries: List[int]
            
    Implementation Notes:
        - Look for recurring error types
        - Detect error rate increases
        - Identify specific LBA error patterns
        - Check for command timeout patterns
        - Classify pattern severity
    """
```

---

## 6. Output Formatting (`output/formatters.py`)

### 6.1 JSON Formatting Functions
```python
def format_health_snapshot_json(snapshot: HealthSnapshot, pretty: bool = True) -> str:
    """
    Format health snapshot as JSON string.
    
    Args:
        snapshot: Health snapshot to format
        pretty: Whether to use pretty printing
        
    Returns:
        JSON string representation
        
    Implementation Notes:
        - Use Pydantic's json() method
        - Handle datetime serialization
        - Include/exclude None values appropriately
        - Use proper indentation for pretty printing
        - Ensure valid JSON output
    """

def format_multiple_snapshots_json(snapshots: List[HealthSnapshot]) -> str:
    """
    Format multiple health snapshots as JSON array.
    
    Args:
        snapshots: List of health snapshots
        
    Returns:
        JSON array string
        
    Implementation Notes:
        - Create consistent JSON structure
        - Handle empty snapshot lists
        - Maintain snapshot ordering
        - Include metadata (collection time, device count)
        - Validate JSON structure
    """
```

### 6.2 CSV Formatting Functions
```python
def format_smart_data_csv(snapshots: List[HealthSnapshot]) -> str:
    """
    Format SMART data from multiple snapshots as CSV.
    
    Args:
        snapshots: List of health snapshots
        
    Returns:
        CSV string with SMART data
        
    Implementation Notes:
        - Create consistent column headers
        - Handle missing SMART data gracefully
        - Include device identification columns
        - Use appropriate CSV escaping
        - Sort rows by device path
    """

def format_error_summary_csv(snapshots: List[HealthSnapshot]) -> str:
    """
    Format error summary data as CSV.
    
    Args:
        snapshots: List of health snapshots
        
    Returns:
        CSV string with error summary
        
    Implementation Notes:
        - Aggregate error counts by device
        - Include error type breakdown
        - Add timestamp columns
        - Handle devices with no errors
        - Use consistent formatting
    """
```

### 6.3 Human-Readable Formatting Functions
```python
def format_health_summary_text(snapshot: HealthSnapshot) -> str:
    """
    Format health snapshot as human-readable text summary.
    
    Args:
        snapshot: Health snapshot to format
        
    Returns:
        Formatted text summary
        
    Implementation Notes:
        - Create clear section headers
        - Use appropriate units (GB, TB, °C)
        - Highlight critical issues
        - Include health score and status
        - Format tables for readability
    """

def format_device_comparison_table(snapshots: List[HealthSnapshot]) -> str:
    """
    Format multiple devices as comparison table.
    
    Args:
        snapshots: List of health snapshots
        
    Returns:
        Formatted comparison table
        
    Implementation Notes:
        - Create aligned columns
        - Include key health metrics
        - Highlight problematic devices
        - Sort by health score or device name
        - Use consistent formatting
    """
```

---

## 7. Configuration Management (`utils/config.py`)

### 7.1 Configuration Loading Functions
```python
def load_default_config() -> Dict[str, Any]:
    """
    Load default configuration settings.
    
    Returns:
        Dictionary with default configuration values
        
    Implementation Notes:
        - Define sensible defaults for all settings
        - Include timeout values, thresholds, paths
        - Set default output formats
        - Configure logging levels
        - Include health score weights
    """

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
        
    Implementation Notes:
        - Support both JSON and YAML formats
        - Validate configuration schema
        - Merge with default configuration
        - Handle missing optional settings
        - Log configuration loading
    """

def validate_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid: bool, validation_errors: List[str])
        
    Implementation Notes:
        - Check required configuration keys
        - Validate value types and ranges
        - Check file path accessibility
        - Validate threshold values
        - Return detailed validation errors
    """
```

### 7.2 Threshold Management Functions
```python
def get_smart_thresholds(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract SMART attribute thresholds from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary mapping SMART attributes to threshold values
        
    Implementation Notes:
        - Include warning and critical thresholds
        - Support percentage and absolute thresholds
        - Handle vendor-specific thresholds
        - Validate threshold consistency
        - Provide fallback defaults
    """

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
        
    Implementation Notes:
        - Validate threshold values
        - Ensure critical > warning for appropriate metrics
        - Update configuration in-place
        - Log threshold changes
        - Validate updated configuration
    """
```

---

## 8. Logging Configuration (`utils/logging_config.py`)

### 8.1 Logger Setup Functions
```python
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
        
    Implementation Notes:
        - Configure console and file handlers
        - Set appropriate log formats
        - Handle log rotation for file logging
        - Configure different levels for different modules
        - Include timestamp and module information
    """

def create_device_logger(device_path: str) -> logging.Logger:
    """
    Create device-specific logger.
    
    Args:
        device_path: NVMe device path
        
    Returns:
        Device-specific logger instance
        
    Implementation Notes:
        - Include device path in log messages
        - Use separate log files per device if configured
        - Inherit from main logger configuration
        - Add device-specific formatting
        - Handle device path sanitization for filenames
    """
```

### 8.2 Logging Utility Functions
```python
def log_command_execution(logger: logging.Logger, command: List[str], result: Dict[str, Any]) -> None:
    """
    Log nvme-cli command execution details.
    
    Args:
        logger: Logger instance
        command: Command arguments list
        result: Command execution result
        
    Implementation Notes:
        - Log command with sanitized arguments
        - Include execution time
        - Log success/failure status
        - Include relevant error details
        - Use appropriate log levels
    """

def log_health_collection(logger: logging.Logger, device_path: str, snapshot: HealthSnapshot) -> None:
    """
    Log health data collection summary.
    
    Args:
        logger: Logger instance
        device_path: Device path
        snapshot: Collected health snapshot
        
    Implementation Notes:
        - Log collection timestamp
        - Include key health metrics
        - Log any collection errors
        - Include health score if calculated
        - Use structured logging format
    """
```

---

## 9. Command Line Interface (`cli.py`)

### 9.1 CLI Command Functions
```python
def create_main_cli() -> click.Group:
    """
    Create main CLI group with all subcommands.
    
    Returns:
        Click group object
        
    Implementation Notes:
        - Use Click framework
        - Add global options (config, verbose, etc.)
        - Include help text and examples
        - Handle global exception catching
        - Set up logging based on verbosity
    """

def create_list_command() -> click.Command:
    """
    Create 'list' command to show available devices.
    
    Returns:
        Click command object
        
    Implementation Notes:
        - List all NVMe devices
        - Show basic device information
        - Support different output formats
        - Handle no devices found case
        - Include device accessibility status
    """

def create_health_command() -> click.Command:
    """
    Create 'health' command to collect health data.
    
    Returns:
        Click command object
        
    Options Required:
        - --device: Specific device path
        - --all: All devices
        - --output: Output file path
        - --format: Output format (json, csv, text)
        - --include-self-test: Include self-test data
        
    Implementation Notes:
        - Support single device or all devices
        - Handle output format selection
        - Include progress indicators for multiple devices
        - Support output to file or stdout
        - Handle permission errors gracefully
    """

def create_monitor_command() -> click.Command:
    """
    Create 'monitor' command for continuous monitoring.
    
    Returns:
        Click command object
        
    Options Required:
        - --interval: Monitoring interval in seconds
        - --duration: Total monitoring duration
        - --threshold-alerts: Enable threshold alerts
        - --output-dir: Directory for output files
        
    Implementation Notes:
        - Implement continuous monitoring loop
        - Support graceful shutdown (SIGINT)
        - Generate timestamped output files
        - Include real-time health status display
        - Handle device hot-plug events
    """

def create_self_test_command() -> click.Command:
    """
    Create 'self-test' command for device testing.
    
    Returns:
        Click command object
        
    Options Required:
        - --device: Device path
        - --type: Test type (short, extended, vendor)
        - --wait: Wait for completion
        - --abort: Abort running test
        
    Implementation Notes:
        - Support test start, abort, and status
        - Show progress for long-running tests
        - Handle test completion detection
        - Display test results
        - Support multiple devices
    """
```

### 9.2 CLI Utility Functions
```python
def validate_cli_arguments(ctx: click.Context, param: click.Parameter, value: Any) -> Any:
    """
    Validate CLI argument values.
    
    Args:
        ctx: Click context
        param: Parameter being validated
        value: Parameter value
        
    Returns:
        Validated parameter value
        
    Raises:
        click.BadParameter: If validation fails
        
    Implementation Notes:
        - Validate device paths
        - Check file permissions
        - Validate numeric ranges
        - Check mutually exclusive options
        - Provide helpful error messages
    """

def setup_cli_logging(verbose: int) -> None:
    """
    Set up logging based on CLI verbosity level.
    
    Args:
        verbose: Verbosity level (0=ERROR, 1=WARNING, 2=INFO, 3=DEBUG)
        
    Implementation Notes:
        - Map verbosity to log levels
        - Configure console output format
        - Disable verbose logging for quiet mode
        - Include progress indicators
        - Handle log output conflicts
    """

def handle_cli_exceptions(func: Callable) -> Callable:
    """
    Decorator to handle CLI exceptions gracefully.
    
    Args:
        func: CLI function to wrap
        
    Returns:
        Wrapped function with exception handling
        
    Implementation Notes:
        - Catch and format NVMe-specific exceptions
        - Provide user-friendly error messages
        - Include troubleshooting hints
        - Exit with appropriate error codes
        - Log detailed errors for debugging
    """
```

---

## 10. Integration and Testing Utilities

### 10.1 Mock Data Generation Functions
```python
def generate_mock_smart_data(device_path: str, health_status: str = "good") -> Dict[str, Any]:
    """
    Generate mock SMART data for testing.
    
    Args:
        device_path: Device path for mock data
        health_status: Health status ('good', 'warning', 'critical')
        
    Returns:
        Mock SMART data dictionary
        
    Implementation Notes:
        - Generate realistic SMART values
        - Adjust values based on health status
        - Include all required SMART fields
        - Use consistent data types
        - Support different device scenarios
    """

def generate_mock_error_logs(device_path: str, error_count: int = 0) -> List[Dict[str, Any]]:
    """
    Generate mock error log entries for testing.
    
    Args:
        device_path: Device path for mock data
        error_count: Number of error entries to generate
        
    Returns:
        List of mock error log entries
        
    Implementation Notes:
        - Generate realistic error patterns
        - Include various error types
        - Use sequential error IDs
        - Include timestamp progression
        - Support different error scenarios
    """
```

### 10.2 Test Utility Functions
```python
def create_test_device_environment() -> Dict[str, Any]:
    """
    Create mock device environment for testing.
    
    Returns:
        Dictionary with mock device setup
        
    Implementation Notes:
        - Mock multiple NVMe devices
        - Include various device states
        - Support permission testing
        - Create temporary device files
        - Include cleanup functionality
    """

def validate_output_format(output_data: str, format_type: str) -> bool:
    """
    Validate output format correctness.
    
    Args:
        output_data: Generated output data
        format_type: Expected format ('json', 'csv', 'text')
        
    Returns:
        True if format is valid
        
    Implementation Notes:
        - Parse and validate JSON structure
        - Check CSV column consistency
        - Validate text format readability
        - Check for required fields
        - Verify data type consistency
    """
```

---

## Implementation Guidelines

### Team Assignment Strategy
1. **Core Infrastructure** (1-2 developers)
   - Exception classes
   - Data models
   - Configuration management

2. **NVMe Interface** (2-3 developers)
   - Command execution functions
   - Device discovery
   - Health data collection

3. **Data Processing** (1-2 developers)
   - Data validation
   - Data transformation
   - Threshold checking

4. **Output and CLI** (1-2 developers)
   - Output formatters
   - CLI interface
   - Logging configuration

5. **Testing and Integration** (1 developer)
   - Mock data generation
   - Test utilities
   - Integration testing

### Development Standards
- Use type hints for all function parameters and return values
- Include comprehensive docstrings with Args, Returns, and Raises sections
- Implement proper error handling with custom exceptions
- Use Pydantic models for data validation
- Follow PEP 8 style guidelines
- Include unit tests for all utility functions
- Use logging instead of print statements
- Handle edge cases and error conditions gracefully

### Testing Requirements
- Unit tests for all utility functions
- Integration tests with mock nvme-cli commands
- Error condition testing
- Performance testing for large device counts
- CLI interface testing
- Output format validation testing

This specification provides a complete blueprint for implementing the NVMe health monitoring utility as a collaborative team project, with clear function boundaries and implementation guidelines.
