#!/usr/bin/env python3
"""
NVMe SSD Formatting Example with LBAF Support

This example demonstrates the complete workflow for formatting NVMe SSDs:

WORKFLOW OVERVIEW:
┌─────────────────────────────────────────────────────────────────┐
│ 1. Prerequisites Check → 2. Device Discovery → 3. Namespace    │
│    Selection → 4. LBA Format Analysis → 5. Format Execution    │
│    → 6. Progress Monitoring → 7. Verification                  │
└─────────────────────────────────────────────────────────────────┘

DETAILED STEPS:
1. Check nvme-cli availability using check_nvme_cli_availability()
2. List available NVMe devices using list_nvme_devices()
3. Select target device and get namespaces using get_device_namespaces()
4. Analyze supported LBA formats using get_namespace_info()
5. Execute format operation using format_namespace()
6. Monitor progress until completion using get_format_status()
7. Verify format was applied correctly

CORE FUNCTIONS DEMONSTRATED:
- get_namespace_info(): Retrieve namespace details and LBA formats
- format_namespace(): Execute format with specified LBAF and secure erase
- get_format_status(): Monitor format progress and completion
- wait_for_format_completion(): Helper for progress monitoring

⚠️  WARNING: This will DESTROY ALL DATA on the selected namespace!
Only run this on test devices or devices you want to completely erase.

For detailed technical documentation, see:
../docs/NVME_FORMAT_CODE_FLOW.md
../docs/FUNCTION_REFERENCE.md
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
    """
    Display available LBA formats for a namespace.
    
    This function parses the LBA format array from namespace information
    and presents it in a user-friendly table format.
    
    LBA Format Structure:
    - ds (Data Size): Sector size in bytes (512, 4096, etc.)
    - ms (Metadata Size): Additional metadata bytes per sector
    - rp (Relative Performance): 0=Best, 1=Better, 2=Good, 3=Degraded
    
    Args:
        namespace_info: Dictionary from get_namespace_info() containing 'lbaf' array
    
    Technical Note:
    The 'lbaf' array contains up to 16 LBA format descriptors (LBAF 0-15).
    Each descriptor defines a different sector size and metadata configuration.
    Most drives support LBAF 0 (512B) and LBAF 1 (4096B) as standard formats.
    """
    print("\n" + "="*60)
    print("SUPPORTED LBA FORMATS")
    print("="*60)
    
    if 'lbaf' in namespace_info:
        lba_formats = namespace_info['lbaf']
        current_lbaf = namespace_info.get('flbas', {}).get('format', 0)
        
        print(f"{'Index':<6} {'Data Size':<12} {'Metadata':<10} {'Performance':<12} {'Current':<8}")
        print("-" * 58)
        
        for i, lbaf in enumerate(lba_formats):
            if isinstance(lbaf, dict) and lbaf.get('ds', 0) > 0:  # Only show valid formats
                data_size = lbaf.get('ds', 0)
                metadata_size = lbaf.get('ms', 0)
                relative_perf = lbaf.get('rp', 0)
                
                perf_desc = {0: "Best", 1: "Better", 2: "Good", 3: "Degraded"}.get(relative_perf, "Unknown")
                current_marker = "✓" if i == current_lbaf else ""
                
                print(f"{i:<6} {data_size:<12} {metadata_size:<10} {perf_desc:<12} {current_marker:<8}")
    else:
        print("No LBA format information available")
    
    print("="*60)
    print("Note: Data Size is the logical block size. 512B is traditional, 4096B is advanced format.")


def wait_for_format_completion(device_path: str, timeout_minutes: int = 30) -> bool:
    """
    Monitor format operation progress until completion.
    
    This function implements a polling loop that checks format status using
    the get_format_status() function. It monitors the 'format_progress_indicator'
    field from the NVMe SMART log to track progress.
    
    MONITORING ALGORITHM:
    1. Poll get_format_status() every 5 seconds
    2. Check 'is_formatting' flag and 'progress_percent' value
    3. Display progress updates when percentage changes
    4. Handle errors with exponential backoff (10 second delay)
    5. Timeout after specified minutes to prevent infinite loops
    
    PROGRESS DETECTION:
    - Uses NVMe SMART log 'format_progress_indicator' field
    - Progress ranges from 0% (started) to 100% (completed)
    - Some drives may not support progress reporting (always shows 100%)
    - Missing progress indicator means format is complete
    
    Args:
        device_path: NVMe device path (e.g., "/dev/nvme0")
        timeout_minutes: Maximum time to wait in minutes (default: 30)
        
    Returns:
        bool: True if format completed successfully, False if timeout occurred
        
    Technical Notes:
    - Format time varies by drive size, type, and secure erase level
    - Enterprise drives may take longer than consumer drives
    - Secure erase operations significantly increase format time
    - Network/USB-connected drives may have slower progress reporting
    """
    print(f"\n🔄 Monitoring format progress for {device_path}...")
    print("This may take several minutes depending on the drive size and secure erase level.")
    print("Progress reporting depends on drive support - some drives may not show incremental progress.")
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    last_progress = -1
    error_count = 0
    max_errors = 10
    
    while True:
        try:
            status = get_format_status(device_path)
            error_count = 0  # Reset error counter on successful status check
            
            if not status['is_formatting']:
                elapsed_min = (time.time() - start_time) / 60
                print(f"\n✅ Format completed successfully! (Total time: {elapsed_min:.1f} minutes)")
                return True
            
            progress = status['progress_percent']
            elapsed_min = (time.time() - start_time) / 60
            
            if progress != last_progress:
                print(f"📊 Format progress: {progress}% (elapsed: {elapsed_min:.1f} min)")
                last_progress = progress
            else:
                print(".", end="", flush=True)
            
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                print(f"\n⏰ Format timeout after {timeout_minutes} minutes")
                print("The format operation may still be in progress.")
                print("Check device status manually with: nvme smart-log " + device_path)
                return False
            
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            error_count += 1
            print(f"\n⚠️  Error checking format status ({error_count}/{max_errors}): {e}")
            
            if error_count >= max_errors:
                print("Too many consecutive errors, giving up on progress monitoring")
                return False
            
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
        
        print("\n🔧 FORMAT EXECUTION (COMMENTED FOR SAFETY)")
        print("The following code demonstrates the complete format workflow:")
        print("=" * 60)
        
        print("# Step 1: Execute format command")
        print(f"# success = format_namespace('{device_path}', {namespace_id}, {selected_lbaf}, secure_erase='user')")
        print("# if success:")
        print("#     print('Format started successfully')")
        print()
        print("# Step 2: Monitor progress until completion")
        print(f"# completed = wait_for_format_completion('{device_path}', timeout_minutes=30)")
        print("# if completed:")
        print("#     print('Format completed successfully!')")
        print()
        print("# Step 3: Verify format was applied")
        print(f"# final_info = get_namespace_info('{device_path}', {namespace_id})")
        print("# final_lbaf = final_info.get('flbas', {}).get('format', -1)")
        print(f"# if final_lbaf == {selected_lbaf}:")
        print("#     print('Format verification successful!')")
        print("# else:")
        print("#     print('Format verification failed!')")
        
        print("\n📝 Example completed successfully!")
        print("\n🚀 TO ACTUALLY FORMAT A DEVICE:")
        print("1. Uncomment the format execution code above")
        print("2. Update device path and parameters as needed")
        print("3. Ensure you have proper backups of important data")
        print("4. Run with appropriate permissions (sudo)")
        print("5. Use the interactive tool for safer operation:")
        print("   python examples/nvme_format_interactive.py")
        
        print("\n📚 For more information:")
        print("- Code flow documentation: docs/NVME_FORMAT_CODE_FLOW.md")
        print("- Function reference: docs/FUNCTION_REFERENCE.md")
        print("- Interactive tool: examples/nvme_format_interactive.py")
        
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
