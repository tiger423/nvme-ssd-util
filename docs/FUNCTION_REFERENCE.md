# NVMe Formatting Functions - Complete Reference

## Quick Reference

| Function | Purpose | Parameters | Returns |
|----------|---------|------------|---------|
| `get_namespace_info()` | Get namespace details and LBA formats | device_path, namespace_id | Dict with namespace info |
| `format_namespace()` | Execute format operation | device_path, namespace_id, lbaf, secure_erase | Boolean success |
| `get_format_status()` | Monitor format progress | device_path | Dict with progress info |

## Detailed Function Documentation

### Core Formatting Functions

#### `get_namespace_info(device_path: str, namespace_id: int) -> Dict[str, Any]`

Retrieves comprehensive namespace information including supported LBA formats.

**Parameters:**
- `device_path` (str): NVMe device path (e.g., "/dev/nvme0")
- `namespace_id` (int): Namespace ID to query (typically 1)

**Returns:**
Dictionary containing:
```python
{
    "lbaf": [                    # LBA Format descriptors
        {
            "ds": 512,           # Data size in bytes
            "ms": 0,             # Metadata size in bytes  
            "rp": 0              # Relative performance (0=best, 3=worst)
        },
        {
            "ds": 4096,
            "ms": 0,
            "rp": 0
        }
    ],
    "flbas": {
        "format": 0,             # Current LBA format index
        "extended": 0            # Extended LBA format flag
    },
    "nsze": 1953525168,          # Namespace size in logical blocks
    "ncap": 1953525168           # Namespace capacity in logical blocks
}
```

**Exceptions:**
- `NVMeDeviceNotFoundError`: Device path invalid or doesn't exist
- `NVMeCommandError`: Command execution failed
- `NVMePermissionError`: Insufficient permissions

**Example Usage:**
```python
# Get namespace information
ns_info = get_namespace_info("/dev/nvme0", 1)

# Display current format
current_lbaf = ns_info.get('flbas', {}).get('format', 0)
print(f"Current LBA Format: {current_lbaf}")

# List available formats
for i, lbaf in enumerate(ns_info.get('lbaf', [])):
    if isinstance(lbaf, dict) and lbaf.get('ds', 0) > 0:
        data_size = lbaf.get('ds', 0)
        performance = lbaf.get('rp', 0)
        perf_desc = {0: "Best", 1: "Better", 2: "Good", 3: "Degraded"}[performance]
        print(f"LBAF {i}: {data_size} bytes, {perf_desc} performance")
```

#### `format_namespace(device_path: str, namespace_id: int, lbaf: int, secure_erase: str = "none") -> bool`

Executes NVMe format operation with specified LBA format and secure erase options.

**Parameters:**
- `device_path` (str): NVMe device path
- `namespace_id` (int): Namespace ID to format
- `lbaf` (int): LBA Format index (0-15)
- `secure_erase` (str): Secure erase level
  - `"none"`: No secure erase (fastest)
  - `"user"`: User data erase (recommended)
  - `"crypto"`: Cryptographic erase (most secure)

**Returns:**
- `True`: Format command successfully issued
- Raises exception on failure

**Exceptions:**
- `NVMeDeviceNotFoundError`: Device path invalid
- `NVMeCommandError`: Format command failed
- `NVMePermissionError`: Insufficient permissions
- `ValueError`: Invalid LBAF index or secure erase option

**Example Usage:**
```python
try:
    # Format with LBAF 0 and user data secure erase
    success = format_namespace("/dev/nvme0", 1, lbaf=0, secure_erase="user")
    if success:
        print("Format started successfully")
        
except NVMePermissionError:
    print("Permission denied - run with sudo")
except ValueError as e:
    print(f"Invalid parameter: {e}")
```

#### `get_format_status(device_path: str) -> Dict[str, Any]`

Monitors current format operation status and progress.

**Parameters:**
- `device_path` (str): NVMe device path

**Returns:**
Dictionary containing:
```python
{
    "is_formatting": False,      # True if format in progress
    "progress_percent": 100,     # Progress percentage (0-100)
    "estimated_completion": None # Future: estimated completion time
}
```

**Exceptions:**
- `NVMeDeviceNotFoundError`: Device path invalid
- `NVMeCommandError`: Status retrieval failed

**Example Usage:**
```python
import time

# Monitor format progress
while True:
    status = get_format_status("/dev/nvme0")
    
    if not status['is_formatting']:
        print("Format completed!")
        break
        
    progress = status['progress_percent']
    print(f"Format progress: {progress}%")
    time.sleep(5)  # Check every 5 seconds
```

### Supporting Functions

#### `check_nvme_cli_availability() -> bool`

Checks if nvme-cli utility is available on the system.

**Returns:**
- `True`: nvme-cli is available
- `False`: nvme-cli not found

**Example:**
```python
if not check_nvme_cli_availability():
    print("Please install nvme-cli:")
    print("  Ubuntu/Debian: sudo apt install nvme-cli")
    print("  RHEL/CentOS: sudo yum install nvme-cli")
    exit(1)
```

#### `list_nvme_devices() -> List[Dict[str, Any]]`

Lists all available NVMe devices on the system.

**Returns:**
List of device dictionaries:
```python
[
    {
        "device_path": "/dev/nvme0",
        "model": "Samsung SSD 980 PRO 1TB",
        "serial_number": "S5P2NG0N123456",
        "firmware_revision": "5B2QGXA7",
        "total_capacity": 1000204886016
    }
]
```

#### `get_device_namespaces(device_path: str) -> List[Dict[str, Any]]`

Gets all namespaces for a specific NVMe device.

**Parameters:**
- `device_path` (str): NVMe device path

**Returns:**
List of namespace dictionaries:
```python
[
    {
        "nsid": 1,
        "size": 1000204886016,
        "capacity": 1000204886016,
        "utilization": 0
    }
]
```

## Complete Workflow Examples

### Basic Format Workflow

```python
from nvme_health_monitor.core.nvme_interface import (
    check_nvme_cli_availability,
    get_namespace_info,
    format_namespace,
    get_format_status
)
import time

def basic_format_workflow(device_path: str, namespace_id: int, target_lbaf: int):
    """Complete format workflow with error handling."""
    
    # 1. Check prerequisites
    if not check_nvme_cli_availability():
        raise RuntimeError("nvme-cli not available")
    
    # 2. Get current namespace information
    print("Getting namespace information...")
    ns_info = get_namespace_info(device_path, namespace_id)
    
    current_lbaf = ns_info.get('flbas', {}).get('format', 0)
    print(f"Current LBAF: {current_lbaf}")
    
    # 3. Validate target LBAF
    available_lbafs = []
    for i, lbaf in enumerate(ns_info.get('lbaf', [])):
        if isinstance(lbaf, dict) and lbaf.get('ds', 0) > 0:
            available_lbafs.append(i)
    
    if target_lbaf not in available_lbafs:
        raise ValueError(f"LBAF {target_lbaf} not available. Available: {available_lbafs}")
    
    # 4. Start format operation
    print(f"Starting format with LBAF {target_lbaf}...")
    success = format_namespace(device_path, namespace_id, target_lbaf, secure_erase="user")
    
    if not success:
        raise RuntimeError("Failed to start format operation")
    
    # 5. Monitor progress
    print("Monitoring format progress...")
    start_time = time.time()
    timeout = 1800  # 30 minutes
    
    while time.time() - start_time < timeout:
        status = get_format_status(device_path)
        
        if not status['is_formatting']:
            print("Format completed successfully!")
            break
            
        progress = status['progress_percent']
        elapsed = (time.time() - start_time) / 60
        print(f"Progress: {progress}% (elapsed: {elapsed:.1f} min)")
        
        time.sleep(10)  # Check every 10 seconds
    else:
        raise TimeoutError("Format operation timed out")
    
    # 6. Verify result
    print("Verifying format result...")
    final_info = get_namespace_info(device_path, namespace_id)
    final_lbaf = final_info.get('flbas', {}).get('format', -1)
    
    if final_lbaf == target_lbaf:
        print(f"Format verification successful! LBAF is now {final_lbaf}")
        return True
    else:
        print(f"Format verification failed! Expected {target_lbaf}, got {final_lbaf}")
        return False

# Usage example
try:
    success = basic_format_workflow("/dev/nvme0", 1, 0)
    if success:
        print("Format workflow completed successfully")
except Exception as e:
    print(f"Format workflow failed: {e}")
```

### Advanced Format with LBA Format Selection

```python
def select_optimal_lbaf(device_path: str, namespace_id: int, prefer_4k: bool = True) -> int:
    """Select optimal LBA format based on preferences and performance."""
    
    ns_info = get_namespace_info(device_path, namespace_id)
    lba_formats = ns_info.get('lbaf', [])
    
    if not lba_formats:
        return 0  # Default fallback
    
    candidates = []
    
    for i, lbaf in enumerate(lba_formats):
        if isinstance(lbaf, dict) and lbaf.get('ds', 0) > 0:
            data_size = lbaf.get('ds', 0)
            performance = lbaf.get('rp', 3)  # Default to worst performance
            metadata_size = lbaf.get('ms', 0)
            
            # Calculate score (lower is better)
            score = performance  # Performance weight
            
            # Prefer requested sector size
            if prefer_4k and data_size == 4096:
                score -= 2  # Bonus for 4K
            elif not prefer_4k and data_size == 512:
                score -= 2  # Bonus for 512B
            
            # Prefer no metadata
            if metadata_size == 0:
                score -= 1
            
            candidates.append((i, score, data_size, performance))
    
    if not candidates:
        return 0
    
    # Sort by score (best first)
    candidates.sort(key=lambda x: x[1])
    
    best_lbaf, best_score, data_size, performance = candidates[0]
    
    print(f"Selected LBAF {best_lbaf}: {data_size} bytes, performance level {performance}")
    return best_lbaf

# Usage
optimal_lbaf = select_optimal_lbaf("/dev/nvme0", 1, prefer_4k=True)
basic_format_workflow("/dev/nvme0", 1, optimal_lbaf)
```

### Error Handling Patterns

```python
from nvme_health_monitor.models.exceptions import (
    NVMeCommandError,
    NVMeDeviceNotFoundError,
    NVMePermissionError,
    NVMeTimeoutError
)

def robust_format_operation(device_path: str, namespace_id: int, lbaf: int):
    """Format operation with comprehensive error handling."""
    
    try:
        # Attempt format operation
        success = format_namespace(device_path, namespace_id, lbaf, secure_erase="user")
        
        if not success:
            print("Format command failed to start")
            return False
        
        # Monitor with timeout and retry logic
        max_timeout = 3600  # 1 hour
        check_interval = 10  # 10 seconds
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        start_time = time.time()
        
        while time.time() - start_time < max_timeout:
            try:
                status = get_format_status(device_path)
                consecutive_errors = 0  # Reset error counter
                
                if not status['is_formatting']:
                    print("Format completed successfully!")
                    return True
                
                progress = status['progress_percent']
                elapsed = (time.time() - start_time) / 60
                print(f"Progress: {progress}% (elapsed: {elapsed:.1f} min)")
                
            except NVMeCommandError as e:
                consecutive_errors += 1
                print(f"Status check error ({consecutive_errors}/{max_consecutive_errors}): {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    print("Too many consecutive errors, aborting")
                    return False
                
                # Wait longer after errors
                time.sleep(30)
                continue
            
            time.sleep(check_interval)
        
        print("Format operation timed out")
        return False
        
    except NVMeDeviceNotFoundError as e:
        print(f"Device not found: {e}")
        print("Check device path and ensure device is connected")
        return False
        
    except NVMePermissionError as e:
        print(f"Permission denied: {e}")
        print("Try running with sudo or add user to nvme group:")
        print("  sudo usermod -a -G nvme $USER")
        return False
        
    except NVMeTimeoutError as e:
        print(f"Command timeout: {e}")
        print("Device may be busy or unresponsive")
        return False
        
    except ValueError as e:
        print(f"Invalid parameter: {e}")
        return False
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

# Usage with error handling
if robust_format_operation("/dev/nvme0", 1, 0):
    print("Format operation completed successfully")
else:
    print("Format operation failed")
```

## Performance and Timing

### Expected Format Times

| Drive Size | Secure Erase | Expected Time | Notes |
|------------|--------------|---------------|-------|
| 256 GB | none | 30s - 2min | Quick format |
| 256 GB | user | 1min - 5min | Secure erase adds time |
| 512 GB | none | 1min - 4min | Scales with capacity |
| 512 GB | user | 2min - 8min | |
| 1 TB | none | 2min - 8min | |
| 1 TB | user | 5min - 15min | |
| 2 TB | user | 10min - 30min | Large drives take longer |

### Optimization Tips

1. **Choose appropriate secure erase level:**
   ```python
   # For maximum speed (testing only)
   format_namespace(device, ns, lbaf, secure_erase="none")
   
   # For balanced security/speed (recommended)
   format_namespace(device, ns, lbaf, secure_erase="user")
   
   # For maximum security (slow)
   format_namespace(device, ns, lbaf, secure_erase="crypto")
   ```

2. **Adjust monitoring frequency:**
   ```python
   # For large drives, check less frequently
   if drive_size_gb > 1000:
       check_interval = 30  # 30 seconds
   else:
       check_interval = 10  # 10 seconds
   ```

3. **Set appropriate timeouts:**
   ```python
   def calculate_timeout(drive_size_gb: int, secure_erase: str) -> int:
       """Calculate appropriate timeout based on drive size and erase type."""
       base_time = drive_size_gb * 0.5  # 30 seconds per 100GB
       
       if secure_erase == "user":
           base_time *= 2
       elif secure_erase == "crypto":
           base_time *= 3
       
       return max(300, int(base_time * 60))  # Minimum 5 minutes
   ```

This reference provides comprehensive documentation for all NVMe formatting functions with practical examples and best practices.
