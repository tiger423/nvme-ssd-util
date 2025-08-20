#!/usr/bin/env python3
"""
Simple NVMe Format Example - Basic Programming Pattern

This script demonstrates the essential programming pattern for NVMe formatting:

BASIC WORKFLOW:
┌─────────────────────────────────────────────────────────────────┐
│ Prerequisites → Namespace Info → Format → Monitor → Verify     │
└─────────────────────────────────────────────────────────────────┘

CORE PATTERN:
1. check_nvme_cli_availability() - Ensure nvme-cli is available
2. get_namespace_info() - Get current format and available options
3. format_namespace() - Execute format with specified LBAF
4. get_format_status() - Monitor progress until completion
5. get_namespace_info() - Verify format was applied correctly

INTEGRATION EXAMPLE:
This pattern can be integrated into larger applications by:
- Wrapping in try/catch blocks for error handling
- Adding user confirmation prompts for safety
- Implementing progress callbacks for UI updates
- Adding logging for audit trails

For production use, see:
- nvme_format_interactive.py (full interactive tool)
- docs/FUNCTION_REFERENCE.md (detailed API documentation)

This is a simplified example for educational purposes.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nvme_health_monitor.core.nvme_interface import (
    check_nvme_cli_availability,
    get_namespace_info,
    format_namespace,
    get_format_status
)


def format_nvme_device_example():
    """
    Example function demonstrating the basic NVMe format pattern.
    
    This function shows the minimal code required to format an NVMe device
    with LBAF support and progress monitoring. It's designed as a template
    that developers can adapt for their specific needs.
    
    CONFIGURATION PARAMETERS:
    - DEVICE_PATH: Target NVMe device (e.g., "/dev/nvme0")
    - NAMESPACE_ID: Target namespace (typically 1 for single-namespace drives)
    - TARGET_LBAF: Desired LBA format index (0=512B, 1=4096B typically)
    - SECURE_ERASE: Data erasure level ("none", "user", "crypto")
    - TIMEOUT_MINUTES: Maximum time to wait for completion
    
    RETURN VALUE:
    Returns True if the example runs successfully (format is commented out),
    False if any errors occur during the demonstration.
    """
    
    DEVICE_PATH = "/dev/nvme0"  # Target device path
    NAMESPACE_ID = 1            # Target namespace (usually 1)
    TARGET_LBAF = 0            # Target LBA format (0=512B, 1=4096B typically)
    SECURE_ERASE = "user"      # Secure erase level (none/user/crypto)
    TIMEOUT_MINUTES = 30       # Maximum wait time for completion
    
    print("🚀 Simple NVMe Format Example - Basic Programming Pattern")
    print("="*65)
    
    print("1️⃣  Checking nvme-cli availability...")
    if not check_nvme_cli_availability():
        print("❌ nvme-cli not available")
        return False
    print("✅ nvme-cli is available")
    
    print(f"\n2️⃣  Getting namespace info for {DEVICE_PATH}n{NAMESPACE_ID}...")
    try:
        ns_info = get_namespace_info(DEVICE_PATH, NAMESPACE_ID)
        print(f"✅ Namespace info retrieved")
        
        current_lbaf = ns_info.get('flbas', {}).get('format', 'Unknown')
        print(f"📊 Current LBA Format: {current_lbaf}")
        
        if 'lbaf' in ns_info:
            print("📋 Available LBA Formats:")
            for i, lbaf in enumerate(ns_info['lbaf']):
                if isinstance(lbaf, dict) and lbaf.get('ds', 0) > 0:
                    data_size = lbaf.get('ds', 0)
                    print(f"   LBAF {i}: {data_size} bytes per block")
        
    except Exception as e:
        print(f"❌ Failed to get namespace info: {e}")
        return False
    
    print(f"\n3️⃣  Formatting {DEVICE_PATH}n{NAMESPACE_ID} with LBAF {TARGET_LBAF}...")
    print("⚠️  WARNING: This would destroy all data!")
    print("⚠️  For safety, format is commented out in this example")
    print("\n📝 ACTUAL FORMAT CODE (commented for safety):")
    print("=" * 50)
    print("# Step 3a: Execute format command")
    print(f"# success = format_namespace('{DEVICE_PATH}', {NAMESPACE_ID}, {TARGET_LBAF}, '{SECURE_ERASE}')")
    print("# if not success:")
    print("#     print('❌ Format command failed')")
    print("#     return False")
    print("# print('✅ Format command issued successfully')")
    
    print(f"\n4️⃣  Monitoring format progress...")
    print("⚠️  Format monitoring is commented out for safety")
    print("\n📝 PROGRESS MONITORING CODE (commented for safety):")
    print("=" * 50)
    print("# Step 4a: Monitor progress with timeout")
    print("# import time")
    print("# start_time = time.time()")
    print(f"# timeout_seconds = {TIMEOUT_MINUTES} * 60")
    print("# ")
    print("# while True:")
    print(f"#     status = get_format_status('{DEVICE_PATH}')")
    print("#     ")
    print("#     if not status['is_formatting']:")
    print("#         print('✅ Format completed!')")
    print("#         break")
    print("#     ")
    print("#     progress = status['progress_percent']")
    print("#     elapsed = (time.time() - start_time) / 60")
    print("#     print(f'📊 Progress: {progress}% (elapsed: {elapsed:.1f} min)')")
    print("#     ")
    print("#     if time.time() - start_time > timeout_seconds:")
    print(f"#         print('⏰ Timeout after {TIMEOUT_MINUTES} minutes')")
    print("#         return False")
    print("#     ")
    print("#     time.sleep(5)  # Check every 5 seconds")
    
    print(f"\n5️⃣  Verifying format results...")
    print("⚠️  Verification is commented out for safety")
    print("\n📝 VERIFICATION CODE (commented for safety):")
    print("=" * 50)
    print("# Step 5a: Get updated namespace information")
    print(f"# final_info = get_namespace_info('{DEVICE_PATH}', {NAMESPACE_ID})")
    print("# final_lbaf = final_info.get('flbas', {}).get('format', -1)")
    print("# ")
    print("# Step 5b: Compare expected vs actual format")
    print(f"# if final_lbaf == {TARGET_LBAF}:")
    print("#     print('✅ Format verification successful!')")
    print(f"#     print(f'Device is now using LBAF {TARGET_LBAF}')")
    print("#     return True")
    print("# else:")
    print("#     print('❌ Format verification failed!')")
    print(f"#     print(f'Expected LBAF {TARGET_LBAF}, got {{final_lbaf}}')")
    print("#     return False")
    
    print("\n🎉 Example completed successfully!")
    print("\n📋 COMPLETE INTEGRATION PATTERN:")
    print("=" * 50)
    print("def production_format_function(device_path, namespace_id, target_lbaf):")
    print("    # 1. Prerequisites")
    print("    if not check_nvme_cli_availability():")
    print("        raise RuntimeError('nvme-cli not available')")
    print("    ")
    print("    # 2. Get current state")
    print("    ns_info = get_namespace_info(device_path, namespace_id)")
    print("    ")
    print("    # 3. Execute format")
    print("    success = format_namespace(device_path, namespace_id, target_lbaf, 'user')")
    print("    if not success:")
    print("        raise RuntimeError('Format failed to start')")
    print("    ")
    print("    # 4. Monitor progress")
    print("    while True:")
    print("        status = get_format_status(device_path)")
    print("        if not status['is_formatting']:")
    print("            break")
    print("        time.sleep(5)")
    print("    ")
    print("    # 5. Verify result")
    print("    final_info = get_namespace_info(device_path, namespace_id)")
    print("    final_lbaf = final_info.get('flbas', {}).get('format', -1)")
    print("    return final_lbaf == target_lbaf")
    
    print("\n📝 TO ACTUALLY FORMAT A DEVICE:")
    print("1. Copy the integration pattern above")
    print("2. Add proper error handling (try/catch blocks)")
    print("3. Add user confirmation prompts for safety")
    print("4. Update device path and parameters")
    print("5. Ensure you have proper backups")
    print("6. Run with appropriate permissions (sudo)")
    
    print("\n🔗 RELATED RESOURCES:")
    print("- Interactive tool: examples/nvme_format_interactive.py")
    print("- Complete example: examples/nvme_format_example.py")
    print("- Technical docs: docs/NVME_FORMAT_CODE_FLOW.md")
    print("- Function reference: docs/FUNCTION_REFERENCE.md")
    
    return True


def main():
    """Main entry point."""
    try:
        success = format_nvme_device_example()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
