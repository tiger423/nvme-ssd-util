# NVMe SSD Formatting Examples

This directory contains example scripts demonstrating how to use the NVMe Health Monitor utility to format NVMe SSDs with LBAF (Logical Block Address Format) support.

## 📚 Documentation

For detailed code flow diagrams and function explanations, see:
- **[Complete Code Flow Documentation](../docs/NVME_FORMAT_CODE_FLOW.md)** - Comprehensive technical documentation with workflow diagrams
- **[Function Reference](../docs/FUNCTION_REFERENCE.md)** - Detailed API documentation for all NVMe functions
- **[Integration Patterns](../docs/NVME_FORMAT_CODE_FLOW.md#integration-patterns)** - Code examples for developers

## ⚠️ CRITICAL WARNING

**These examples involve DESTRUCTIVE operations that will PERMANENTLY ERASE ALL DATA on the target NVMe device. Use with extreme caution and ensure you have proper backups.**

## Examples Overview

### 1. `nvme_format_example.py` - Basic Example
A comprehensive example that demonstrates the complete workflow:
- Device discovery and selection
- Namespace enumeration
- LBA format inspection
- Format operation (commented out for safety)
- Progress monitoring
- Result verification

**Usage:**
```bash
cd /path/to/nvme-ssd-util
python examples/nvme_format_example.py
```

### 2. `nvme_format_interactive.py` - Interactive Tool
A full-featured interactive tool with:
- Menu-driven device selection
- LBA format selection with detailed information
- Multiple safety confirmations
- Real-time progress monitoring
- Automatic verification

**Usage:**
```bash
cd /path/to/nvme-ssd-util
sudo python examples/nvme_format_interactive.py
```

### 3. `simple_format_example.py` - Simple Pattern
A minimal example showing the basic programming pattern:
- Prerequisites checking
- Namespace information retrieval
- Format command execution
- Progress monitoring
- Result verification

**Usage:**
```bash
cd /path/to/nvme-ssd-util
python examples/simple_format_example.py
```

## Prerequisites

1. **nvme-cli installed:**
   ```bash
   # Ubuntu/Debian
   sudo apt install nvme-cli
   
   # RHEL/CentOS/Fedora
   sudo yum install nvme-cli
   # or
   sudo dnf install nvme-cli
   ```

2. **Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Appropriate permissions:**
   - Root access (sudo) is typically required for NVMe operations
   - Alternatively, ensure your user is in the `nvme` group

## Key Functions Used

### Device Management
- `check_nvme_cli_availability()` - Verify nvme-cli is installed
- `list_nvme_devices()` - List all NVMe devices
- `get_device_namespaces()` - Get namespaces for a device
- `validate_device_path()` - Validate device path format

### Namespace Operations
- `get_namespace_info()` - Get detailed namespace information including LBA formats
- `format_namespace()` - Format namespace with specified LBAF
- `get_format_status()` - Monitor format progress

### Monitoring and Verification
- `get_smart_log()` - Get SMART data for health monitoring
- Progress monitoring loops with timeout handling
- Format verification by comparing expected vs actual LBAF

## LBA Format (LBAF) Overview

LBA Format determines the block size and metadata configuration:

- **LBAF 0**: Usually 512 bytes (traditional sector size)
- **LBAF 1**: Often 4096 bytes (4K sectors, better performance)
- **LBAF 2+**: Vendor-specific formats, may include metadata

### Choosing the Right LBAF

1. **512-byte sectors (LBAF 0)**: 
   - Maximum compatibility
   - Works with all operating systems
   - Slightly lower performance

2. **4K sectors (LBAF 1)**:
   - Better performance for modern workloads
   - More efficient space utilization
   - Requires OS support (most modern systems)

3. **Metadata formats**:
   - Include additional protection information
   - Used for enterprise features
   - May require special application support

## Safety Guidelines

### Before Formatting

1. **Backup all important data** - formatting is irreversible
2. **Verify the correct device** - double-check device paths
3. **Understand the implications** - formatting affects the entire namespace
4. **Test on non-production systems** first

### During Formatting

1. **Don't interrupt the process** - can corrupt the device
2. **Monitor progress** - use the provided monitoring functions
3. **Be patient** - large drives can take significant time
4. **Have a recovery plan** - know how to restore if needed

### After Formatting

1. **Verify the results** - check that the format was successful
2. **Create partitions** - format doesn't create filesystems
3. **Test thoroughly** - ensure the device works as expected

## Error Handling

The examples include comprehensive error handling for:

- **Permission errors**: Run with sudo or check user groups
- **Device not found**: Verify device path and connection
- **Command failures**: Check nvme-cli installation and device health
- **Timeout errors**: Increase timeout values for large devices

## Integration with NVMe Health Monitor

These examples integrate with the full NVMe Health Monitor utility:

```python
from nvme_health_monitor.core.nvme_interface import *
from nvme_health_monitor.models.exceptions import *
from nvme_health_monitor.utils.logging_config import setup_logging
from nvme_health_monitor.output.formatters import *
```

This allows you to:
- Use comprehensive error handling
- Leverage logging capabilities
- Format output for reports
- Integrate with monitoring systems

## Troubleshooting

### Common Issues

1. **Permission denied**:
   ```bash
   sudo python examples/nvme_format_interactive.py
   ```

2. **nvme-cli not found**:
   ```bash
   sudo apt install nvme-cli  # Ubuntu/Debian
   sudo yum install nvme-cli  # RHEL/CentOS
   ```

3. **Device not found**:
   - Check `lsblk` or `nvme list` to verify device paths
   - Ensure the device is properly connected

4. **Format timeout**:
   - Increase timeout values in the scripts
   - Large SSDs can take 30+ minutes to format

### Getting Help

1. Check device status: `nvme smart-log /dev/nvmeX`
2. List devices: `nvme list`
3. Check system logs: `dmesg | grep nvme`
4. Verify permissions: `ls -la /dev/nvme*`

## License

These examples are part of the NVMe Health Monitor utility and follow the same license terms.

## Contributing

When contributing new examples:
1. Include comprehensive safety warnings
2. Add proper error handling
3. Document all parameters and options
4. Test on multiple device types
5. Follow the established code style
