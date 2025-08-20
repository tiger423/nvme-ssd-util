#!/usr/bin/env python3
"""
NVMe SSD Device Detector

This example demonstrates how to detect and enumerate all NVMe SSDs in a server or PC,
providing detailed information about each device found.

DEVICE DETECTION WORKFLOW:
┌─────────────────────────────────────────────────────────────────┐
│ System Scan → Device Enumeration → Basic Info Collection →     │
│ Topology Analysis → Connection Details → Summary Report        │
└─────────────────────────────────────────────────────────────────┘

DETECTION CAPABILITIES:
🔍 Automatic discovery of all NVMe devices
📊 Device count and enumeration
🔌 Connection interface detection (PCIe, M.2, U.2, etc.)
📍 Physical location identification
⚡ Interface speed and lane configuration
🏷️  Device identification and specifications
📈 Capacity and namespace information
🌡️  Basic health status overview

SYSTEM TOPOLOGY ANALYSIS:
- PCIe slot identification and mapping
- NVMe controller to namespace relationships
- Multi-path device detection
- Hot-plug capability assessment
- Power management state detection

For technical documentation:
- Function reference: ../docs/FUNCTION_REFERENCE.md
- Integration patterns: ../docs/NVME_FORMAT_CODE_FLOW.md
"""

import sys
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from nvme_health_monitor.core.nvme_interface import (
    check_nvme_cli_availability,
    list_nvme_devices,
    get_controller_info,
    get_smart_log,
    get_device_namespaces
)
from nvme_health_monitor.models.exceptions import (
    NVMeCommandError,
    NVMeDeviceNotFoundError,
    NVMePermissionError
)
from nvme_health_monitor.utils.logging_config import setup_logging


@dataclass
class PCIeInfo:
    """PCIe connection information."""
    bus_id: str
    slot: str
    vendor_id: str
    device_id: str
    subsystem_vendor: str
    subsystem_device: str
    link_speed: str
    link_width: str
    max_link_speed: str
    max_link_width: str
    numa_node: int


@dataclass
class PhysicalLocation:
    """Physical location and connection details."""
    form_factor: str  # M.2, U.2, PCIe Card, etc.
    connector_type: str
    slot_designation: str
    removable: bool
    hot_pluggable: bool


@dataclass
class DeviceCapabilities:
    """Device capabilities and features."""
    max_namespaces: int
    current_namespaces: int
    multipath_support: bool
    security_features: List[str]
    power_states: int
    queue_depth: int
    max_transfer_size: int


@dataclass
class HealthSummary:
    """Basic health status summary."""
    temperature: int
    health_status: str
    available_spare: int
    percentage_used: int
    critical_warnings: int
    power_on_hours: int


@dataclass
class DetectedDevice:
    """Complete detected device information."""
    device_path: str
    controller_id: int
    model: str
    serial_number: str
    firmware_version: str
    capacity_gb: float
    capacity_tb: float
    pcie_info: Optional[PCIeInfo]
    physical_location: PhysicalLocation
    capabilities: DeviceCapabilities
    health_summary: HealthSummary
    namespace_count: int
    detection_timestamp: str


@dataclass
class SystemSummary:
    """System-wide NVMe device summary."""
    total_devices: int
    total_capacity_tb: float
    device_types: Dict[str, int]
    interface_types: Dict[str, int]
    health_status_counts: Dict[str, int]
    oldest_device_hours: int
    newest_device_hours: int
    average_temperature: float


class NVMeDeviceDetector:
    """Comprehensive NVMe device detector and analyzer."""
    
    def __init__(self):
        """Initialize the device detector."""
        self.logger = setup_logging("INFO")
        self.detected_devices: List[DetectedDevice] = []

    def detect_all_devices(self) -> Tuple[List[DetectedDevice], SystemSummary]:
        """
        Detect and analyze all NVMe devices in the system.
        
        This function performs comprehensive device detection including:
        1. Basic device enumeration using nvme-cli
        2. PCIe topology analysis from sysfs
        3. Physical location detection
        4. Capability assessment
        5. Health status collection
        
        Returns:
            Tuple of (detected_devices, system_summary)
            
        Raises:
            NVMeCommandError: Failed to detect devices
        """
        print("🔍 Starting comprehensive NVMe device detection...")
        
        try:
            basic_devices = list_nvme_devices()
            print(f"✅ Found {len(basic_devices)} NVMe device(s) via nvme-cli")
        except Exception as e:
            print(f"❌ Failed to list devices: {e}")
            return [], self._create_empty_summary()
        
        detected_devices = []
        
        for device in basic_devices:
            try:
                device_path = device['device_path']
                print(f"🔍 Analyzing device: {device_path}")
                
                detected_device = self._analyze_single_device(device_path, device)
                detected_devices.append(detected_device)
                
            except Exception as e:
                print(f"⚠️  Failed to analyze {device.get('device_path', 'unknown')}: {e}")
        
        system_summary = self._generate_system_summary(detected_devices)
        
        self.detected_devices = detected_devices
        return detected_devices, system_summary

    def _analyze_single_device(self, device_path: str, basic_info: Dict) -> DetectedDevice:
        """Analyze a single NVMe device comprehensively."""
        
        device_info = get_controller_info(device_path)
        smart_data = get_smart_log(device_path)
        namespaces = get_device_namespaces(device_path)
        
        controller_match = re.search(r'nvme(\d+)', device_path)
        controller_id = int(controller_match.group(1)) if controller_match else 0
        
        pcie_info = self._get_pcie_info(device_path, controller_id)
        
        physical_location = self._determine_physical_location(pcie_info, device_info)
        
        capabilities = self._analyze_capabilities(device_info, namespaces)
        
        health_summary = self._create_health_summary(smart_data)
        
        total_capacity = basic_info.get('total_capacity', 0)
        capacity_gb = total_capacity / (1024**3) if total_capacity else 0
        capacity_tb = capacity_gb / 1024 if capacity_gb else 0
        
        return DetectedDevice(
            device_path=device_path,
            controller_id=controller_id,
            model=basic_info.get('model', 'Unknown').strip(),
            serial_number=basic_info.get('serial_number', 'Unknown').strip(),
            firmware_version=basic_info.get('firmware_revision', 'Unknown').strip(),
            capacity_gb=capacity_gb,
            capacity_tb=capacity_tb,
            pcie_info=pcie_info,
            physical_location=physical_location,
            capabilities=capabilities,
            health_summary=health_summary,
            namespace_count=len(namespaces),
            detection_timestamp=datetime.now().isoformat()
        )

    def _get_pcie_info(self, device_path: str, controller_id: int) -> Optional[PCIeInfo]:
        """Extract PCIe information from sysfs."""
        try:
            sysfs_path = f"/sys/class/nvme/nvme{controller_id}/device"
            
            if not os.path.exists(sysfs_path):
                return None
            
            def read_sysfs_file(filename: str, default: str = "Unknown") -> str:
                try:
                    with open(os.path.join(sysfs_path, filename), 'r') as f:
                        return f.read().strip()
                except:
                    return default
            
            try:
                real_path = os.path.realpath(sysfs_path)
                bus_id = os.path.basename(real_path)
            except:
                bus_id = "Unknown"
            
            current_link_speed = read_sysfs_file("current_link_speed", "Unknown")
            current_link_width = read_sysfs_file("current_link_width", "Unknown")
            max_link_speed = read_sysfs_file("max_link_speed", "Unknown")
            max_link_width = read_sysfs_file("max_link_width", "Unknown")
            
            numa_node_str = read_sysfs_file("numa_node", "-1")
            try:
                numa_node = int(numa_node_str)
            except:
                numa_node = -1
            
            return PCIeInfo(
                bus_id=bus_id,
                slot=read_sysfs_file("slot", "Unknown"),
                vendor_id=read_sysfs_file("vendor", "Unknown"),
                device_id=read_sysfs_file("device", "Unknown"),
                subsystem_vendor=read_sysfs_file("subsystem_vendor", "Unknown"),
                subsystem_device=read_sysfs_file("subsystem_device", "Unknown"),
                link_speed=current_link_speed,
                link_width=current_link_width,
                max_link_speed=max_link_speed,
                max_link_width=max_link_width,
                numa_node=numa_node
            )
            
        except Exception as e:
            print(f"⚠️  Could not get PCIe info: {e}")
            return None

    def _determine_physical_location(self, pcie_info: Optional[PCIeInfo], 
                                   device_info: Dict) -> PhysicalLocation:
        """Determine physical location and connection type."""
        
        form_factor = "Unknown"
        connector_type = "PCIe"
        slot_designation = "Unknown"
        removable = True
        hot_pluggable = False
        
        if pcie_info:
            if "M.2" in pcie_info.slot or "m2" in pcie_info.slot.lower():
                form_factor = "M.2"
                connector_type = "M.2"
                removable = True
                hot_pluggable = False
            elif "U.2" in pcie_info.slot or "u2" in pcie_info.slot.lower():
                form_factor = "U.2"
                connector_type = "U.2"
                removable = True
                hot_pluggable = True
            elif pcie_info.link_width in ["x4", "x8", "x16"]:
                form_factor = "PCIe Card"
                connector_type = f"PCIe {pcie_info.link_width}"
                removable = True
                hot_pluggable = False
            
            slot_designation = pcie_info.slot if pcie_info.slot != "Unknown" else pcie_info.bus_id
        
        return PhysicalLocation(
            form_factor=form_factor,
            connector_type=connector_type,
            slot_designation=slot_designation,
            removable=removable,
            hot_pluggable=hot_pluggable
        )

    def _analyze_capabilities(self, device_info: Dict, namespaces: List) -> DeviceCapabilities:
        """Analyze device capabilities and features."""
        
        security_features = []
        oacs = device_info.get('oacs', {})
        if oacs.get('security', False):
            security_features.append("Security Send/Receive")
        if oacs.get('format', False):
            security_features.append("Format NVM")
        
        sanicap = device_info.get('sanicap', {})
        if sanicap.get('ces', False):
            security_features.append("Crypto Erase")
        if sanicap.get('ber', False):
            security_features.append("Block Erase")
        
        power_states = len(device_info.get('psd', []))
        
        return DeviceCapabilities(
            max_namespaces=device_info.get('nn', 0),
            current_namespaces=len(namespaces),
            multipath_support=device_info.get('mic', {}).get('mp', False),
            security_features=security_features,
            power_states=power_states,
            queue_depth=device_info.get('maxcmd', 0),
            max_transfer_size=device_info.get('mdts', 0)
        )

    def _create_health_summary(self, smart_data: Dict) -> HealthSummary:
        """Create basic health status summary."""
        
        critical_warning = smart_data.get('critical_warning', 0)
        percentage_used = smart_data.get('percentage_used', 0)
        available_spare = smart_data.get('available_spare', 100)
        
        if critical_warning > 0:
            health_status = "Critical"
        elif percentage_used > 90 or available_spare < 10:
            health_status = "Warning"
        else:
            health_status = "Healthy"
        
        return HealthSummary(
            temperature=smart_data.get('temperature', 0),
            health_status=health_status,
            available_spare=available_spare,
            percentage_used=percentage_used,
            critical_warnings=critical_warning,
            power_on_hours=smart_data.get('power_on_hours', 0)
        )

    def _generate_system_summary(self, devices: List[DetectedDevice]) -> SystemSummary:
        """Generate system-wide summary statistics."""
        
        if not devices:
            return self._create_empty_summary()
        
        total_capacity_tb = sum(device.capacity_tb for device in devices)
        
        device_types = {}
        interface_types = {}
        health_status_counts = {}
        
        temperatures = []
        power_hours = []
        
        for device in devices:
            model_prefix = device.model.split()[0] if device.model else "Unknown"
            device_types[model_prefix] = device_types.get(model_prefix, 0) + 1
            
            interface = device.physical_location.form_factor
            interface_types[interface] = interface_types.get(interface, 0) + 1
            
            health = device.health_summary.health_status
            health_status_counts[health] = health_status_counts.get(health, 0) + 1
            
            if device.health_summary.temperature > 0:
                temperatures.append(device.health_summary.temperature)
            if device.health_summary.power_on_hours > 0:
                power_hours.append(device.health_summary.power_on_hours)
        
        return SystemSummary(
            total_devices=len(devices),
            total_capacity_tb=total_capacity_tb,
            device_types=device_types,
            interface_types=interface_types,
            health_status_counts=health_status_counts,
            oldest_device_hours=max(power_hours) if power_hours else 0,
            newest_device_hours=min(power_hours) if power_hours else 0,
            average_temperature=sum(temperatures) / len(temperatures) if temperatures else 0
        )

    def _create_empty_summary(self) -> SystemSummary:
        """Create empty system summary."""
        return SystemSummary(
            total_devices=0,
            total_capacity_tb=0.0,
            device_types={},
            interface_types={},
            health_status_counts={},
            oldest_device_hours=0,
            newest_device_hours=0,
            average_temperature=0.0
        )

    def display_detection_report(self, devices: List[DetectedDevice], 
                               summary: SystemSummary) -> None:
        """Display comprehensive device detection report."""
        
        print("\n" + "="*100)
        print("🔍 NVMe DEVICE DETECTION REPORT")
        print("="*100)
        
        print(f"\n📊 SYSTEM SUMMARY")
        print("-" * 50)
        print(f"Total NVMe Devices:  {summary.total_devices}")
        print(f"Total Capacity:      {summary.total_capacity_tb:.2f} TB")
        print(f"Average Temperature: {summary.average_temperature:.1f}°C")
        
        if summary.oldest_device_hours > 0:
            print(f"Oldest Device:       {summary.oldest_device_hours:,} hours ({summary.oldest_device_hours/8760:.1f} years)")
        if summary.newest_device_hours > 0:
            print(f"Newest Device:       {summary.newest_device_hours:,} hours ({summary.newest_device_hours/8760:.1f} years)")
        
        if summary.device_types:
            print(f"\n📱 DEVICE TYPES")
            print("-" * 30)
            for device_type, count in summary.device_types.items():
                print(f"{device_type:<20} {count} device(s)")
        
        if summary.interface_types:
            print(f"\n🔌 INTERFACE TYPES")
            print("-" * 30)
            for interface, count in summary.interface_types.items():
                print(f"{interface:<20} {count} device(s)")
        
        if summary.health_status_counts:
            print(f"\n🏥 HEALTH STATUS")
            print("-" * 30)
            for status, count in summary.health_status_counts.items():
                emoji = {"Healthy": "✅", "Warning": "⚠️", "Critical": "🚨"}.get(status, "❓")
                print(f"{emoji} {status:<15} {count} device(s)")
        
        if devices:
            print(f"\n📋 DETAILED DEVICE INFORMATION")
            print("="*100)
            
            for i, device in enumerate(devices, 1):
                print(f"\n🔧 DEVICE {i}: {device.device_path}")
                print("-" * 60)
                
                print(f"Model:               {device.model}")
                print(f"Serial Number:       {device.serial_number}")
                print(f"Firmware:            {device.firmware_version}")
                print(f"Capacity:            {device.capacity_gb:.2f} GB ({device.capacity_tb:.3f} TB)")
                print(f"Namespaces:          {device.namespace_count}")
                
                print(f"Form Factor:         {device.physical_location.form_factor}")
                print(f"Connector:           {device.physical_location.connector_type}")
                print(f"Slot:                {device.physical_location.slot_designation}")
                print(f"Removable:           {'Yes' if device.physical_location.removable else 'No'}")
                print(f"Hot-Pluggable:       {'Yes' if device.physical_location.hot_pluggable else 'No'}")
                
                if device.pcie_info:
                    print(f"PCIe Bus ID:         {device.pcie_info.bus_id}")
                    print(f"Link Speed:          {device.pcie_info.link_speed} (Max: {device.pcie_info.max_link_speed})")
                    print(f"Link Width:          {device.pcie_info.link_width} (Max: {device.pcie_info.max_link_width})")
                    if device.pcie_info.numa_node >= 0:
                        print(f"NUMA Node:           {device.pcie_info.numa_node}")
                
                print(f"Max Namespaces:      {device.capabilities.max_namespaces}")
                print(f"Queue Depth:         {device.capabilities.queue_depth}")
                print(f"Power States:        {device.capabilities.power_states}")
                if device.capabilities.security_features:
                    print(f"Security Features:   {', '.join(device.capabilities.security_features)}")
                
                health_emoji = {"Healthy": "✅", "Warning": "⚠️", "Critical": "🚨"}.get(
                    device.health_summary.health_status, "❓")
                print(f"Health Status:       {health_emoji} {device.health_summary.health_status}")
                print(f"Temperature:         {device.health_summary.temperature}°C")
                print(f"Available Spare:     {device.health_summary.available_spare}%")
                print(f"Percentage Used:     {device.health_summary.percentage_used}%")
                print(f"Power-On Hours:      {device.health_summary.power_on_hours:,} hours")
                
                if device.health_summary.critical_warnings > 0:
                    print(f"Critical Warnings:   {device.health_summary.critical_warnings}")
        
        print("="*100)

    def export_detection_results(self, devices: List[DetectedDevice], 
                                summary: SystemSummary, filename: str) -> None:
        """Export detection results to JSON file."""
        try:
            export_data = {
                'detection_timestamp': datetime.now().isoformat(),
                'system_summary': asdict(summary),
                'detected_devices': [asdict(device) for device in devices]
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            print(f"✅ Detection results exported to: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to export results: {e}")


def main():
    """Main entry point for NVMe device detector."""
    print("🔍 NVMe SSD Device Detector")
    print("="*40)
    
    if not check_nvme_cli_availability():
        print("❌ nvme-cli not available. Please install:")
        print("   Ubuntu/Debian: sudo apt install nvme-cli")
        print("   RHEL/CentOS: sudo yum install nvme-cli")
        return 1
    
    export_json = "--json" in sys.argv or "-j" in sys.argv
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    try:
        detector = NVMeDeviceDetector()
        devices, summary = detector.detect_all_devices()
        
        if not devices:
            print("❌ No NVMe devices detected in the system")
            return 1
        
        detector.display_detection_report(devices, summary)
        
        if export_json:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nvme_detection_report_{timestamp}.json"
            detector.export_detection_results(devices, summary, filename)
        
        if summary.health_status_counts.get("Critical", 0) > 0:
            return 2  # Critical issues found
        elif summary.health_status_counts.get("Warning", 0) > 0:
            return 1  # Warnings found
        else:
            return 0  # All devices healthy
        
    except Exception as e:
        print(f"❌ Detection failed: {e}")
        return 3


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Detection cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
