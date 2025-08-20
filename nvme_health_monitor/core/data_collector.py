"""
NVMe Health Monitor - Data Collection Module

This module orchestrates the collection of health data from NVMe devices.
It coordinates between the nvme_interface and data models to gather comprehensive health information.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models.exceptions import (
    NVMeBaseException, 
    NVMeDeviceNotFoundError,
    NVMeCommandError
)
from ..models.health_metrics import (
    DeviceInfo,
    SMARTData, 
    ErrorLogEntry,
    SelfTestEntry,
    ControllerInfo,
    NamespaceInfo,
    SystemHealthSummary,
    TemperatureReading,
    SMARTAttribute,
    SelfTestType,
    SelfTestResult,
    HealthStatus
)
from .nvme_interface import (
    list_nvme_devices,
    get_device_namespaces,
    get_smart_log,
    get_error_log,
    get_self_test_log,
    get_controller_info,
    validate_device_path
)


logger = logging.getLogger(__name__)


class DataCollector:
    """Main data collection orchestrator for NVMe health monitoring."""
    
    def __init__(self, max_workers: int = 4, timeout: int = 30):
        """
        Initialize data collector.
        
        Args:
            max_workers: Maximum number of concurrent collection threads
            timeout: Timeout for individual operations in seconds
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def collect_device_health(self, device_path: str) -> DeviceInfo:
        """
        Collect comprehensive health data for a single NVMe device.
        
        Args:
            device_path: Path to NVMe device (e.g., '/dev/nvme0')
            
        Returns:
            DeviceInfo: Complete device health information
            
        Raises:
            NVMeDeviceNotFoundError: If device doesn't exist
            NVMeCommandError: If data collection fails
        """
        self.logger.info(f"Collecting health data for device: {device_path}")
        
        validate_device_path(device_path)
        
        try:
            controller_info = self._collect_controller_info(device_path)
            namespaces = self._collect_namespace_info(device_path)
            smart_data = self._collect_smart_data(device_path)
            error_log = self._collect_error_log(device_path)
            self_test_log = self._collect_self_test_log(device_path)
            
            device_info = DeviceInfo(
                device_path=device_path,
                controller_info=controller_info,
                namespaces=namespaces,
                smart_data=smart_data,
                error_log=error_log,
                self_test_log=self_test_log,
                collection_timestamp=datetime.now()
            )
            
            self.logger.info(f"Successfully collected health data for {device_path}")
            return device_info
            
        except Exception as e:
            self.logger.error(f"Failed to collect health data for {device_path}: {e}")
            raise NVMeCommandError(
                f"Health data collection failed for {device_path}",
                device_path=device_path
            ) from e
    
    def collect_all_devices_health(self) -> SystemHealthSummary:
        """
        Collect health data for all available NVMe devices.
        
        Returns:
            SystemHealthSummary: System-wide health summary
            
        Raises:
            NVMeCommandError: If device discovery or collection fails
        """
        self.logger.info("Starting system-wide health data collection")
        
        try:
            devices_list = list_nvme_devices()
            device_paths = [device['DevicePath'] for device in devices_list]
            
            if not device_paths:
                self.logger.warning("No NVMe devices found on system")
                return SystemHealthSummary(
                    devices=[],
                    collection_timestamp=datetime.now()
                )
            
            self.logger.info(f"Found {len(device_paths)} NVMe devices")
            
            devices_info = self._collect_multiple_devices(device_paths)
            
            summary = SystemHealthSummary(
                devices=devices_info,
                collection_timestamp=datetime.now()
            )
            
            self.logger.info(f"System health collection complete: {summary.total_devices} devices, "
                           f"{summary.healthy_devices} healthy, {summary.warning_devices} warnings, "
                           f"{summary.critical_devices} critical")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"System health collection failed: {e}")
            raise NVMeCommandError("System-wide health collection failed") from e
    
    def _collect_multiple_devices(self, device_paths: List[str]) -> List[DeviceInfo]:
        """
        Collect health data for multiple devices concurrently.
        
        Args:
            device_paths: List of device paths to collect from
            
        Returns:
            List[DeviceInfo]: Health data for all devices
        """
        devices_info = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_device = {
                executor.submit(self.collect_device_health, device_path): device_path
                for device_path in device_paths
            }
            
            for future in as_completed(future_to_device, timeout=self.timeout * len(device_paths)):
                device_path = future_to_device[future]
                try:
                    device_info = future.result()
                    devices_info.append(device_info)
                except Exception as e:
                    self.logger.error(f"Failed to collect data for {device_path}: {e}")
                    continue
        
        return devices_info
    
    def _collect_controller_info(self, device_path: str) -> ControllerInfo:
        """Collect NVMe controller information."""
        self.logger.debug(f"Collecting controller info for {device_path}")
        
        controller_data = get_controller_info(device_path)
        
        return ControllerInfo(
            device_path=device_path,
            model_number=controller_data.get('mn', '').strip(),
            serial_number=controller_data.get('sn', '').strip(),
            firmware_revision=controller_data.get('fr', '').strip(),
            pci_vendor_id=controller_data.get('vid', ''),
            pci_subsystem_vendor_id=controller_data.get('ssvid', ''),
            ieee_oui_identifier=controller_data.get('ieee', ''),
            total_nvm_capacity=controller_data.get('tnvmcap', 0),
            unallocated_nvm_capacity=controller_data.get('unvmcap', 0),
            controller_id=controller_data.get('cntlid', 0),
            version=controller_data.get('ver', ''),
            rtd3_resume_latency=controller_data.get('rtd3r', None),
            rtd3_entry_latency=controller_data.get('rtd3e', None),
            optional_admin_commands=controller_data.get('oacs', []),
            optional_nvm_commands=controller_data.get('oncs', []),
            maximum_data_transfer_size=controller_data.get('mdts', None)
        )
    
    def _collect_namespace_info(self, device_path: str) -> List[NamespaceInfo]:
        """Collect namespace information for device."""
        self.logger.debug(f"Collecting namespace info for {device_path}")
        
        namespaces_data = get_device_namespaces(device_path)
        namespaces = []
        
        for ns_data in namespaces_data:
            namespace = NamespaceInfo(
                namespace_id=ns_data.get('nsid', 0),
                device_path=ns_data.get('DevicePath', ''),
                size=ns_data.get('Size', 0),
                capacity=ns_data.get('PhysicalSize', 0),
                utilization=ns_data.get('UsedBytes', 0),
                formatted_lba_size=ns_data.get('SectorSize', 0),
                metadata_size=ns_data.get('MetadataSize', 0),
                relative_performance=ns_data.get('RelativePerformance', None)
            )
            namespaces.append(namespace)
        
        return namespaces
    
    def _collect_smart_data(self, device_path: str) -> SMARTData:
        """Collect SMART health data."""
        self.logger.debug(f"Collecting SMART data for {device_path}")
        
        smart_raw = get_smart_log(device_path)
        
        temp_celsius = smart_raw.get('temperature_celsius', 0)
        temperature = TemperatureReading(
            celsius=temp_celsius,
            sensor_name="Composite Temperature",
            timestamp=datetime.now()
        )
        
        smart_data = SMARTData(
            device_path=device_path,
            timestamp=datetime.now(),
            critical_warning=smart_raw.get('critical_warning', 0),
            temperature=temperature,
            available_spare=smart_raw.get('available_spare', 0),
            available_spare_threshold=smart_raw.get('available_spare_threshold', 0),
            percentage_used=smart_raw.get('percentage_used', 0),
            data_units_read=smart_raw.get('data_units_read', 0),
            data_units_written=smart_raw.get('data_units_written', 0),
            host_read_commands=smart_raw.get('host_read_commands', 0),
            host_write_commands=smart_raw.get('host_write_commands', 0),
            controller_busy_time=smart_raw.get('controller_busy_time', 0),
            power_cycles=smart_raw.get('power_cycles', 0),
            power_on_hours=smart_raw.get('power_on_hours', 0),
            unsafe_shutdowns=smart_raw.get('unsafe_shutdowns', 0),
            media_errors=smart_raw.get('media_errors', 0),
            error_log_entries=smart_raw.get('num_err_log_entries', 0),
            raw_data=smart_raw
        )
        
        return smart_data
    
    def _collect_error_log(self, device_path: str) -> List[ErrorLogEntry]:
        """Collect error log entries."""
        self.logger.debug(f"Collecting error log for {device_path}")
        
        try:
            error_data = get_error_log(device_path)
            error_entries = []
            
            for entry in error_data:
                error_entry = ErrorLogEntry(
                    error_count=entry.get('error_count', 0),
                    submission_queue_id=entry.get('sqid', 0),
                    command_id=entry.get('cmdid', 0),
                    status_field=entry.get('status_field', ''),
                    parameter_error_location=entry.get('parm_error_location', ''),
                    lba=entry.get('lba', 0),
                    namespace_id=entry.get('nsid', 0),
                    vendor_specific_info=entry.get('vs', ''),
                    timestamp=datetime.now()
                )
                error_entries.append(error_entry)
            
            return error_entries
            
        except Exception as e:
            self.logger.warning(f"Could not collect error log for {device_path}: {e}")
            return []
    
    def _collect_self_test_log(self, device_path: str) -> List[SelfTestEntry]:
        """Collect self-test log entries."""
        self.logger.debug(f"Collecting self-test log for {device_path}")
        
        try:
            test_data = get_self_test_log(device_path)
            test_entries = []
            
            for entry in test_data:
                test_type_map = {
                    1: SelfTestType.SHORT,
                    2: SelfTestType.EXTENDED,
                    15: SelfTestType.VENDOR_SPECIFIC
                }
                test_type = test_type_map.get(entry.get('self_test_code', 0), SelfTestType.SHORT)
                
                result_map = {
                    0: SelfTestResult.COMPLETED_WITHOUT_ERROR,
                    1: SelfTestResult.ABORTED_BY_HOST,
                    2: SelfTestResult.ABORTED_BY_DEVICE,
                    3: SelfTestResult.UNKNOWN_TEST_ERROR,
                    4: SelfTestResult.COMPLETED_WITH_SEGMENT_ERROR,
                    5: SelfTestResult.FAILED_SEGMENT,
                    15: SelfTestResult.IN_PROGRESS
                }
                test_result = result_map.get(entry.get('self_test_result', 15), SelfTestResult.UNKNOWN_FAILURE)
                
                test_entry = SelfTestEntry(
                    test_type=test_type,
                    test_result=test_result,
                    power_on_hours=entry.get('power_on_hours', 0),
                    failing_lba=entry.get('failing_lba', None),
                    status_code=entry.get('status_code', None),
                    segment_number=entry.get('segment_number', None),
                    valid_diagnostic_info=entry.get('valid_diagnostic_info', False),
                    timestamp=datetime.now()
                )
                test_entries.append(test_entry)
            
            return test_entries
            
        except Exception as e:
            self.logger.warning(f"Could not collect self-test log for {device_path}: {e}")
            return []


def collect_single_device_health(device_path: str) -> DeviceInfo:
    """
    Collect health data for a single NVMe device.
    
    Args:
        device_path: Path to NVMe device
        
    Returns:
        DeviceInfo: Complete device health information
        
    Implementation Notes:
        - Use nvme_interface functions to gather raw data
        - Convert to structured data models
        - Handle errors gracefully
        - Include timestamp information
    """
    collector = DataCollector()
    return collector.collect_device_health(device_path)


def collect_all_devices_health() -> SystemHealthSummary:
    """
    Collect health data for all NVMe devices on system.
    
    Returns:
        SystemHealthSummary: System-wide health summary
        
    Implementation Notes:
        - Discover all available devices
        - Collect data concurrently for performance
        - Aggregate results into system summary
        - Handle partial failures gracefully
    """
    collector = DataCollector()
    return collector.collect_all_devices_health()


def collect_smart_data_only(device_path: str) -> SMARTData:
    """
    Collect only SMART data for a device (lightweight collection).
    
    Args:
        device_path: Path to NVMe device
        
    Returns:
        SMARTData: SMART health metrics
        
    Implementation Notes:
        - Faster than full device collection
        - Focus on critical health metrics
        - Include temperature conversion
    """
    collector = DataCollector()
    return collector._collect_smart_data(device_path)


def collect_error_logs_only(device_path: str) -> List[ErrorLogEntry]:
    """
    Collect only error logs for a device.
    
    Args:
        device_path: Path to NVMe device
        
    Returns:
        List[ErrorLogEntry]: Error log entries
        
    Implementation Notes:
        - Parse nvme error-log output
        - Convert to structured format
        - Include error classification
    """
    collector = DataCollector()
    return collector._collect_error_log(device_path)


def collect_self_test_logs_only(device_path: str) -> List[SelfTestEntry]:
    """
    Collect only self-test logs for a device.
    
    Args:
        device_path: Path to NVMe device
        
    Returns:
        List[SelfTestEntry]: Self-test log entries
        
    Implementation Notes:
        - Parse nvme self-test-log output
        - Map test types and results
        - Include progress information
    """
    collector = DataCollector()
    return collector._collect_self_test_log(device_path)
