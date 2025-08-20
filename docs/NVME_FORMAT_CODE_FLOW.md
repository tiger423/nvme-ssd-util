# NVMe SSD Formatting - Code Flow and Function Documentation

## Overview

This document provides detailed code flow diagrams and function explanations for the NVMe SSD formatting examples. The implementation demonstrates how to format NVMe SSDs with LBAF (Logical Block Address Format) support and monitor the format process until completion.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    NVMe Formatting Architecture                 │
├─────────────────────────────────────────────────────────────────┤
│  Examples Layer                                                 │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ Educational     │ │ Interactive     │ │ Simple Pattern  │   │
│  │ Example         │ │ Tool            │ │ Example         │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  Core NVMe Interface Functions                                 │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │get_namespace_   │ │format_namespace │ │get_format_      │   │
│  │info()           │ │()               │ │status()         │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  Base NVMe Operations                                           │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │execute_nvme_    │ │validate_device_ │ │list_nvme_       │   │
│  │command()        │ │path()           │ │devices()        │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  System Layer (nvme-cli)                                       │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │nvme id-ns       │ │nvme format      │ │nvme smart-log   │   │
│  │(namespace info) │ │(format command) │ │(progress check) │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Code Flow Diagrams

### 1. Educational Example Flow (`nvme_format_example.py`)

```
START
  │
  ├─ Check nvme-cli availability
  │  └─ check_nvme_cli_availability()
  │
  ├─ Discover NVMe devices
  │  └─ list_nvme_devices()
  │     ├─ Execute: nvme list --output-format=json
  │     └─ Parse device information
  │
  ├─ Select device and namespace
  │  └─ get_device_namespaces(device_path)
  │     ├─ Execute: nvme list-ns device_path --output-format=json
  │     └─ Parse namespace list
  │
  ├─ Get namespace information
  │  └─ get_namespace_info(device_path, namespace_id)
  │     ├─ Execute: nvme id-ns device_path n namespace_id --output-format=json
  │     ├─ Parse LBA format information
  │     └─ Display available formats
  │
  ├─ Display safety warnings
  │  └─ Show data destruction warnings
  │
  ├─ [COMMENTED] Format execution
  │  └─ format_namespace(device_path, namespace_id, lbaf, secure_erase)
  │     ├─ Validate parameters
  │     ├─ Execute: nvme format device_path n namespace_id --lbaf=X --ses=Y
  │     └─ Return success status
  │
  ├─ [COMMENTED] Monitor progress
  │  └─ wait_for_format_completion(device_path, timeout)
  │     ├─ Loop: get_format_status(device_path)
  │     │  ├─ Execute: nvme smart-log device_path --output-format=json
  │     │  ├─ Check format_progress_indicator
  │     │  └─ Return progress percentage
  │     ├─ Display progress updates
  │     └─ Exit when progress = 100%
  │
  └─ Display completion message
END
```

### 2. Interactive Tool Flow (`nvme_format_interactive.py`)

```
START
  │
  ├─ Initialize NVMeFormatter class
  │  └─ Setup logging and initialize variables
  │
  ├─ Check prerequisites
  │  └─ check_nvme_cli_availability()
  │
  ├─ Device Selection Menu
  │  └─ list_and_select_device()
  │     ├─ list_nvme_devices()
  │     ├─ Display device table
  │     ├─ User input validation
  │     └─ Return selected device
  │
  ├─ Namespace Selection Menu
  │  └─ select_namespace(device_path)
  │     ├─ get_device_namespaces(device_path)
  │     ├─ Display namespace table
  │     ├─ User input validation
  │     └─ Return selected namespace ID
  │
  ├─ LBA Format Selection Menu
  │  └─ select_lba_format(device_path, namespace_id)
  │     ├─ get_namespace_info(device_path, namespace_id)
  │     ├─ Parse and display LBA formats
  │     ├─ Show current format and performance info
  │     ├─ User input validation
  │     └─ Return selected LBAF index
  │
  ├─ Safety Confirmation Process
  │  └─ confirm_format(device_path, namespace_id, lbaf)
  │     ├─ Display critical warnings
  │     ├─ Require exact text confirmation
  │     ├─ Final YES/NO confirmation
  │     └─ Return confirmation status
  │
  ├─ Format Execution
  │  └─ perform_format(device_path, namespace_id, lbaf)
  │     ├─ format_namespace(device_path, namespace_id, lbaf, "user")
  │     ├─ Handle errors and exceptions
  │     └─ Return execution status
  │
  ├─ Progress Monitoring
  │  └─ monitor_format_progress(device_path, timeout)
  │     ├─ Real-time progress display
  │     ├─ Timeout handling
  │     ├─ Error recovery
  │     └─ Return completion status
  │
  ├─ Format Verification
  │  └─ verify_format(device_path, namespace_id, expected_lbaf)
  │     ├─ get_namespace_info(device_path, namespace_id)
  │     ├─ Compare expected vs actual LBAF
  │     └─ Return verification result
  │
  └─ Display final results and next steps
END
```

### 3. Simple Pattern Flow (`simple_format_example.py`)

```
START
  │
  ├─ Check nvme-cli availability
  │  └─ check_nvme_cli_availability()
  │
  ├─ Get namespace information
  │  └─ get_namespace_info(DEVICE_PATH, NAMESPACE_ID)
  │     ├─ Display current LBA format
  │     └─ Show available formats
  │
  ├─ [COMMENTED] Format execution
  │  └─ format_namespace(DEVICE_PATH, NAMESPACE_ID, TARGET_LBAF, SECURE_ERASE)
  │
  ├─ [COMMENTED] Progress monitoring
  │  └─ Monitor format completion with timeout
  │
  ├─ [COMMENTED] Verification
  │  └─ Verify format was applied correctly
  │
  └─ Display usage instructions
END
```

## Core Function Documentation

### 1. `get_namespace_info(device_path: str, namespace_id: int) -> Dict[str, Any]`

**Purpose**: Retrieves detailed namespace information including supported LBA formats.

**Parameters**:
- `device_path`: NVMe device path (e.g., "/dev/nvme0")
- `namespace_id`: Namespace ID to query (typically 1)

**Returns**: Dictionary containing:
- `lbaf`: Array of LBA format descriptors
- `flbas`: Current format and extended LBA settings
- `nsze`: Namespace size in logical blocks
- `ncap`: Namespace capacity in logical blocks

**Internal Flow**:
```python
def get_namespace_info(device_path: str, namespace_id: int) -> Dict[str, Any]:
    # 1. Validate device path exists
    if not validate_device_path(device_path):
        raise NVMeDeviceNotFoundError(f"Invalid device: {device_path}")
    
    # 2. Construct nvme-cli command
    command = ['nvme', 'id-ns', f'{device_path}n{namespace_id}', '--output-format=json']
    
    # 3. Execute command with error handling
    result = execute_nvme_command(command)
    
    # 4. Validate command success
    if not result['success']:
        raise NVMeCommandError("Failed to get namespace info", ...)
    
    # 5. Return parsed JSON data
    return result['data']
```

**LBA Format Structure**:
```json
{
  "lbaf": [
    {
      "ms": 0,     // Metadata size in bytes
      "ds": 512,   // Data size in bytes (sector size)
      "rp": 0      // Relative performance (0=best, 3=degraded)
    },
    {
      "ms": 0,
      "ds": 4096,
      "rp": 0
    }
  ],
  "flbas": {
    "format": 0,   // Current LBA format index
    "extended": 0  // Extended LBA format flag
  }
}
```

### 2. `format_namespace(device_path: str, namespace_id: int, lbaf: int, secure_erase: str = "none") -> bool`

**Purpose**: Formats NVMe namespace with specified LBA format and secure erase options.

**Parameters**:
- `device_path`: NVMe device path
- `namespace_id`: Namespace ID to format
- `lbaf`: LBA Format index (0-15)
- `secure_erase`: Secure erase level ("none", "user", "crypto")

**Returns**: `True` if format command was successfully issued

**Internal Flow**:
```python
def format_namespace(device_path: str, namespace_id: int, lbaf: int, secure_erase: str = "none") -> bool:
    # 1. Validate device path
    if not validate_device_path(device_path):
        raise NVMeDeviceNotFoundError(f"Invalid device: {device_path}")
    
    # 2. Validate LBAF range
    if not (0 <= lbaf <= 15):
        raise ValueError(f"Invalid LBAF index: {lbaf}")
    
    # 3. Map secure erase options
    secure_erase_codes = {'none': '0', 'user': '1', 'crypto': '2'}
    if secure_erase not in secure_erase_codes:
        raise ValueError(f"Invalid secure erase: {secure_erase}")
    
    # 4. Construct format command
    command = [
        'nvme', 'format', f'{device_path}n{namespace_id}',
        f'--lbaf={lbaf}',
        f'--ses={secure_erase_codes[secure_erase]}'
    ]
    
    # 5. Execute with extended timeout (format can take time)
    result = execute_nvme_command(command, timeout=300)
    
    # 6. Validate success
    if not result['success']:
        raise NVMeCommandError("Format failed", ...)
    
    return True
```

**Secure Erase Options**:
- `"none"` (0): No secure erase performed
- `"user"` (1): User data erase - cryptographically erase user data
- `"crypto"` (2): Cryptographic erase - change encryption keys

### 3. `get_format_status(device_path: str) -> Dict[str, Any]`

**Purpose**: Monitors current format operation status and progress.

**Parameters**:
- `device_path`: NVMe device path

**Returns**: Dictionary containing:
- `is_formatting`: Boolean indicating if format is in progress
- `progress_percent`: Integer progress percentage (0-100)
- `estimated_completion`: Optional completion time estimate

**Internal Flow**:
```python
def get_format_status(device_path: str) -> Dict[str, Any]:
    # 1. Validate device path
    if not validate_device_path(device_path):
        raise NVMeDeviceNotFoundError(f"Invalid device: {device_path}")
    
    # 2. Get SMART log data
    smart_data = get_smart_log(device_path)
    
    # 3. Initialize status structure
    status = {
        'is_formatting': False,
        'progress_percent': 100,
        'estimated_completion': None
    }
    
    # 4. Check format progress indicator
    if 'format_progress_indicator' in smart_data:
        progress = smart_data.get('format_progress_indicator', 100)
        status['is_formatting'] = progress < 100
        status['progress_percent'] = progress
    
    return status
```

**Progress Monitoring Logic**:
- Format progress is tracked via SMART log `format_progress_indicator` field
- Progress ranges from 0% (just started) to 100% (completed)
- Progress of 100% or missing indicator means format is complete
- Some drives may not support progress reporting (always shows 100%)

## Integration Patterns

### Pattern 1: Basic Format Operation

```python
from nvme_health_monitor.core.nvme_interface import (
    get_namespace_info, format_namespace, get_format_status
)

# 1. Check current format
ns_info = get_namespace_info("/dev/nvme0", 1)
current_lbaf = ns_info.get('flbas', {}).get('format', 0)
print(f"Current LBAF: {current_lbaf}")

# 2. Start format operation
success = format_namespace("/dev/nvme0", 1, lbaf=0, secure_erase="user")
if success:
    print("Format started successfully")

# 3. Monitor progress
while True:
    status = get_format_status("/dev/nvme0")
    if not status['is_formatting']:
        print("Format completed!")
        break
    print(f"Progress: {status['progress_percent']}%")
    time.sleep(5)
```

### Pattern 2: Error Handling

```python
from nvme_health_monitor.models.exceptions import (
    NVMeCommandError, NVMeDeviceNotFoundError, NVMePermissionError
)

try:
    # Format operation
    format_namespace("/dev/nvme0", 1, lbaf=0)
    
except NVMeDeviceNotFoundError as e:
    print(f"Device not found: {e}")
    
except NVMePermissionError as e:
    print(f"Permission denied: {e}")
    print("Try running with sudo")
    
except NVMeCommandError as e:
    print(f"Format failed: {e}")
    print(f"Command: {e.command}")
    print(f"Return code: {e.return_code}")
```

### Pattern 3: LBA Format Selection

```python
def select_optimal_lbaf(device_path: str, namespace_id: int) -> int:
    """Select optimal LBA format based on performance and size."""
    ns_info = get_namespace_info(device_path, namespace_id)
    
    if 'lbaf' not in ns_info:
        return 0  # Default to LBAF 0
    
    best_lbaf = 0
    best_performance = 3  # Worst performance
    
    for i, lbaf in enumerate(ns_info['lbaf']):
        if isinstance(lbaf, dict) and lbaf.get('ds', 0) > 0:
            performance = lbaf.get('rp', 3)  # Relative performance
            data_size = lbaf.get('ds', 0)
            
            # Prefer 4K sectors with best performance
            if data_size == 4096 and performance <= best_performance:
                best_lbaf = i
                best_performance = performance
            # Fallback to 512B sectors
            elif data_size == 512 and performance < best_performance:
                best_lbaf = i
                best_performance = performance
    
    return best_lbaf
```

## Performance Considerations

### Format Time Estimates

| Drive Size | Expected Format Time | Factors |
|------------|---------------------|---------|
| 256 GB     | 1-5 minutes        | Drive type, secure erase level |
| 512 GB     | 2-10 minutes       | Interface speed (PCIe gen) |
| 1 TB       | 5-20 minutes       | Controller efficiency |
| 2 TB       | 10-40 minutes      | Background operations |

### Optimization Tips

1. **Choose appropriate secure erase level**:
   - `"none"`: Fastest, minimal security
   - `"user"`: Balanced, good security
   - `"crypto"`: Slowest, maximum security

2. **Monitor system load**:
   - Format operations are I/O intensive
   - Avoid other disk operations during format

3. **Use appropriate timeouts**:
   - Small drives: 10-15 minutes
   - Large drives: 30-60 minutes
   - Enterprise drives: May take longer

## Error Scenarios and Recovery

### Common Error Conditions

1. **Device Busy**: Another process is using the device
   ```
   Solution: Stop applications, unmount filesystems
   ```

2. **Permission Denied**: Insufficient privileges
   ```
   Solution: Run with sudo or add user to nvme group
   ```

3. **Invalid LBAF**: Requested format not supported
   ```
   Solution: Check available formats with get_namespace_info()
   ```

4. **Format Timeout**: Operation takes longer than expected
   ```
   Solution: Increase timeout, check device health
   ```

### Recovery Procedures

```python
def safe_format_with_recovery(device_path: str, namespace_id: int, lbaf: int):
    """Format with automatic error recovery."""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Attempt format
            success = format_namespace(device_path, namespace_id, lbaf)
            if success:
                return True
                
        except NVMePermissionError:
            print("Permission error - run with sudo")
            return False
            
        except NVMeCommandError as e:
            retry_count += 1
            if retry_count < max_retries:
                print(f"Format failed, retrying ({retry_count}/{max_retries})...")
                time.sleep(10)  # Wait before retry
            else:
                print(f"Format failed after {max_retries} attempts: {e}")
                return False
    
    return False
```

## Testing and Validation

### Unit Test Examples

```python
import unittest
from unittest.mock import patch, MagicMock

class TestNVMeFormatting(unittest.TestCase):
    
    @patch('nvme_health_monitor.core.nvme_interface.execute_nvme_command')
    def test_get_namespace_info_success(self, mock_execute):
        # Mock successful command execution
        mock_execute.return_value = {
            'success': True,
            'data': {
                'lbaf': [{'ds': 512, 'ms': 0, 'rp': 0}],
                'flbas': {'format': 0}
            }
        }
        
        result = get_namespace_info('/dev/nvme0', 1)
        
        self.assertIn('lbaf', result)
        self.assertEqual(result['lbaf'][0]['ds'], 512)
    
    @patch('nvme_health_monitor.core.nvme_interface.execute_nvme_command')
    def test_format_namespace_invalid_lbaf(self, mock_execute):
        with self.assertRaises(ValueError):
            format_namespace('/dev/nvme0', 1, lbaf=16)  # Invalid LBAF
```

### Integration Test Pattern

```python
def test_complete_format_workflow():
    """Test complete format workflow on test device."""
    device_path = "/dev/nvme0"  # Use test device only!
    namespace_id = 1
    
    # 1. Get initial state
    initial_info = get_namespace_info(device_path, namespace_id)
    initial_lbaf = initial_info.get('flbas', {}).get('format', 0)
    
    # 2. Select different LBAF for testing
    available_lbafs = [i for i, lbaf in enumerate(initial_info.get('lbaf', []))
                      if isinstance(lbaf, dict) and lbaf.get('ds', 0) > 0]
    
    if len(available_lbafs) < 2:
        print("Not enough LBA formats for testing")
        return
    
    target_lbaf = available_lbafs[1] if available_lbafs[0] == initial_lbaf else available_lbafs[0]
    
    # 3. Perform format
    success = format_namespace(device_path, namespace_id, target_lbaf)
    assert success, "Format command failed"
    
    # 4. Monitor completion
    timeout = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status = get_format_status(device_path)
        if not status['is_formatting']:
            break
        time.sleep(5)
    else:
        assert False, "Format timeout"
    
    # 5. Verify result
    final_info = get_namespace_info(device_path, namespace_id)
    final_lbaf = final_info.get('flbas', {}).get('format', -1)
    
    assert final_lbaf == target_lbaf, f"Expected LBAF {target_lbaf}, got {final_lbaf}"
    
    print("Format workflow test completed successfully")
```

## Security Considerations

### Data Protection

1. **Multiple Confirmations**: Interactive tool requires exact text confirmation
2. **Device Validation**: Strict device path validation prevents accidents
3. **Secure Erase Options**: Support for cryptographic data erasure
4. **Audit Logging**: All operations are logged for security auditing

### Access Control

```python
def check_format_permissions(device_path: str) -> bool:
    """Check if user has permission to format device."""
    try:
        # Test with a safe read operation first
        get_namespace_info(device_path, 1)
        return True
    except NVMePermissionError:
        return False
```

### Safe Defaults

- Default secure erase: `"user"` (not `"none"`)
- Default timeout: Conservative values to prevent premature termination
- Default LBAF: 0 (most compatible format)
- Validation: All parameters validated before execution

This comprehensive documentation provides developers with everything needed to understand, implement, and extend the NVMe formatting functionality safely and effectively.
