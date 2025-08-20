# Device Detector - Code Flow and Function Documentation

## Overview

The `device_detector.py` example demonstrates comprehensive NVMe device detection and enumeration across a system. This tool automatically discovers all NVMe devices, analyzes their physical topology, connection interfaces, and provides a system-wide summary of NVMe storage infrastructure.

## Code Architecture

```
NVMeDeviceDetector
├── System-Wide Device Discovery
├── Physical Topology Analysis
├── PCIe Interface Detection
├── Device Capability Assessment
├── Health Status Overview
├── System Summary Generation
└── Detection Report & Export
```

## Detailed Code Flow

### 1. Data Classes Structure

The detector uses structured data classes to organize detection results:

#### PCIe Information
```python
@dataclass
class PCIeInfo:
    bus_id: str
    device_id: str
    function_id: str
    vendor_id: str
    device_id_hex: str
    subsystem_vendor: str
    subsystem_device: str
    link_speed: str
    link_width: str
    max_link_speed: str
    max_link_width: str
    numa_node: int
```

#### Physical Location
```python
@dataclass
class PhysicalLocation:
    slot_type: str          # M.2, U.2, PCIe, etc.
    slot_number: str        # Physical slot identifier
    form_factor: str        # 2280, 22110, U.2, etc.
    interface_type: str     # PCIe, SATA, etc.
    connector_type: str     # M-Key, B+M-Key, SFF-8639, etc.
```

#### Device Capabilities
```python
@dataclass
class DeviceCapabilities:
    max_namespaces: int
    namespace_management: bool
    format_nvm: bool
    security_send_receive: bool
    firmware_update: bool
    volatile_write_cache: bool
    multipath: bool
    reservation: bool
```

#### Health Summary
```python
@dataclass
class HealthSummary:
    overall_status: str
    temperature_celsius: int
    available_spare_percent: int
    percentage_used: int
    critical_warnings: int
    power_on_hours: int
    estimated_health_score: int
```

### 2. Main Detection Function

```python
def detect_all_devices(self) -> SystemSummary:
```

**Flow Diagram**:
```
System Scan Initiation
       ↓
NVMe Device Discovery ← list_nvme_devices()
       ↓
For Each Device:
├── Basic Information Collection
├── Detailed Device Analysis ← _analyze_single_device()
│   ├── Controller Info ← get_controller_info()
│   ├── SMART Data ← get_smart_log()
│   ├── Namespace Info ← get_device_namespaces()
│   ├── PCIe Topology ← _get_pcie_info()
│   ├── Physical Location ← _determine_physical_location()
│   ├── Capabilities ← _analyze_capabilities()
│   └── Health Summary ← _create_health_summary()
└── DetectedDevice Assembly
       ↓
System Summary Generation ← _generate_system_summary()
       ↓
SystemSummary Object
```

### 3. Single Device Analysis

```python
def _analyze_single_device(self, device_path: str, basic_info: Dict) -> DetectedDevice:
```

**Analysis Process**:

#### 3.1 Data Collection Phase
```python
# Collect comprehensive device data
device_info = get_controller_info(device_path)
smart_data = get_smart_log(device_path)
namespaces = get_device_namespaces(device_path)
```

#### 3.2 Controller Identification
```python
# Extract controller number for sysfs access
controller_match = re.search(r'nvme(\d+)', device_path)
controller_num = int(controller_match.group(1)) if controller_match else 0
```

#### 3.3 PCIe Information Extraction

```python
def _get_pcie_info(self, controller_num: int) -> PCIeInfo:
```

**PCIe Discovery Process**:
```python
# Construct sysfs path for PCIe information
sysfs_path = f"/sys/class/nvme/nvme{controller_num}/device"

# Read PCIe configuration from sysfs
def read_sysfs_file(filepath: str) -> str:
    try:
        with open(filepath, 'r') as f:
            return f.read().strip()
    except (IOError, OSError):
        return "unknown"

# Extract PCIe identifiers
vendor_id = read_sysfs_file(f"{sysfs_path}/vendor")
device_id = read_sysfs_file(f"{sysfs_path}/device")
subsystem_vendor = read_sysfs_file(f"{sysfs_path}/subsystem_vendor")
subsystem_device = read_sysfs_file(f"{sysfs_path}/subsystem_device")

# Parse PCIe bus topology
uevent_data = read_sysfs_file(f"{sysfs_path}/uevent")
pci_slot_match = re.search(r'PCI_SLOT_NAME=(\d+):(\d+):(\d+)\.(\d+)', uevent_data)
```

**PCIe Link Analysis**:
```python
# Current link status
current_link_speed = read_sysfs_file(f"{sysfs_path}/current_link_speed")
current_link_width = read_sysfs_file(f"{sysfs_path}/current_link_width")

# Maximum link capabilities
max_link_speed = read_sysfs_file(f"{sysfs_path}/max_link_speed")
max_link_width = read_sysfs_file(f"{sysfs_path}/max_link_width")

# NUMA topology
numa_node = read_sysfs_file(f"{sysfs_path}/numa_node")
```

#### 3.4 Physical Location Determination

```python
def _determine_physical_location(self, pcie_info: PCIeInfo, device_info: Dict) -> PhysicalLocation:
```

**Location Detection Logic**:
```python
# Determine slot type based on PCIe configuration
def determine_slot_type(pcie_info: PCIeInfo) -> str:
    # M.2 devices typically use specific vendor/device combinations
    if pcie_info.vendor_id in ["0x144d", "0x15b7", "0x1c5c"]:  # Samsung, SanDisk, SK Hynix
        return "M.2"
    
    # U.2 devices often have different subsystem configurations
    if pcie_info.link_width in ["x4"] and pcie_info.max_link_speed >= "8.0 GT/s":
        return "U.2"
    
    # PCIe add-in cards
    if pcie_info.link_width in ["x8", "x16"]:
        return "PCIe Add-in Card"
    
    return "Unknown"

# Determine form factor
def determine_form_factor(slot_type: str, device_info: Dict) -> str:
    if slot_type == "M.2":
        # Common M.2 form factors
        return "2280"  # Most common, could be enhanced with actual detection
    elif slot_type == "U.2":
        return "2.5\" U.2"
    elif slot_type == "PCIe Add-in Card":
        return "PCIe Card"
    
    return "Unknown"
```

**Interface Type Detection**:
```python
# Determine interface based on PCIe generation and lanes
def determine_interface_type(pcie_info: PCIeInfo) -> str:
    if "PCIe" in pcie_info.max_link_speed:
        pcie_gen = "3.0" if "8.0 GT/s" in pcie_info.max_link_speed else "4.0"
        return f"PCIe {pcie_gen} x{pcie_info.max_link_width.replace('x', '')}"
    
    return "PCIe"
```

#### 3.5 Device Capabilities Analysis

```python
def _analyze_capabilities(self, device_info: Dict) -> DeviceCapabilities:
```

**Capability Detection Process**:
```python
# Extract capability flags from controller information
oacs = device_info.get('oacs', 0)  # Optional Admin Command Support
oncs = device_info.get('oncs', 0)  # Optional NVM Command Support
fna = device_info.get('fna', 0)    # Format NVM Attributes

# Parse individual capabilities
namespace_management = bool(oacs & 0x08)  # Namespace Management
security_send_receive = bool(oacs & 0x01)  # Security Send/Receive
firmware_update = bool(oacs & 0x04)       # Firmware Commit/Download

format_nvm = bool(oncs & 0x01)            # Format NVM
volatile_write_cache = bool(device_info.get('vwc', 0))

# Advanced capabilities
multipath = bool(device_info.get('mic', 0) & 0x01)
reservation = bool(oncs & 0x20)           # Reservations
```

**Namespace Management Detection**:
```python
# Determine maximum namespace support
max_namespaces = device_info.get('nn', 1)

# Check if namespace management is supported
namespace_mgmt_support = bool(oacs & 0x08)
```

#### 3.6 Health Summary Creation

```python
def _create_health_summary(self, smart_data: Dict) -> HealthSummary:
```

**Health Assessment Logic**:
```python
# Extract key health metrics
temperature = smart_data.get('temperature', 273) - 273  # Convert from Kelvin
available_spare = smart_data.get('available_spare', 0)
percentage_used = smart_data.get('percentage_used', 0)
critical_warnings = smart_data.get('critical_warning', 0)
power_on_hours = smart_data.get('power_on_hours', 0)

# Calculate estimated health score
def calculate_health_score(spare: int, used: int, warnings: int, temp: int) -> int:
    score = 100
    
    # Temperature impact
    if temp > 85:
        score -= 30
    elif temp > 70:
        score -= 15
    
    # Spare capacity impact
    if spare < 5:
        score -= 40
    elif spare < 10:
        score -= 20
    
    # Usage impact
    if used > 95:
        score -= 30
    elif used > 80:
        score -= 15
    
    # Critical warnings
    if warnings > 0:
        score -= 25
    
    return max(0, score)

# Determine overall status
def determine_status(score: int, warnings: int) -> str:
    if warnings > 0 or score < 30:
        return "Critical"
    elif score < 50:
        return "Warning"
    elif score < 70:
        return "Fair"
    else:
        return "Good"
```

### 4. System Summary Generation

```python
def _generate_system_summary(self, devices: List[DetectedDevice]) -> SystemSummary:
```

**Summary Calculation Process**:
```python
# Count devices by status
status_counts = {"Good": 0, "Fair": 0, "Warning": 0, "Critical": 0}
for device in devices:
    status_counts[device.health_summary.overall_status] += 1

# Calculate total capacity
total_capacity_bytes = sum(
    device.basic_info.get('Size', 0) for device in devices
)

# Identify unique vendors and models
vendors = set(device.identification.vendor_id for device in devices)
models = set(device.identification.model_number for device in devices)

# Analyze interface distribution
interface_types = {}
for device in devices:
    interface = device.physical_location.interface_type
    interface_types[interface] = interface_types.get(interface, 0) + 1

# Calculate average health score
avg_health_score = sum(
    device.health_summary.estimated_health_score for device in devices
) / len(devices) if devices else 0
```

### 5. Detection Report Generation

```python
def display_detection_report(self, summary: SystemSummary):
```

**Report Structure**:
```
🔍 NVMe Device Detection Report
├── 📊 System Summary
│   ├── Device Count & Status Distribution
│   ├── Total Capacity & Utilization
│   ├── Vendor & Model Diversity
│   └── Interface Type Distribution
├── 📱 Individual Device Details
│   ├── Device Identification
│   ├── Physical Location & Topology
│   ├── PCIe Configuration
│   ├── Device Capabilities
│   └── Health Status Summary
└── 💡 System Recommendations
```

**Report Sections**:

#### System Summary Section
```python
print(f"📊 System Summary:")
print(f"   Total NVMe Devices: {summary.total_devices}")
print(f"   Total Capacity: {summary.total_capacity_gb:.1f} GB")
print(f"   Unique Vendors: {len(summary.unique_vendors)}")
print(f"   Average Health Score: {summary.average_health_score:.1f}/100")

# Status distribution
for status, count in summary.device_status_counts.items():
    if count > 0:
        print(f"   {status}: {count} device(s)")
```

#### Individual Device Details
```python
for i, device in enumerate(summary.detected_devices, 1):
    print(f"\n📱 Device {i}: {device.device_path}")
    
    # Basic identification
    print(f"   Model: {device.identification.model_number}")
    print(f"   Serial: {device.identification.serial_number}")
    print(f"   Firmware: {device.identification.firmware_revision}")
    
    # Physical location
    print(f"   Location: {device.physical_location.slot_type}")
    print(f"   Form Factor: {device.physical_location.form_factor}")
    print(f"   Interface: {device.physical_location.interface_type}")
    
    # PCIe configuration
    print(f"   PCIe: {device.pcie_info.bus_id}:{device.pcie_info.device_id}")
    print(f"   Link: {device.pcie_info.link_speed} x{device.pcie_info.link_width}")
    
    # Health status
    health = device.health_summary
    print(f"   Health: {health.overall_status} ({health.estimated_health_score}/100)")
    print(f"   Temperature: {health.temperature_celsius}°C")
    print(f"   Spare: {health.available_spare_percent}%")
    print(f"   Used: {health.percentage_used}%")
```

### 6. JSON Export Functionality

```python
def export_detection_results(self, summary: SystemSummary) -> str:
```

**Export Structure**:
```json
{
    "detection_timestamp": "2024-08-20T22:54:40Z",
    "system_summary": {
        "total_devices": 2,
        "total_capacity_gb": 2048.0,
        "unique_vendors": ["Samsung", "Intel"],
        "device_status_counts": {"Good": 1, "Fair": 1},
        "average_health_score": 85.5,
        "interface_distribution": {"PCIe 3.0 x4": 2}
    },
    "detected_devices": [
        {
            "device_path": "/dev/nvme0",
            "identification": { ... },
            "physical_location": { ... },
            "pcie_info": { ... },
            "capabilities": { ... },
            "health_summary": { ... },
            "basic_info": { ... }
        }
    ]
}
```

## Function Reference

### Core NVMe Interface Functions Used

#### `list_nvme_devices() -> List[Dict[str, Any]]`
**Purpose**: Discovers all NVMe devices in the system

**Returns**: List of basic device information including:
- `DevicePath`: Device path (e.g., "/dev/nvme0")
- `DeviceNode`: Device node name
- `ModelNumber`: Device model
- `SerialNumber`: Device serial number
- `Size`: Device capacity in bytes
- `PhysicalSize`: Physical sector size
- `LogicalSize`: Logical sector size

#### `get_controller_info(device_path: str) -> Dict[str, Any]`
**Purpose**: Retrieves detailed controller identification and capabilities

**Key Data Used**:
- `mn`: Model number
- `sn`: Serial number
- `fr`: Firmware revision
- `vid`: Vendor ID
- `ssvid`: Subsystem vendor ID
- `nn`: Number of namespaces
- `oacs`: Optional admin command support
- `oncs`: Optional NVM command support
- `vwc`: Volatile write cache support

#### `get_smart_log(device_path: str) -> Dict[str, Any]`
**Purpose**: Retrieves current device health and status information

**Key Data Used**:
- `temperature`: Current temperature
- `available_spare`: Available spare capacity
- `percentage_used`: Endurance consumption
- `critical_warning`: Critical warning flags
- `power_on_hours`: Total power-on time

#### `get_device_namespaces(device_path: str) -> List[Dict[str, Any]]`
**Purpose**: Enumerates namespaces for namespace count and management assessment

## Usage Examples

### Basic System Detection
```python
detector = NVMeDeviceDetector()
summary = detector.detect_all_devices()
detector.display_detection_report(summary)
```

### JSON Export for Inventory
```python
detector = NVMeDeviceDetector()
summary = detector.detect_all_devices()
json_data = detector.export_detection_results(summary)

# Save to inventory file
with open("nvme_inventory.json", "w") as f:
    f.write(json_data)
```

### Automated Discovery Service
```python
class NVMeDiscoveryService:
    def __init__(self):
        self.detector = NVMeDeviceDetector()
        self.last_scan = None
        self.device_history = {}
    
    def periodic_scan(self, interval_minutes: int = 60):
        while True:
            try:
                summary = self.detector.detect_all_devices()
                self._process_changes(summary)
                self.last_scan = datetime.now()
                
                time.sleep(interval_minutes * 60)
            except Exception as e:
                print(f"❌ Discovery scan failed: {e}")
                time.sleep(300)  # Retry in 5 minutes
    
    def _process_changes(self, summary: SystemSummary):
        current_devices = {d.device_path: d for d in summary.detected_devices}
        
        # Detect new devices
        for path, device in current_devices.items():
            if path not in self.device_history:
                self._handle_new_device(device)
        
        # Detect removed devices
        for path in self.device_history:
            if path not in current_devices:
                self._handle_removed_device(path)
        
        self.device_history = current_devices
    
    def _handle_new_device(self, device: DetectedDevice):
        print(f"🆕 New NVMe device detected: {device.device_path}")
        print(f"   Model: {device.identification.model_number}")
        print(f"   Location: {device.physical_location.slot_type}")
    
    def _handle_removed_device(self, device_path: str):
        print(f"❌ NVMe device removed: {device_path}")
```

### Capacity Planning Analysis
```python
def analyze_system_capacity():
    detector = NVMeDeviceDetector()
    summary = detector.detect_all_devices()
    
    # Group by interface type
    interface_analysis = {}
    for device in summary.detected_devices:
        interface = device.physical_location.interface_type
        if interface not in interface_analysis:
            interface_analysis[interface] = {
                'count': 0,
                'total_capacity': 0,
                'avg_health': 0,
                'devices': []
            }
        
        analysis = interface_analysis[interface]
        analysis['count'] += 1
        analysis['total_capacity'] += device.basic_info.get('Size', 0)
        analysis['avg_health'] += device.health_summary.estimated_health_score
        analysis['devices'].append(device)
    
    # Calculate averages
    for interface, data in interface_analysis.items():
        data['avg_health'] /= data['count']
        data['total_capacity_gb'] = data['total_capacity'] / (1000**3)
    
    return interface_analysis
```

## Integration Patterns

### Asset Management Integration
```python
class AssetManager:
    def __init__(self, asset_db_url: str):
        self.detector = NVMeDeviceDetector()
        self.db_url = asset_db_url
    
    def sync_assets(self):
        summary = self.detector.detect_all_devices()
        
        for device in summary.detected_devices:
            asset_data = {
                'asset_type': 'nvme_ssd',
                'serial_number': device.identification.serial_number,
                'model': device.identification.model_number,
                'vendor': device.identification.vendor_id,
                'capacity_gb': device.basic_info.get('Size', 0) / (1000**3),
                'location': device.physical_location.slot_type,
                'pcie_slot': f"{device.pcie_info.bus_id}:{device.pcie_info.device_id}",
                'health_score': device.health_summary.estimated_health_score,
                'last_seen': datetime.now().isoformat()
            }
            
            self._update_asset_database(asset_data)
```

### Monitoring System Integration
```python
def export_to_prometheus():
    detector = NVMeDeviceDetector()
    summary = detector.detect_all_devices()
    
    metrics = []
    
    # System-level metrics
    metrics.append(f'nvme_total_devices {summary.total_devices}')
    metrics.append(f'nvme_total_capacity_bytes {summary.total_capacity_gb * 1e9}')
    metrics.append(f'nvme_average_health_score {summary.average_health_score}')
    
    # Per-device metrics
    for device in summary.detected_devices:
        labels = f'device="{device.device_path}",model="{device.identification.model_number}"'
        
        metrics.append(f'nvme_device_health_score{{{labels}}} {device.health_summary.estimated_health_score}')
        metrics.append(f'nvme_device_temperature_celsius{{{labels}}} {device.health_summary.temperature_celsius}')
        metrics.append(f'nvme_device_spare_percent{{{labels}}} {device.health_summary.available_spare_percent}')
        metrics.append(f'nvme_device_used_percent{{{labels}}} {device.health_summary.percentage_used}')
    
    return '\n'.join(metrics)
```

## Performance Considerations

### Optimization Strategies
1. **Parallel Detection**: Analyze devices concurrently
2. **Sysfs Caching**: Cache sysfs reads for repeated access
3. **Selective Analysis**: Skip detailed analysis for basic discovery
4. **Change Detection**: Only re-analyze changed devices

### Resource Usage
- **Memory**: ~2-5MB per device
- **CPU**: Low impact, I/O bound operations
- **Storage**: Minimal temporary data
- **Permissions**: Requires read access to /sys and /dev

## Troubleshooting

### Common Issues

#### Sysfs Access Errors
```python
def safe_sysfs_read(filepath: str, default: str = "unknown") -> str:
    try:
        with open(filepath, 'r') as f:
            return f.read().strip()
    except (IOError, OSError, PermissionError) as e:
        # Log error but continue with default value
        return default
```

#### PCIe Information Unavailable
```python
# Handle systems where PCIe information is not accessible
def _get_pcie_info_fallback(self, device_info: Dict) -> PCIeInfo:
    return PCIeInfo(
        bus_id="unknown",
        device_id="unknown",
        function_id="unknown",
        vendor_id=f"0x{device_info.get('vid', 0):04x}",
        device_id_hex="unknown",
        subsystem_vendor="unknown",
        subsystem_device="unknown",
        link_speed="unknown",
        link_width="unknown",
        max_link_speed="unknown",
        max_link_width="unknown",
        numa_node=-1
    )
```

#### Virtual Environment Detection
```python
def is_virtual_environment() -> bool:
    """Detect if running in a virtual environment where PCIe info may be limited."""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            return any(virt in cpuinfo.lower() for virt in ['vmware', 'virtualbox', 'qemu', 'kvm'])
    except:
        return False
```

This comprehensive documentation provides complete understanding of the device detector's architecture, topology analysis capabilities, and system integration patterns for effective NVMe infrastructure management.
