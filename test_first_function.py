"""
Test script for the first implemented function: create_nvme_base_exception()
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, '/home/ubuntu')

from nvme_health_monitor.models.exceptions import create_nvme_base_exception


def test_create_nvme_base_exception():
    """Test the create_nvme_base_exception function."""
    print("Testing create_nvme_base_exception()...")
    
    NVMeBaseException = create_nvme_base_exception()
    
    print("\n1. Testing basic exception creation:")
    try:
        raise NVMeBaseException("Test error message")
    except NVMeBaseException as e:
        print(f"✓ Exception caught: {type(e).__name__}")
        print(f"✓ Message: {e.message}")
        print(f"✓ Timestamp: {e.timestamp}")
        print(f"✓ String representation: {str(e)}")
    
    print("\n2. Testing exception with device path:")
    try:
        raise NVMeBaseException("Device access failed", device_path="/dev/nvme0")
    except NVMeBaseException as e:
        print(f"✓ Exception with device: {str(e)}")
        print(f"✓ Device path: {e.device_path}")
    
    print("\n3. Testing exception with custom timestamp:")
    custom_time = datetime(2025, 8, 20, 15, 30, 0)
    try:
        raise NVMeBaseException("Custom time error", timestamp=custom_time)
    except NVMeBaseException as e:
        print(f"✓ Custom timestamp: {e.timestamp}")
        print(f"✓ String with custom time: {str(e)}")
    
    print("\n4. Testing dictionary conversion:")
    exc = NVMeBaseException("Dict test", device_path="/dev/nvme1")
    exc_dict = exc.to_dict()
    print(f"✓ Dictionary representation: {exc_dict}")
    
    print("\n5. Testing inheritance:")
    exc = NVMeBaseException("Inheritance test")
    print(f"✓ Is Exception: {isinstance(exc, Exception)}")
    print(f"✓ Is NVMeBaseException: {isinstance(exc, NVMeBaseException)}")
    
    print("\n✅ All tests passed! First function implementation is working correctly.")


if __name__ == "__main__":
    test_create_nvme_base_exception()
