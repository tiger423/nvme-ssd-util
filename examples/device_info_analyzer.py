#!/usr/bin/env python3
"""
NVMe SSD Detailed Information Analyzer

This example demonstrates how to collect and display comprehensive information
about NVMe SSDs, including device specifications, capabilities, and current status.

INFORMATION COLLECTION WORKFLOW:
┌─────────────────────────────────────────────────────────────────┐
│ Device Discovery → Controller Info → Namespace Details →       │
│ SMART Data → Feature Analysis → Capability Assessment →        │
│ Performance Metrics → Comprehensive Report                     │
└─────────────────────────────────────────────────────────────────┘

INFORMATION CATEGORIES:
🔧 Device Identification (model, serial, firmware)
📊 Capacity and Geometry (size, block sizes, namespace configuration)
⚡ Performance Specifications (queue depth, transfer rates)
🛡️  Security Features (encryption, secure erase capabilities)
🔋 Power Management (power states, consumption)
📈 Current Status (temperature, health, utilization)
🎯 Advanced Features (NVMe version, optional commands)

TECHNICAL DETAILS COLLECTED:
- Controller identification and capabilities
- Namespace configuration and LBA formats
- SMART attributes and health indicators
- Feature support matrix
- Power state information
- Security and encryption status
- Performance characteristics
- Firmware and hardware details

For technical documentation:
- Function reference: ../docs/FUNCTION_REFERENCE.md
- Integration patterns: ../docs/NVME_FORMAT_CODE_FLOW.md
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from nvme_health_monitor.core.nvme_interface import (
    check_nvme_cli_availability,
    list_nvme_devices,
    get_controller_info,
    get_smart_log,
    get_device_namespaces,
    get_namespace_info
)
from nvme_health_monitor.models.exceptions import (
    NVMeCommandError,
    NVMeDeviceNotFoundError,
    NVMePermissionError
)
from nvme_health_monitor.utils.logging_config import setup_logging


@dataclass
class DeviceIdentification:
    """Device identification information."""
    model_number: str
    serial_number: str
    firmware_revision: str
    vendor_id: str
    subsystem_vendor_id: str
    ieee_oui: str
    controller_id: int


@dataclass
class CapacityInfo:
    """Device capacity and geometry information."""
    total_capacity_bytes: int
    total_capacity_gb: float
    total_capacity_tb: float
    unallocated_capacity: int
    namespace_count: int
    max_namespaces: int
    namespace_details: List[Dict[str, Any]]


@dataclass
class PerformanceSpecs:
    """Performance specifications and capabilities."""
    max_data_transfer_size: int
    max_outstanding_commands: int
    submission_queue_entries: int
    completion_queue_entries: int
    arbitration_burst: int
    weighted_round_robin: bool
    vendor_specific_arbitration: bool


@dataclass
class SecurityFeatures:
    """Security and encryption capabilities."""
    security_send_receive: bool
    format_nvm: bool
    security_erase: bool
    crypto_erase: bool
    sanitize_support: bool
    opal_support: bool
    encryption_support: bool


@dataclass
class PowerManagement:
    """Power management information."""
    power_states: List[Dict[str, Any]]
    current_power_state: int
    power_state_change_support: bool
    autonomous_power_state_transition: bool


@dataclass
class CurrentStatus:
    """Current device status and health."""
    temperature_celsius: int
    available_spare_percent: int
    percentage_used: int
    critical_warnings: List[str]
    power_on_hours: int
    power_cycles: int
    unsafe_shutdowns: int
    media_errors: int
    error_log_entries: int


@dataclass
class AdvancedFeatures:
    """Advanced NVMe features and capabilities."""
    nvme_version: str
    optional_admin_commands: List[str]
    optional_nvm_commands: List[str]
    log_page_attributes: Dict[str, bool]
    identify_controller_extensions: bool
    namespace_management: bool
    firmware_update_support: bool
    telemetry_support: bool


@dataclass
class ComprehensiveDeviceInfo:
    """Complete device information structure."""
    device_path: str
    scan_timestamp: str
    identification: DeviceIdentification
    capacity: CapacityInfo
    performance: PerformanceSpecs
    security: SecurityFeatures
    power_management: PowerManagement
    current_status: CurrentStatus
    advanced_features: AdvancedFeatures
    raw_data: Dict[str, Any]  # Store raw nvme-cli output


class NVMeDeviceAnalyzer:
    """Comprehensive NVMe device information analyzer."""
    
    def __init__(self):
        """Initialize the device analyzer."""
        self.logger = setup_logging("INFO")

    def analyze_device(self, device_path: str) -> ComprehensiveDeviceInfo:
        """
        Perform comprehensive analysis of NVMe device.
        
        This function collects and analyzes all available information about
        an NVMe device, including controller capabilities, namespace configuration,
        current health status, and advanced features.
        
        Args:
            device_path: NVMe device path (e.g., "/dev/nvme0")
            
        Returns:
            ComprehensiveDeviceInfo: Complete device analysis
            
        Raises:
            NVMeDeviceNotFoundError: Device not found
            NVMeCommandError: Failed to collect device information
        """
        print(f"🔍 Analyzing device: {device_path}")
        
        device_info = get_controller_info(device_path)
        smart_data = get_smart_log(device_path)
        namespaces = get_device_namespaces(device_path)
        
        namespace_details = []
        for ns in namespaces:
            try:
                ns_info = get_namespace_info(device_path, ns.get('nsid', 1))
                namespace_details.append(ns_info)
            except Exception as e:
                print(f"⚠️  Could not get info for namespace {ns.get('nsid')}: {e}")
        
        identification = self._parse_identification(device_info)
        capacity = self._parse_capacity(device_info, namespaces, namespace_details)
        performance = self._parse_performance(device_info)
        security = self._parse_security_features(device_info)
        power_mgmt = self._parse_power_management(device_info)
        current_status = self._parse_current_status(smart_data)
        advanced_features = self._parse_advanced_features(device_info)
        
        return ComprehensiveDeviceInfo(
            device_path=device_path,
            scan_timestamp=datetime.now().isoformat(),
            identification=identification,
            capacity=capacity,
            performance=performance,
            security=security,
            power_management=power_mgmt,
            current_status=current_status,
            advanced_features=advanced_features,
            raw_data={
                'device_info': device_info,
                'smart_data': smart_data,
                'namespaces': namespaces,
                'namespace_details': namespace_details
            }
        )

    def _parse_identification(self, device_info: Dict) -> DeviceIdentification:
        """Parse device identification information."""
        return DeviceIdentification(
            model_number=device_info.get('mn', 'Unknown').strip(),
            serial_number=device_info.get('sn', 'Unknown').strip(),
            firmware_revision=device_info.get('fr', 'Unknown').strip(),
            vendor_id=device_info.get('vid', 'Unknown'),
            subsystem_vendor_id=device_info.get('ssvid', 'Unknown'),
            ieee_oui=device_info.get('ieee', 'Unknown'),
            controller_id=device_info.get('cntlid', 0)
        )

    def _parse_capacity(self, device_info: Dict, namespaces: List, 
                       namespace_details: List) -> CapacityInfo:
        """Parse capacity and geometry information."""
        total_capacity = device_info.get('tnvmcap', 0)
        unallocated = device_info.get('unvmcap', 0)
        
        return CapacityInfo(
            total_capacity_bytes=total_capacity,
            total_capacity_gb=total_capacity / (1024**3) if total_capacity else 0,
            total_capacity_tb=total_capacity / (1024**4) if total_capacity else 0,
            unallocated_capacity=unallocated,
            namespace_count=len(namespaces),
            max_namespaces=device_info.get('nn', 0),
            namespace_details=namespace_details
        )

    def _parse_performance(self, device_info: Dict) -> PerformanceSpecs:
        """Parse performance specifications."""
        return PerformanceSpecs(
            max_data_transfer_size=device_info.get('mdts', 0),
            max_outstanding_commands=device_info.get('maxcmd', 0),
            submission_queue_entries=device_info.get('sqes', {}).get('max', 0),
            completion_queue_entries=device_info.get('cqes', {}).get('max', 0),
            arbitration_burst=device_info.get('ab', 0),
            weighted_round_robin=bool(device_info.get('arb_mechanisms', {}).get('wrr', False)),
            vendor_specific_arbitration=bool(device_info.get('arb_mechanisms', {}).get('vs', False))
        )

    def _parse_security_features(self, device_info: Dict) -> SecurityFeatures:
        """Parse security and encryption capabilities."""
        oacs = device_info.get('oacs', {})
        sanicap = device_info.get('sanicap', {})
        
        return SecurityFeatures(
            security_send_receive=bool(oacs.get('security', False)),
            format_nvm=bool(oacs.get('format', False)),
            security_erase=bool(sanicap.get('ces', False)),
            crypto_erase=bool(sanicap.get('cer', False)),
            sanitize_support=bool(sanicap.get('sanitize', False)),
            opal_support=self._check_opal_support(device_info),
            encryption_support=self._check_encryption_support(device_info)
        )

    def _parse_power_management(self, device_info: Dict) -> PowerManagement:
        """Parse power management information."""
        power_states = device_info.get('psd', [])
        
        return PowerManagement(
            power_states=power_states,
            current_power_state=0,  # Would need additional command to get current state
            power_state_change_support=len(power_states) > 1,
            autonomous_power_state_transition=bool(device_info.get('apsta', {}).get('apst', False))
        )

    def _parse_current_status(self, smart_data: Dict) -> CurrentStatus:
        """Parse current device status from SMART data."""
        critical_warning = smart_data.get('critical_warning', 0)
        warnings = []
        
        if critical_warning & 0x01:
            warnings.append("Available spare below threshold")
        if critical_warning & 0x02:
            warnings.append("Temperature above threshold")
        if critical_warning & 0x04:
            warnings.append("NVM subsystem reliability degraded")
        if critical_warning & 0x08:
            warnings.append("Media in read-only mode")
        if critical_warning & 0x10:
            warnings.append("Volatile memory backup device failed")
        
        return CurrentStatus(
            temperature_celsius=smart_data.get('temperature', 0),
            available_spare_percent=smart_data.get('available_spare', 100),
            percentage_used=smart_data.get('percentage_used', 0),
            critical_warnings=warnings,
            power_on_hours=smart_data.get('power_on_hours', 0),
            power_cycles=smart_data.get('power_cycles', 0),
            unsafe_shutdowns=smart_data.get('unsafe_shutdowns', 0),
            media_errors=smart_data.get('media_errors', 0),
            error_log_entries=smart_data.get('num_err_log_entries', 0)
        )

    def _parse_advanced_features(self, device_info: Dict) -> AdvancedFeatures:
        """Parse advanced NVMe features and capabilities."""
        ver = device_info.get('ver', 0)
        nvme_version = f"{(ver >> 16) & 0xFFFF}.{(ver >> 8) & 0xFF}.{ver & 0xFF}"
        
        oacs = device_info.get('oacs', {})
        oncs = device_info.get('oncs', {})
        
        optional_admin = []
        if oacs.get('security', False):
            optional_admin.append("Security Send/Receive")
        if oacs.get('format', False):
            optional_admin.append("Format NVM")
        if oacs.get('firmware', False):
            optional_admin.append("Firmware Commit/Download")
        if oacs.get('ns_manage', False):
            optional_admin.append("Namespace Management")
        
        optional_nvm = []
        if oncs.get('compare', False):
            optional_nvm.append("Compare")
        if oncs.get('write_unc', False):
            optional_nvm.append("Write Uncorrectable")
        if oncs.get('dsm', False):
            optional_nvm.append("Dataset Management")
        if oncs.get('write_zeroes', False):
            optional_nvm.append("Write Zeroes")
        
        return AdvancedFeatures(
            nvme_version=nvme_version,
            optional_admin_commands=optional_admin,
            optional_nvm_commands=optional_nvm,
            log_page_attributes=device_info.get('lpa', {}),
            identify_controller_extensions=bool(device_info.get('oaes', {}).get('cfg_change', False)),
            namespace_management=bool(oacs.get('ns_manage', False)),
            firmware_update_support=bool(oacs.get('firmware', False)),
            telemetry_support=bool(device_info.get('lpa', {}).get('telemetry', False))
        )

    def _check_opal_support(self, device_info: Dict) -> bool:
        """Check for OPAL/TCG security support."""
        return bool(device_info.get('oacs', {}).get('security', False))

    def _check_encryption_support(self, device_info: Dict) -> bool:
        """Check for hardware encryption support."""
        return bool(device_info.get('oacs', {}).get('security', False))

    def display_device_report(self, info: ComprehensiveDeviceInfo) -> None:
        """Display comprehensive device information report."""
        print("\n" + "="*100)
        print("📱 COMPREHENSIVE NVMe DEVICE INFORMATION REPORT")
        print("="*100)
        
        print(f"\n🔧 DEVICE: {info.device_path}")
        print(f"📅 SCAN TIME: {info.scan_timestamp}")
        
        print(f"\n📋 DEVICE IDENTIFICATION")
        print("-" * 50)
        print(f"Model Number:        {info.identification.model_number}")
        print(f"Serial Number:       {info.identification.serial_number}")
        print(f"Firmware Revision:   {info.identification.firmware_revision}")
        print(f"Vendor ID:           {info.identification.vendor_id}")
        print(f"Subsystem Vendor:    {info.identification.subsystem_vendor_id}")
        print(f"IEEE OUI:            {info.identification.ieee_oui}")
        print(f"Controller ID:       {info.identification.controller_id}")
        
        print(f"\n💾 CAPACITY & GEOMETRY")
        print("-" * 50)
        print(f"Total Capacity:      {info.capacity.total_capacity_gb:.2f} GB ({info.capacity.total_capacity_tb:.3f} TB)")
        print(f"Raw Capacity:        {info.capacity.total_capacity_bytes:,} bytes")
        print(f"Unallocated:         {info.capacity.unallocated_capacity:,} bytes")
        print(f"Namespace Count:     {info.capacity.namespace_count}")
        print(f"Max Namespaces:      {info.capacity.max_namespaces}")
        
        if info.capacity.namespace_details:
            print(f"\n📂 NAMESPACE DETAILS")
            print("-" * 50)
            for i, ns in enumerate(info.capacity.namespace_details):
                nsid = ns.get('nsid', i+1)
                size = ns.get('nsze', 0)
                capacity = ns.get('ncap', 0)
                current_lbaf = ns.get('flbas', {}).get('format', 0)
                
                print(f"Namespace {nsid}:")
                print(f"  Size:              {size:,} blocks")
                print(f"  Capacity:          {capacity:,} blocks")
                print(f"  Current LBA Format: {current_lbaf}")
                
                if 'lbaf' in ns:
                    print(f"  Available LBA Formats:")
                    for lbaf_idx, lbaf in enumerate(ns['lbaf']):
                        if isinstance(lbaf, dict) and lbaf.get('ds', 0) > 0:
                            data_size = lbaf.get('ds', 0)
                            metadata = lbaf.get('ms', 0)
                            performance = lbaf.get('rp', 0)
                            current = "✓" if lbaf_idx == current_lbaf else " "
                            print(f"    {current} LBAF {lbaf_idx}: {data_size} bytes/block, {metadata} metadata, perf={performance}")
        
        print(f"\n⚡ PERFORMANCE SPECIFICATIONS")
        print("-" * 50)
        print(f"Max Data Transfer:   {info.performance.max_data_transfer_size} bytes")
        print(f"Max Outstanding Cmds: {info.performance.max_outstanding_commands}")
        print(f"Submission Queue:    {info.performance.submission_queue_entries} entries")
        print(f"Completion Queue:    {info.performance.completion_queue_entries} entries")
        print(f"Arbitration Burst:   {info.performance.arbitration_burst}")
        print(f"Weighted Round Robin: {'Yes' if info.performance.weighted_round_robin else 'No'}")
        print(f"Vendor Arbitration:  {'Yes' if info.performance.vendor_specific_arbitration else 'No'}")
        
        print(f"\n🛡️  SECURITY FEATURES")
        print("-" * 50)
        print(f"Security Send/Recv:  {'Yes' if info.security.security_send_receive else 'No'}")
        print(f"Format NVM:          {'Yes' if info.security.format_nvm else 'No'}")
        print(f"Security Erase:      {'Yes' if info.security.security_erase else 'No'}")
        print(f"Crypto Erase:        {'Yes' if info.security.crypto_erase else 'No'}")
        print(f"Sanitize Support:    {'Yes' if info.security.sanitize_support else 'No'}")
        print(f"OPAL Support:        {'Yes' if info.security.opal_support else 'No'}")
        print(f"Encryption Support:  {'Yes' if info.security.encryption_support else 'No'}")
        
        print(f"\n🔋 POWER MANAGEMENT")
        print("-" * 50)
        print(f"Power States:        {len(info.power_management.power_states)} available")
        print(f"Current State:       {info.power_management.current_power_state}")
        print(f"State Change Support: {'Yes' if info.power_management.power_state_change_support else 'No'}")
        print(f"Auto Power State:    {'Yes' if info.power_management.autonomous_power_state_transition else 'No'}")
        
        if info.power_management.power_states:
            print("Available Power States:")
            for i, ps in enumerate(info.power_management.power_states):
                max_power = ps.get('max_power', 0)
                idle_power = ps.get('idle_power', 0)
                active_power = ps.get('active_power', 0)
                print(f"  State {i}: Max={max_power}mW, Idle={idle_power}mW, Active={active_power}mW")
        
        print(f"\n📊 CURRENT STATUS")
        print("-" * 50)
        print(f"Temperature:         {info.current_status.temperature_celsius}°C")
        print(f"Available Spare:     {info.current_status.available_spare_percent}%")
        print(f"Percentage Used:     {info.current_status.percentage_used}%")
        print(f"Power-On Hours:      {info.current_status.power_on_hours:,} hours ({info.current_status.power_on_hours/8760:.1f} years)")
        print(f"Power Cycles:        {info.current_status.power_cycles:,}")
        print(f"Unsafe Shutdowns:    {info.current_status.unsafe_shutdowns:,}")
        print(f"Media Errors:        {info.current_status.media_errors:,}")
        print(f"Error Log Entries:   {info.current_status.error_log_entries:,}")
        
        if info.current_status.critical_warnings:
            print(f"Critical Warnings:   {', '.join(info.current_status.critical_warnings)}")
        else:
            print(f"Critical Warnings:   None")
        
        print(f"\n🎯 ADVANCED FEATURES")
        print("-" * 50)
        print(f"NVMe Version:        {info.advanced_features.nvme_version}")
        print(f"Namespace Management: {'Yes' if info.advanced_features.namespace_management else 'No'}")
        print(f"Firmware Update:     {'Yes' if info.advanced_features.firmware_update_support else 'No'}")
        print(f"Telemetry Support:   {'Yes' if info.advanced_features.telemetry_support else 'No'}")
        
        if info.advanced_features.optional_admin_commands:
            print(f"Optional Admin Cmds: {', '.join(info.advanced_features.optional_admin_commands)}")
        
        if info.advanced_features.optional_nvm_commands:
            print(f"Optional NVM Cmds:   {', '.join(info.advanced_features.optional_nvm_commands)}")
        
        print("="*100)

    def export_to_json(self, info: ComprehensiveDeviceInfo, filename: str) -> None:
        """Export device information to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(asdict(info), f, indent=2, default=str)
            print(f"✅ Device information exported to: {filename}")
        except Exception as e:
            print(f"❌ Failed to export to JSON: {e}")


def analyze_single_device(device_path: str, export_json: bool = False) -> None:
    """Analyze a single NVMe device."""
    analyzer = NVMeDeviceAnalyzer()
    
    try:
        info = analyzer.analyze_device(device_path)
        analyzer.display_device_report(info)
        
        if export_json:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            device_name = device_path.replace('/', '_')
            filename = f"nvme_device_info_{device_name}_{timestamp}.json"
            analyzer.export_to_json(info, filename)
            
    except NVMeDeviceNotFoundError:
        print(f"❌ Device not found: {device_path}")
    except NVMePermissionError:
        print(f"❌ Permission denied accessing {device_path}")
        print("Try running with sudo or ensure user is in nvme group")
    except Exception as e:
        print(f"❌ Error analyzing device: {e}")


def analyze_all_devices(export_json: bool = False) -> None:
    """Analyze all NVMe devices in the system."""
    print("🔍 Discovering NVMe devices...")
    
    try:
        devices = list_nvme_devices()
        if not devices:
            print("❌ No NVMe devices found in the system")
            return
        
        print(f"✅ Found {len(devices)} NVMe device(s)")
        
        analyzer = NVMeDeviceAnalyzer()
        
        for i, device in enumerate(devices, 1):
            device_path = device['device_path']
            print(f"\n{'='*80}")
            print(f"📱 ANALYZING DEVICE {i}/{len(devices)}: {device_path}")
            print('='*80)
            
            try:
                info = analyzer.analyze_device(device_path)
                analyzer.display_device_report(info)
                
                if export_json:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    device_name = device_path.replace('/', '_')
                    filename = f"nvme_device_info_{device_name}_{timestamp}.json"
                    analyzer.export_to_json(info, filename)
                    
            except Exception as e:
                print(f"❌ Failed to analyze {device_path}: {e}")
        
    except Exception as e:
        print(f"❌ Error discovering devices: {e}")


def main():
    """Main entry point for device information analyzer."""
    print("📱 NVMe SSD Detailed Information Analyzer")
    print("="*60)
    
    if not check_nvme_cli_availability():
        print("❌ nvme-cli not available. Please install:")
        print("   Ubuntu/Debian: sudo apt install nvme-cli")
        print("   RHEL/CentOS: sudo yum install nvme-cli")
        return 1
    
    export_json = "--json" in sys.argv or "-j" in sys.argv
    
    device_args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
    
    if device_args:
        device_path = device_args[0]
        print(f"Analyzing specific device: {device_path}")
        analyze_single_device(device_path, export_json)
    else:
        print("Analyzing all NVMe devices in system...")
        analyze_all_devices(export_json)
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Analysis cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
