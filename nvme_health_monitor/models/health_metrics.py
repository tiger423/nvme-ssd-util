"""
NVMe Health Monitor - Health Metrics Data Models

This module contains data models for NVMe health metrics and device information.
Uses Pydantic for data validation and serialization.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class TemperatureUnit(str, Enum):
    """Temperature unit enumeration."""
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"
    KELVIN = "kelvin"


class SelfTestType(str, Enum):
    """Self-test type enumeration."""
    SHORT = "short"
    EXTENDED = "extended"
    VENDOR_SPECIFIC = "vendor_specific"


class SelfTestResult(str, Enum):
    """Self-test result enumeration."""
    COMPLETED_WITHOUT_ERROR = "completed_without_error"
    ABORTED_BY_HOST = "aborted_by_host"
    ABORTED_BY_DEVICE = "aborted_by_device"
    UNKNOWN_TEST_ERROR = "unknown_test_error"
    COMPLETED_WITH_SEGMENT_ERROR = "completed_with_segment_error"
    FAILED_SEGMENT = "failed_segment"
    UNKNOWN_FAILURE = "unknown_failure"
    IN_PROGRESS = "in_progress"


class HealthStatus(str, Enum):
    """Overall health status enumeration."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class SMARTAttribute(BaseModel):
    """Individual SMART attribute data model."""
    
    name: str = Field(..., description="Attribute name")
    value: Union[int, float, str] = Field(..., description="Attribute value")
    raw_value: Optional[str] = Field(None, description="Raw hex value")
    threshold: Optional[Union[int, float]] = Field(None, description="Threshold value")
    worst: Optional[Union[int, float]] = Field(None, description="Worst recorded value")
    unit: Optional[str] = Field(None, description="Value unit")
    critical: bool = Field(False, description="Is this a critical attribute")
    
    class Config:
        extra = "allow"


class TemperatureReading(BaseModel):
    """Temperature reading data model."""
    
    celsius: float = Field(..., description="Temperature in Celsius")
    fahrenheit: float = Field(..., description="Temperature in Fahrenheit") 
    kelvin: float = Field(..., description="Temperature in Kelvin")
    sensor_name: str = Field(..., description="Temperature sensor name")
    timestamp: datetime = Field(default_factory=datetime.now, description="Reading timestamp")
    
    @validator('fahrenheit', pre=True, always=True)
    def calculate_fahrenheit(cls, v, values):
        if 'celsius' in values:
            return (values['celsius'] * 9/5) + 32
        return v
    
    @validator('kelvin', pre=True, always=True) 
    def calculate_kelvin(cls, v, values):
        if 'celsius' in values:
            return values['celsius'] + 273.15
        return v


class SMARTData(BaseModel):
    """SMART data collection model."""
    
    device_path: str = Field(..., description="NVMe device path")
    timestamp: datetime = Field(default_factory=datetime.now, description="Collection timestamp")
    
    critical_warning: int = Field(..., description="Critical warning flags")
    temperature: TemperatureReading = Field(..., description="Current temperature")
    available_spare: float = Field(..., description="Available spare percentage")
    available_spare_threshold: float = Field(..., description="Available spare threshold")
    percentage_used: float = Field(..., description="Percentage used")
    
    data_units_read: int = Field(..., description="Data units read")
    data_units_written: int = Field(..., description="Data units written")
    host_read_commands: int = Field(..., description="Host read commands")
    host_write_commands: int = Field(..., description="Host write commands")
    controller_busy_time: int = Field(..., description="Controller busy time")
    power_cycles: int = Field(..., description="Power cycles")
    power_on_hours: int = Field(..., description="Power on hours")
    unsafe_shutdowns: int = Field(..., description="Unsafe shutdowns")
    media_errors: int = Field(..., description="Media and data integrity errors")
    error_log_entries: int = Field(..., description="Number of error log entries")
    
    attributes: Dict[str, SMARTAttribute] = Field(default_factory=dict, description="Additional SMART attributes")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Raw nvme-cli output")
    
    @property
    def health_status(self) -> HealthStatus:
        """Calculate overall health status based on SMART data."""
        if self.critical_warning > 0:
            return HealthStatus.CRITICAL
        
        if (self.available_spare < self.available_spare_threshold or 
            self.percentage_used > 90 or
            self.temperature.celsius > 70):
            return HealthStatus.WARNING
            
        return HealthStatus.HEALTHY


class ErrorLogEntry(BaseModel):
    """NVMe error log entry model."""
    
    error_count: int = Field(..., description="Error count")
    submission_queue_id: int = Field(..., description="Submission queue ID")
    command_id: int = Field(..., description="Command ID")
    status_field: str = Field(..., description="Status field")
    parameter_error_location: str = Field(..., description="Parameter error location")
    lba: int = Field(..., description="Logical block address")
    namespace_id: int = Field(..., description="Namespace ID")
    vendor_specific_info: str = Field(..., description="Vendor specific information")
    timestamp: Optional[datetime] = Field(None, description="Error timestamp")
    
    class Config:
        extra = "allow"


class SelfTestEntry(BaseModel):
    """Self-test log entry model."""
    
    test_type: SelfTestType = Field(..., description="Type of self-test")
    test_result: SelfTestResult = Field(..., description="Test result")
    power_on_hours: int = Field(..., description="Power on hours when test completed")
    failing_lba: Optional[int] = Field(None, description="Failing LBA if test failed")
    status_code: Optional[str] = Field(None, description="Status code")
    segment_number: Optional[int] = Field(None, description="Segment number")
    valid_diagnostic_info: bool = Field(False, description="Valid diagnostic information")
    timestamp: Optional[datetime] = Field(None, description="Test timestamp")
    
    class Config:
        extra = "allow"


class NamespaceInfo(BaseModel):
    """NVMe namespace information model."""
    
    namespace_id: int = Field(..., description="Namespace ID")
    device_path: str = Field(..., description="Namespace device path")
    size: int = Field(..., description="Namespace size in bytes")
    capacity: int = Field(..., description="Namespace capacity in bytes")
    utilization: int = Field(..., description="Namespace utilization in bytes")
    formatted_lba_size: int = Field(..., description="Formatted LBA size")
    metadata_size: int = Field(..., description="Metadata size")
    relative_performance: Optional[str] = Field(None, description="Relative performance")
    
    class Config:
        extra = "allow"


class ControllerInfo(BaseModel):
    """NVMe controller information model."""
    
    device_path: str = Field(..., description="Controller device path")
    model_number: str = Field(..., description="Model number")
    serial_number: str = Field(..., description="Serial number")
    firmware_revision: str = Field(..., description="Firmware revision")
    pci_vendor_id: str = Field(..., description="PCI vendor ID")
    pci_subsystem_vendor_id: str = Field(..., description="PCI subsystem vendor ID")
    ieee_oui_identifier: str = Field(..., description="IEEE OUI identifier")
    total_nvm_capacity: int = Field(..., description="Total NVM capacity")
    unallocated_nvm_capacity: int = Field(..., description="Unallocated NVM capacity")
    controller_id: int = Field(..., description="Controller ID")
    version: str = Field(..., description="NVMe version")
    rtd3_resume_latency: Optional[int] = Field(None, description="RTD3 resume latency")
    rtd3_entry_latency: Optional[int] = Field(None, description="RTD3 entry latency")
    optional_admin_commands: List[str] = Field(default_factory=list, description="Optional admin commands")
    optional_nvm_commands: List[str] = Field(default_factory=list, description="Optional NVM commands")
    maximum_data_transfer_size: Optional[int] = Field(None, description="Maximum data transfer size")
    
    class Config:
        extra = "allow"


class DeviceInfo(BaseModel):
    """Complete NVMe device information model."""
    
    device_path: str = Field(..., description="Device path")
    controller_info: ControllerInfo = Field(..., description="Controller information")
    namespaces: List[NamespaceInfo] = Field(default_factory=list, description="Namespace information")
    smart_data: Optional[SMARTData] = Field(None, description="SMART data")
    error_log: List[ErrorLogEntry] = Field(default_factory=list, description="Error log entries")
    self_test_log: List[SelfTestEntry] = Field(default_factory=list, description="Self-test log entries")
    collection_timestamp: datetime = Field(default_factory=datetime.now, description="Data collection timestamp")
    
    @property
    def health_status(self) -> HealthStatus:
        """Get overall device health status."""
        if self.smart_data:
            return self.smart_data.health_status
        return HealthStatus.UNKNOWN
    
    @property
    def total_capacity_gb(self) -> float:
        """Get total device capacity in GB."""
        return self.controller_info.total_nvm_capacity / (1024**3)
    
    @property
    def has_errors(self) -> bool:
        """Check if device has any logged errors."""
        return len(self.error_log) > 0
    
    @property
    def last_self_test_result(self) -> Optional[SelfTestResult]:
        """Get result of most recent self-test."""
        if self.self_test_log:
            return self.self_test_log[0].test_result
        return None


class SystemHealthSummary(BaseModel):
    """System-wide health summary model."""
    
    devices: List[DeviceInfo] = Field(default_factory=list, description="All NVMe devices")
    collection_timestamp: datetime = Field(default_factory=datetime.now, description="Collection timestamp")
    total_devices: int = Field(0, description="Total number of devices")
    healthy_devices: int = Field(0, description="Number of healthy devices")
    warning_devices: int = Field(0, description="Number of devices with warnings")
    critical_devices: int = Field(0, description="Number of critical devices")
    
    @validator('total_devices', pre=True, always=True)
    def calculate_total_devices(cls, v, values):
        if 'devices' in values:
            return len(values['devices'])
        return v
    
    @validator('healthy_devices', pre=True, always=True)
    def calculate_healthy_devices(cls, v, values):
        if 'devices' in values:
            return len([d for d in values['devices'] if d.health_status == HealthStatus.HEALTHY])
        return v
    
    @validator('warning_devices', pre=True, always=True)
    def calculate_warning_devices(cls, v, values):
        if 'devices' in values:
            return len([d for d in values['devices'] if d.health_status == HealthStatus.WARNING])
        return v
    
    @validator('critical_devices', pre=True, always=True)
    def calculate_critical_devices(cls, v, values):
        if 'devices' in values:
            return len([d for d in values['devices'] if d.health_status == HealthStatus.CRITICAL])
        return v
    
    @property
    def overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        if self.critical_devices > 0:
            return HealthStatus.CRITICAL
        elif self.warning_devices > 0:
            return HealthStatus.WARNING
        elif self.healthy_devices > 0:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN


def create_smart_data_model() -> type:
    """
    Create SMART data model class.
    
    Returns:
        type: SMARTData model class
        
    Implementation Notes:
        - Use Pydantic BaseModel for validation
        - Include all standard SMART attributes
        - Add temperature conversion methods
        - Include health status calculation
    """
    return SMARTData


def create_device_info_model() -> type:
    """
    Create device information model class.
    
    Returns:
        type: DeviceInfo model class
        
    Implementation Notes:
        - Combine controller info, namespaces, SMART data
        - Include error logs and self-test results
        - Add computed properties for health status
    """
    return DeviceInfo


def create_error_log_model() -> type:
    """
    Create error log entry model class.
    
    Returns:
        type: ErrorLogEntry model class
        
    Implementation Notes:
        - Map all nvme error log fields
        - Include timestamp parsing
        - Add severity classification
    """
    return ErrorLogEntry


def create_self_test_model() -> type:
    """
    Create self-test log entry model class.
    
    Returns:
        type: SelfTestEntry model class
        
    Implementation Notes:
        - Support all self-test types and results
        - Include progress tracking
        - Add failure analysis fields
    """
    return SelfTestEntry


def create_controller_info_model() -> type:
    """
    Create controller information model class.
    
    Returns:
        type: ControllerInfo model class
        
    Implementation Notes:
        - Map nvme id-ctrl output fields
        - Include capacity calculations
        - Add feature support flags
    """
    return ControllerInfo


def create_namespace_info_model() -> type:
    """
    Create namespace information model class.
    
    Returns:
        type: NamespaceInfo model class
        
    Implementation Notes:
        - Map namespace identification fields
        - Include size and capacity calculations
        - Add formatting information
    """
    return NamespaceInfo


def create_system_health_summary_model() -> type:
    """
    Create system health summary model class.
    
    Returns:
        type: SystemHealthSummary model class
        
    Implementation Notes:
        - Aggregate multiple device health data
        - Calculate system-wide statistics
        - Include overall health assessment
    """
    return SystemHealthSummary
