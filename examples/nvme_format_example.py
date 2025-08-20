#!/usr/bin/env python3
"""
NVMe SSD Formatting Example with LBAF Support

This example demonstrates how to:
1. List available NVMe devices
2. Select a device and namespace
3. Check supported LBA formats
4. Format the namespace with a specific LBAF
5. Monitor the format progress until completion
6. Verify the format was successful

WARNING: This will DESTROY ALL DATA on the selected namespace!
Only run this on test devices or devices you want to completely erase.
"""

import sys
import time
from pathlib import Path

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
from nvme_health_monitor.output.formatters import format_device_comparison_table
from nvme_health_monitor.utils.logging_config import setup_logging


def display_lba_formats(namespace_info: dict) -> None:
    """Display available LBA formats for a namespace."""
    print("\n" + "="*60)
    print("SUPPORTED LBA FORMATS")
    print("="*60)
    
    if 'lbaf' in namespace_info:
        lba_formats = namespace_info['lbaf']
        print(f"{'Index':<6} {'Data Size':<12} {'Metadata':<10} {'Performance':<12}")
        print("-" * 50)
        
        for i, lbaf in enumerate(lba_formats):
            if isinstance(lbaf, dict):
                data_size = lbaf.get('ds', 0)
                metadata_size = lbaf.get('ms', 0)
                relative_perf = lbaf.get('rp', 0)
                
                perf_desc = {0: "Best", 1: "Better", 2: "Good", 3: "Degraded"}.get(relative_perf, "Unknown")
                
                print(f"{i:<6} {data_size:<12} {metadata_size:<10} {perf_desc:<12}")
    else:
        print("No LBA format information available")
    
    print("="*60)


def wait_for_format_completion(device_path: str, timeout_minutes: int = 30) -> bool:
    """
    Wait for format operation to complete.
    
    Args:
        device_path: NVMe device path
        timeout_minutes: Maximum time to wait in minutes
        
    Returns:
        bool: True if format completed successfully, False if timeout
    """
    print(f"\n🔄 Monitoring format progress for {device_path}...")
    print("This may take several minutes depending on the drive size.")
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    last_progress = -1
    
    while True:
        try:
            status = get_format_status(device_path)
            
            if not status['is_formatting']:
                print(f"\n✅ Format completed successfully!")
                return True
            
            progress = status['progress_percent']
            if progress != last_progress:
                print(f"📊 Format progress: {progress}%")
                last_progress = progress
            
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                print(f"\n⏰ Format timeout after {timeout_minutes} minutes")
                return False
            
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            print(f"⚠️  Error checking format status: {e}")
            time.sleep(10)  # Wait longer on error
            
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                return False


def main():
    """Main example function."""
    print("🚀 NVMe SSD Formatting Example with LBAF Support")
    print("="*60)
    
    logger = setup_logging("INFO")
    
    if not check_nvme_cli_availability():
        print("❌ Error: nvme-cli is not available. Please install nvme-cli first.")
        print("   Ubuntu/Debian: sudo apt install nvme-cli")
        print("   RHEL/CentOS: sudo yum install nvme-cli")
        return 1
    
    print("✅ nvme-cli is available")
    
    try:
        print("\n📋 Listing available NVMe devices...")
        devices = list_nvme_devices()
        
        if not devices:
            print("❌ No NVMe devices found on this system")
            return 1
        
        print(f"Found {len(devices)} NVMe device(s):")
        for i, device in enumerate(devices):
            print(f"  {i+1}. {device['device_path']} - {device['model']} ({device['serial_number']})")
        
        if len(devices) == 1:
            selected_device = devices[0]
            print(f"\n🎯 Using device: {selected_device['device_path']}")
        else:
            print(f"\n🎯 Using first device for example: {devices[0]['device_path']}")
            selected_device = devices[0]
        
        device_path = selected_device['device_path']
        
        print(f"\n📂 Getting namespaces for {device_path}...")
        namespaces = get_device_namespaces(device_path)
        
        if not namespaces:
            print("❌ No namespaces found for this device")
            return 1
        
        print(f"Found {len(namespaces)} namespace(s):")
        for ns in namespaces:
            size_gb = ns.get('size', 0) / (1024**3) if ns.get('size') else 0
            print(f"  Namespace {ns.get('nsid', 'Unknown')}: {size_gb:.1f} GB")
        
        namespace_id = namespaces[0].get('nsid', 1)
        print(f"\n🎯 Using namespace: {namespace_id}")
        
        print(f"\n🔍 Getting namespace information for {device_path}n{namespace_id}...")
        namespace_info = get_namespace_info(device_path, namespace_id)
        
        display_lba_formats(namespace_info)
        
        selected_lbaf = 0
        print(f"\n🎯 Selected LBA Format: {selected_lbaf}")
        
        print("\n" + "⚠️ " * 20)
        print("WARNING: FORMATTING WILL DESTROY ALL DATA!")
        print("This is an example script - in production, you should:")
        print("1. Prompt user for confirmation")
        print("2. Verify the correct device is selected")
        print("3. Backup any important data")
        print("⚠️ " * 20)
        
        
        # 
        #     
        #     
        #         
        #         
        
        print("\n📝 Example completed successfully!")
        print("To actually perform formatting, uncomment the format section in the code.")
        print("Remember to always backup your data before formatting!")
        
        return 0
        
    except NVMePermissionError as e:
        print(f"❌ Permission Error: {e}")
        print("Try running with sudo or ensure your user is in the nvme group")
        return 1
    except NVMeDeviceNotFoundError as e:
        print(f"❌ Device Error: {e}")
        return 1
    except NVMeCommandError as e:
        print(f"❌ Command Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
