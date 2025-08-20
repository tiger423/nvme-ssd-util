# Health Status Checker - Code Flow and Function Documentation

## Overview

The `health_status_checker.py` example demonstrates comprehensive NVMe SSD health assessment with multi-parameter analysis, health scoring, and actionable recommendations. This tool evaluates critical health indicators and provides a pass/fail determination for SSD health status.

## Code Architecture

```
NVMeHealthChecker
├── Device Discovery & Validation
├── SMART Data Collection
├── Multi-Parameter Health Analysis
├── Health Score Calculation
├── Status Determination
└── Report Generation & Recommendations
```

## Detailed Code Flow

### 1. Initialization and Setup

```python
def __init__(self):
    """Initialize the health checker with configurable thresholds."""
    self.temperature_warning = 70    # °C
    self.temperature_critical = 85   # °C
    self.spare_warning = 10         # %
    self.spare_critical = 5         # %
    self.used_warning = 80          # %
    self.used_critical = 95         # %
```

**Purpose**: Sets up configurable health thresholds for different parameters.

**Key Features**:
- Temperature thresholds (warning/critical)
- Available spare capacity limits
- Percentage used thresholds
- Extensible threshold system

### 2. Main Health Analysis Function

```python
def check_device_health(self, device_path: str) -> HealthAssessment:
```

**Flow Diagram**:
```
Device Path Input
       ↓
Device Validation
       ↓
SMART Data Collection ← get_smart_log()
       ↓              ← get_controller_info()
Device Info Collection
       ↓
Multi-Parameter Analysis
├── Temperature Analysis
├── Available Spare Analysis  
├── Percentage Used Analysis
├── Critical Warnings Analysis
├── Power-On Hours Analysis
└── Media Errors Analysis
       ↓
Health Score Calculation
       ↓
Overall Status Determination
       ↓
Recommendations Generation
       ↓
HealthAssessment Object
```

**Function Breakdown**:

#### 2.1 Data Collection Phase
```python
smart_data = get_smart_log(device_path)
device_info = get_controller_info(device_path)
```

- **`get_smart_log()`**: Retrieves SMART attributes including temperature, spare capacity, wear level
- **`get_controller_info()`**: Gets device identification and controller capabilities

#### 2.2 Analysis Functions

##### Temperature Analysis
```python
def _analyze_temperature(self, smart_data: Dict) -> HealthMetric:
```

**Logic Flow**:
```
Extract Temperature → Convert to Celsius → Compare Thresholds → Determine Status
```

**Implementation Details**:
- Extracts `temperature` from SMART data
- Handles multiple temperature units (Kelvin/Celsius)
- Applies warning/critical thresholds
- Returns status with recommendations

##### Available Spare Analysis
```python
def _analyze_available_spare(self, smart_data: Dict) -> HealthMetric:
```

**Logic Flow**:
```
Extract Spare % → Compare to Thresholds → Assess Remaining Life → Generate Status
```

**Key Metrics**:
- `available_spare`: Current spare capacity percentage
- `available_spare_threshold`: Device-specific threshold
- Status determination based on remaining spare blocks

##### Percentage Used Analysis
```python
def _analyze_percentage_used(self, smart_data: Dict) -> HealthMetric:
```

**Logic Flow**:
```
Extract Used % → Calculate Remaining Life → Apply Thresholds → Determine Wear Level
```

**Wear Level Categories**:
- 0-50%: Excellent condition
- 51-80%: Good condition (warning threshold)
- 81-95%: High wear (critical threshold)
- 95%+: End of life approaching

##### Critical Warnings Analysis
```python
def _analyze_critical_warnings(self, smart_data: Dict) -> HealthMetric:
```

**Warning Types Detected**:
- Available spare space has fallen below threshold
- Temperature above/below threshold
- NVM subsystem reliability degraded
- Media placed in read-only mode
- Volatile memory backup device failed

##### Power-On Hours Analysis
```python
def _analyze_power_on_hours(self, smart_data: Dict) -> HealthMetric:
```

**Analysis Logic**:
- Tracks total device runtime
- Calculates average daily usage
- Provides longevity insights
- No critical thresholds (informational)

##### Media Errors Analysis
```python
def _analyze_media_errors(self, smart_data: Dict) -> HealthMetric:
```

**Error Types Monitored**:
- `media_errors`: Uncorrectable media errors
- `num_err_log_entries`: Total error log entries
- Trend analysis for error rate

### 3. Health Score Calculation

```python
def _calculate_health_score(self, metrics: List[HealthMetric]) -> int:
```

**Scoring Algorithm**:
```
Base Score: 100 points
For each CRITICAL issue: -30 points
For each WARNING issue: -15 points
For each INFO issue: -5 points
Minimum Score: 0 points
```

**Score Interpretation**:
- 90-100: Excellent health
- 70-89: Good health
- 50-69: Fair health (monitoring recommended)
- 30-49: Poor health (action required)
- 0-29: Critical health (immediate action required)

### 4. Overall Status Determination

```python
def _determine_overall_status(self, metrics: List[HealthMetric], score: int) -> HealthStatus:
```

**Status Logic**:
```python
if any(m.status == HealthStatus.FAILING for m in metrics):
    return HealthStatus.FAILING
elif any(m.status == HealthStatus.CRITICAL for m in metrics):
    return HealthStatus.CRITICAL
elif any(m.status == HealthStatus.WARNING for m in metrics):
    return HealthStatus.WARNING
else:
    return HealthStatus.HEALTHY
```

### 5. Recommendations Generation

```python
def _generate_recommendations(self, metrics: List[HealthMetric], status: HealthStatus) -> List[str]:
```

**Recommendation Categories**:

#### Temperature Recommendations
- Improve system cooling
- Check thermal paste/pads
- Verify airflow patterns
- Consider workload optimization

#### Spare Capacity Recommendations
- Plan for replacement
- Reduce write-intensive workloads
- Enable write caching optimizations
- Monitor wear leveling

#### High Usage Recommendations
- Backup critical data
- Plan migration strategy
- Reduce unnecessary writes
- Implement data lifecycle management

#### Critical Warning Recommendations
- Immediate data backup
- Contact vendor support
- Plan emergency replacement
- Enable read-only mode if necessary

## Function Reference

### Core NVMe Interface Functions Used

#### `get_smart_log(device_path: str) -> Dict[str, Any]`
**Purpose**: Retrieves SMART/Health Information log from NVMe device

**Returns**:
- `temperature`: Current temperature
- `available_spare`: Available spare capacity percentage
- `available_spare_threshold`: Spare capacity threshold
- `percentage_used`: Percentage of rated endurance used
- `critical_warning`: Critical warning flags
- `power_on_hours`: Total power-on time
- `media_errors`: Media and data integrity errors

#### `get_controller_info(device_path: str) -> Dict[str, Any]`
**Purpose**: Retrieves controller identification information

**Returns**:
- `mn`: Model number
- `sn`: Serial number
- `fr`: Firmware revision
- `tnvmcap`: Total NVM capacity
- `vid`: Vendor ID

#### `list_nvme_devices() -> List[Dict[str, Any]]`
**Purpose**: Discovers all NVMe devices in the system

**Returns**: List of device information dictionaries

### Data Classes

#### `HealthStatus` Enum
```python
class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning" 
    CRITICAL = "critical"
    FAILING = "failing"
```

#### `HealthMetric` Dataclass
```python
@dataclass
class HealthMetric:
    name: str
    value: Any
    status: HealthStatus
    message: str
    recommendation: str
```

#### `HealthAssessment` Dataclass
```python
@dataclass
class HealthAssessment:
    device_path: str
    device_model: str
    device_serial: str
    metrics: List[HealthMetric]
    overall_status: HealthStatus
    health_score: int
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[str]
```

## Usage Examples

### Basic Health Check
```python
checker = NVMeHealthChecker()
assessment = checker.check_device_health("/dev/nvme0")
checker.display_health_report(assessment)
```

### System-Wide Health Check
```python
def check_all_devices():
    checker = NVMeHealthChecker()
    devices = list_nvme_devices()
    
    for device in devices:
        try:
            assessment = checker.check_device_health(device['DevicePath'])
            checker.display_health_report(assessment)
        except Exception as e:
            print(f"❌ Failed to check {device['DevicePath']}: {e}")
```

### Custom Thresholds
```python
checker = NVMeHealthChecker()
checker.temperature_critical = 90  # Raise temperature threshold
checker.spare_warning = 15         # More conservative spare threshold
assessment = checker.check_device_health("/dev/nvme0")
```

## Error Handling

### Exception Types Handled
- `NVMeDeviceNotFoundError`: Device path invalid or device not found
- `NVMeCommandError`: nvme-cli command execution failed
- `NVMePermissionError`: Insufficient permissions to access device
- `NVMeTimeoutError`: Command execution timeout

### Error Recovery Strategies
```python
try:
    assessment = checker.check_device_health(device_path)
except NVMeDeviceNotFoundError:
    print(f"❌ Device {device_path} not found")
except NVMePermissionError:
    print(f"❌ Permission denied. Try running with sudo")
except NVMeCommandError as e:
    print(f"❌ Command failed: {e}")
```

## Integration Patterns

### Monitoring System Integration
```python
def health_monitoring_service():
    checker = NVMeHealthChecker()
    
    while True:
        for device in list_nvme_devices():
            assessment = checker.check_device_health(device['DevicePath'])
            
            if assessment.overall_status in [HealthStatus.CRITICAL, HealthStatus.FAILING]:
                send_alert(assessment)
            
            log_health_metrics(assessment)
        
        time.sleep(3600)  # Check hourly
```

### Automated Reporting
```python
def generate_health_report():
    checker = NVMeHealthChecker()
    report = {
        'timestamp': datetime.now().isoformat(),
        'devices': []
    }
    
    for device in list_nvme_devices():
        assessment = checker.check_device_health(device['DevicePath'])
        report['devices'].append({
            'path': assessment.device_path,
            'model': assessment.device_model,
            'status': assessment.overall_status.value,
            'score': assessment.health_score,
            'issues': assessment.critical_issues + assessment.warnings
        })
    
    return report
```

## Performance Considerations

### Optimization Tips
1. **Batch Processing**: Check multiple devices in parallel
2. **Caching**: Cache device info for repeated checks
3. **Selective Monitoring**: Focus on critical parameters for frequent checks
4. **Threshold Tuning**: Adjust thresholds based on device characteristics

### Resource Usage
- **Memory**: Minimal (< 10MB per device)
- **CPU**: Low impact (< 1% CPU per check)
- **I/O**: Single SMART log read per device
- **Network**: None (local device access only)

## Troubleshooting

### Common Issues

#### No Devices Found
```bash
# Check if nvme-cli is installed
nvme version

# List devices manually
nvme list

# Check permissions
ls -la /dev/nvme*
```

#### Permission Denied
```bash
# Run with sudo
sudo python examples/health_status_checker.py

# Or add user to nvme group
sudo usermod -a -G nvme $USER
```

#### SMART Data Unavailable
- Some older devices may not support all SMART attributes
- Virtual machines may not expose SMART data
- Check device documentation for supported features

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

checker = NVMeHealthChecker()
assessment = checker.check_device_health("/dev/nvme0")
```

This comprehensive documentation provides complete understanding of the health status checker's architecture, implementation details, and usage patterns for effective NVMe SSD health monitoring.
