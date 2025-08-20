#!/usr/bin/env python3
"""
Interactive NVMe SSD Formatting Tool with LBAF Support

PRODUCTION-READY INTERACTIVE TOOL

This comprehensive tool provides a safe, menu-driven interface for formatting
NVMe SSDs with advanced features and multiple safety mechanisms.

WORKFLOW ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────┐
│ Prerequisites → Device Selection → Namespace Selection →       │
│ LBA Format Selection → Safety Confirmations → Format →         │
│ Progress Monitoring → Verification → Results                   │
└─────────────────────────────────────────────────────────────────┘

KEY FEATURES:
✅ Menu-driven device and namespace selection
✅ Detailed LBA format analysis and selection
✅ Multiple safety confirmation prompts
✅ Real-time progress monitoring with timeout handling
✅ Automatic format verification
✅ Comprehensive error handling and recovery
✅ User-friendly progress indicators and status updates

SAFETY MECHANISMS:
🔒 Multiple confirmation prompts with exact text matching
🔒 Device path validation and existence checking
🔒 LBA format validation against device capabilities
🔒 Progress monitoring with timeout protection
🔒 Automatic verification of format results
🔒 Comprehensive error handling with user guidance

TECHNICAL IMPLEMENTATION:
- Uses NVMeFormatter class for state management
- Implements robust error handling for all operations
- Provides detailed progress feedback and status updates
- Supports timeout handling for long-running operations
- Includes format verification to ensure success

⚠️  CAUTION: This tool will permanently erase data. Use with extreme care!

For technical documentation:
- Code flow: ../docs/NVME_FORMAT_CODE_FLOW.md
- Function reference: ../docs/FUNCTION_REFERENCE.md
"""

import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from nvme_health_monitor.core.nvme_interface import (
    check_nvme_cli_availability,
    list_nvme_devices,
    get_device_namespaces,
    get_namespace_info,
    format_namespace,
    get_format_status,
    get_smart_log
)
from nvme_health_monitor.models.exceptions import (
    NVMeCommandError,
    NVMeDeviceNotFoundError,
    NVMePermissionError,
    NVMeTimeoutError
)
from nvme_health_monitor.utils.logging_config import setup_logging


class NVMeFormatter:
    """Interactive NVMe formatting tool."""
    
    def __init__(self):
        self.logger = setup_logging("INFO")
        self.selected_device = None
        self.selected_namespace = None
        self.selected_lbaf = None
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        print("🔍 Checking prerequisites...")
        
        if not check_nvme_cli_availability():
            print("❌ nvme-cli is not available")
            print("   Install with: sudo apt install nvme-cli (Ubuntu/Debian)")
            print("   Or: sudo yum install nvme-cli (RHEL/CentOS)")
            return False
        
        print("✅ nvme-cli is available")
        return True
    
    def list_and_select_device(self) -> Optional[Dict[str, Any]]:
        """List devices and let user select one."""
        try:
            devices = list_nvme_devices()
            
            if not devices:
                print("❌ No NVMe devices found")
                return None
            
            print(f"\n📋 Found {len(devices)} NVMe device(s):")
            print("-" * 80)
            print(f"{'#':<3} {'Device Path':<15} {'Model':<30} {'Serial':<20}")
            print("-" * 80)
            
            for i, device in enumerate(devices):
                print(f"{i+1:<3} {device['device_path']:<15} {device['model'][:29]:<30} {device['serial_number']:<20}")
            
            while True:
                try:
                    choice = input(f"\nSelect device (1-{len(devices)}) or 'q' to quit: ").strip()
                    
                    if choice.lower() == 'q':
                        return None
                    
                    device_idx = int(choice) - 1
                    if 0 <= device_idx < len(devices):
                        selected = devices[device_idx]
                        print(f"✅ Selected: {selected['device_path']} - {selected['model']}")
                        return selected
                    else:
                        print(f"❌ Invalid choice. Please enter 1-{len(devices)}")
                        
                except ValueError:
                    print("❌ Invalid input. Please enter a number or 'q'")
                    
        except Exception as e:
            print(f"❌ Error listing devices: {e}")
            return None
    
    def select_namespace(self, device_path: str) -> Optional[int]:
        """Select namespace for the device."""
        try:
            namespaces = get_device_namespaces(device_path)
            
            if not namespaces:
                print("❌ No namespaces found")
                return None
            
            print(f"\n📂 Found {len(namespaces)} namespace(s) for {device_path}:")
            print("-" * 60)
            print(f"{'#':<3} {'NSID':<6} {'Size (GB)':<12} {'Capacity (GB)':<15}")
            print("-" * 60)
            
            for i, ns in enumerate(namespaces):
                size_gb = ns.get('size', 0) / (1024**3) if ns.get('size') else 0
                capacity_gb = ns.get('capacity', 0) / (1024**3) if ns.get('capacity') else 0
                print(f"{i+1:<3} {ns.get('nsid', 'N/A'):<6} {size_gb:<12.1f} {capacity_gb:<15.1f}")
            
            while True:
                try:
                    choice = input(f"\nSelect namespace (1-{len(namespaces)}) or 'q' to quit: ").strip()
                    
                    if choice.lower() == 'q':
                        return None
                    
                    ns_idx = int(choice) - 1
                    if 0 <= ns_idx < len(namespaces):
                        selected_nsid = namespaces[ns_idx].get('nsid', 1)
                        print(f"✅ Selected namespace: {selected_nsid}")
                        return selected_nsid
                    else:
                        print(f"❌ Invalid choice. Please enter 1-{len(namespaces)}")
                        
                except ValueError:
                    print("❌ Invalid input. Please enter a number or 'q'")
                    
        except Exception as e:
            print(f"❌ Error getting namespaces: {e}")
            return None
    
    def select_lba_format(self, device_path: str, namespace_id: int) -> Optional[int]:
        """Select LBA format for formatting."""
        try:
            namespace_info = get_namespace_info(device_path, namespace_id)
            
            if 'lbaf' not in namespace_info:
                print("❌ No LBA format information available")
                return None
            
            lba_formats = namespace_info['lbaf']
            current_lbaf = namespace_info.get('flbas', {}).get('format', 0)
            
            print(f"\n🔧 Available LBA Formats for {device_path}n{namespace_id}:")
            print(f"Current format: {current_lbaf}")
            print("-" * 70)
            print(f"{'#':<3} {'Index':<6} {'Data Size':<12} {'Metadata':<10} {'Performance':<12}")
            print("-" * 70)
            
            valid_formats = []
            for i, lbaf in enumerate(lba_formats):
                if isinstance(lbaf, dict) and lbaf.get('ds', 0) > 0:
                    data_size = lbaf.get('ds', 0)
                    metadata_size = lbaf.get('ms', 0)
                    relative_perf = lbaf.get('rp', 0)
                    
                    perf_desc = {0: "Best", 1: "Better", 2: "Good", 3: "Degraded"}.get(relative_perf, "Unknown")
                    current_marker = " (current)" if i == current_lbaf else ""
                    
                    print(f"{len(valid_formats)+1:<3} {i:<6} {data_size:<12} {metadata_size:<10} {perf_desc:<12}{current_marker}")
                    valid_formats.append(i)
            
            if not valid_formats:
                print("❌ No valid LBA formats found")
                return None
            
            while True:
                try:
                    choice = input(f"\nSelect LBA format (1-{len(valid_formats)}) or 'q' to quit: ").strip()
                    
                    if choice.lower() == 'q':
                        return None
                    
                    format_idx = int(choice) - 1
                    if 0 <= format_idx < len(valid_formats):
                        selected_lbaf = valid_formats[format_idx]
                        print(f"✅ Selected LBA format: {selected_lbaf}")
                        return selected_lbaf
                    else:
                        print(f"❌ Invalid choice. Please enter 1-{len(valid_formats)}")
                        
                except ValueError:
                    print("❌ Invalid input. Please enter a number or 'q'")
                    
        except Exception as e:
            print(f"❌ Error getting LBA formats: {e}")
            return None
    
    def confirm_format(self, device_path: str, namespace_id: int, lbaf: int) -> bool:
        """Get user confirmation for destructive format operation."""
        print("\n" + "⚠️ " * 25)
        print("CRITICAL WARNING: DATA DESTRUCTION IMMINENT!")
        print("⚠️ " * 25)
        print(f"\nYou are about to FORMAT:")
        print(f"  Device: {device_path}")
        print(f"  Namespace: {namespace_id}")
        print(f"  LBA Format: {lbaf}")
        print(f"\n🔥 THIS WILL PERMANENTLY ERASE ALL DATA!")
        print("🔥 THIS OPERATION CANNOT BE UNDONE!")
        print("🔥 MAKE SURE YOU HAVE BACKUPS!")
        
        print("\nTo proceed, you must type exactly: 'I UNDERSTAND DATA WILL BE LOST'")
        confirmation = input("Confirmation: ").strip()
        
        if confirmation != "I UNDERSTAND DATA WILL BE LOST":
            print("❌ Format cancelled - confirmation text did not match")
            return False
        
        print("\nFinal confirmation - type 'YES' to proceed with format:")
        final_confirm = input("Final confirmation: ").strip().upper()
        
        if final_confirm != "YES":
            print("❌ Format cancelled")
            return False
        
        return True
    
    def perform_format(self, device_path: str, namespace_id: int, lbaf: int) -> bool:
        """Perform the actual format operation."""
        try:
            print(f"\n🔧 Starting format operation...")
            print(f"Device: {device_path}n{namespace_id}")
            print(f"LBA Format: {lbaf}")
            print(f"Secure Erase: User data")
            
            success = format_namespace(device_path, namespace_id, lbaf, secure_erase="user")
            
            if not success:
                print("❌ Failed to start format operation")
                return False
            
            print("✅ Format command issued successfully")
            return True
            
        except Exception as e:
            print(f"❌ Format failed: {e}")
            return False
    
    def monitor_format_progress(self, device_path: str, timeout_minutes: int = 60) -> bool:
        """Monitor format progress until completion."""
        print(f"\n📊 Monitoring format progress (timeout: {timeout_minutes} minutes)...")
        print("Format progress will be displayed below:")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        last_progress = -1
        dots = 0
        
        while True:
            try:
                status = get_format_status(device_path)
                
                if not status['is_formatting']:
                    print(f"\n✅ Format completed!")
                    return True
                
                progress = status['progress_percent']
                if progress != last_progress:
                    elapsed_min = (time.time() - start_time) / 60
                    print(f"\n📊 Progress: {progress}% (elapsed: {elapsed_min:.1f} min)")
                    last_progress = progress
                    dots = 0
                else:
                    print(".", end="", flush=True)
                    dots += 1
                    if dots >= 60:  # New line every 60 dots (5 minutes)
                        print()
                        dots = 0
                
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    print(f"\n⏰ Format timeout after {timeout_minutes} minutes")
                    print("The format may still be in progress. Check device status manually.")
                    return False
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"\n⚠️  Error checking format status: {e}")
                time.sleep(10)  # Wait longer on error
                
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    return False
    
    def verify_format(self, device_path: str, namespace_id: int, expected_lbaf: int) -> bool:
        """Verify the format was successful."""
        try:
            print(f"\n🔍 Verifying format results...")
            
            namespace_info = get_namespace_info(device_path, namespace_id)
            current_lbaf = namespace_info.get('flbas', {}).get('format', -1)
            
            print(f"Expected LBA Format: {expected_lbaf}")
            print(f"Current LBA Format: {current_lbaf}")
            
            if current_lbaf == expected_lbaf:
                print("✅ Format verification successful!")
                return True
            else:
                print(f"⚠️  Format verification failed!")
                print(f"Expected LBAF {expected_lbaf}, but device shows LBAF {current_lbaf}")
                return False
                
        except Exception as e:
            print(f"❌ Format verification error: {e}")
            return False
    
    def run(self):
        """Run the interactive formatting tool."""
        print("🚀 Interactive NVMe SSD Formatting Tool")
        print("="*60)
        
        if not self.check_prerequisites():
            return 1
        
        self.selected_device = self.list_and_select_device()
        if not self.selected_device:
            print("👋 Goodbye!")
            return 0
        
        device_path = self.selected_device['device_path']
        
        self.selected_namespace = self.select_namespace(device_path)
        if not self.selected_namespace:
            print("👋 Goodbye!")
            return 0
        
        self.selected_lbaf = self.select_lba_format(device_path, self.selected_namespace)
        if self.selected_lbaf is None:
            print("👋 Goodbye!")
            return 0
        
        if not self.confirm_format(device_path, self.selected_namespace, self.selected_lbaf):
            print("👋 Format cancelled. Your data is safe!")
            return 0
        
        if not self.perform_format(device_path, self.selected_namespace, self.selected_lbaf):
            return 1
        
        if not self.monitor_format_progress(device_path):
            print("⚠️  Format monitoring timed out")
            print("Check device status manually with: nvme smart-log " + device_path)
            return 1
        
        if not self.verify_format(device_path, self.selected_namespace, self.selected_lbaf):
            print("⚠️  Format verification failed")
            return 1
        
        print("\n🎉 Format operation completed successfully!")
        print(f"Device {device_path}n{self.selected_namespace} has been formatted with LBAF {self.selected_lbaf}")
        print("\n📝 Next steps:")
        print("1. Create new partitions if needed")
        print("2. Format with a filesystem (ext4, NTFS, etc.)")
        print("3. Mount and use the device")
        
        return 0


def main():
    """Main entry point."""
    try:
        formatter = NVMeFormatter()
        return formatter.run()
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled by user")
        return 0
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
