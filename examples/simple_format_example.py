#!/usr/bin/env python3
"""
Simple NVMe Format Example

This script demonstrates the basic pattern for formatting an NVMe SSD:
1. Check device availability
2. Get namespace information
3. Format with specified LBAF
4. Wait for completion
5. Verify results

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
    """Example function showing how to format an NVMe device."""
    
    DEVICE_PATH = "/dev/nvme0"  # Target device
    NAMESPACE_ID = 1            # Target namespace
    TARGET_LBAF = 0            # Target LBA format (usually 0 = 512 bytes)
    SECURE_ERASE = "user"      # Secure erase level
    TIMEOUT_MINUTES = 30       # Maximum wait time
    
    print("🚀 Simple NVMe Format Example")
    print("="*50)
    
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
    
    
    print(f"\n4️⃣  Monitoring format progress...")
    print("⚠️  Format monitoring is commented out for safety")
    
    # 
    #         
    #         
    #         
    #         
    #         
    
    print(f"\n5️⃣  Verifying format results...")
    print("⚠️  Verification is commented out for safety")
    
    #     
    #     
    #         
    
    print("\n🎉 Example completed successfully!")
    print("\n📝 To actually format a device:")
    print("1. Uncomment the format, monitoring, and verification sections")
    print("2. Update the DEVICE_PATH, NAMESPACE_ID, and TARGET_LBAF variables")
    print("3. Ensure you have proper backups")
    print("4. Run with appropriate permissions (sudo)")
    
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
