"""
NVMe Health Monitor - Exception Classes

This module contains all custom exception classes for NVMe operations.
Each exception provides specific context for different types of failures.
"""

from datetime import datetime
from typing import Optional


class NVMeBaseException(Exception):
    """
    Base exception class for all NVMe operations.
    
    Provides common attributes and functionality for all NVMe-related exceptions.
    """
    
    def __init__(
        self, 
        message: str, 
        device_path: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize base NVMe exception.
        
        Args:
            message: Error message describing the issue
            device_path: Optional NVMe device path where error occurred
            timestamp: Optional timestamp when error occurred (defaults to now)
        """
        super().__init__(message)
        self.message = message
        self.device_path = device_path
        self.timestamp = timestamp or datetime.now()
    
    def __str__(self) -> str:
        """
        Return formatted error message with context.
        
        Returns:
            Formatted error message including device path and timestamp
        """
        parts = [self.message]
        
        if self.device_path:
            parts.append(f"Device: {self.device_path}")
        
        parts.append(f"Time: {self.timestamp.isoformat()}")
        
        return " | ".join(parts)
    
    def to_dict(self) -> dict:
        """
        Convert exception to dictionary for logging/serialization.
        
        Returns:
            Dictionary representation of the exception
        """
        return {
            "exception_type": self.__class__.__name__,
            "message": self.message,
            "device_path": self.device_path,
            "timestamp": self.timestamp.isoformat()
        }


class NVMeCommandError(NVMeBaseException):
    """Exception for nvme-cli command execution failures."""
    
    def __init__(
        self,
        message: str,
        command: Optional[list] = None,
        return_code: Optional[int] = None,
        stderr_output: Optional[str] = None,
        device_path: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        super().__init__(message, device_path, timestamp)
        self.command = command or []
        self.return_code = return_code
        self.stderr_output = stderr_output
    
    def __str__(self) -> str:
        parts = [self.message]
        
        if self.command:
            parts.append(f"Command: {' '.join(self.command)}")
        
        if self.return_code is not None:
            parts.append(f"Return code: {self.return_code}")
        
        if self.stderr_output:
            parts.append(f"Error: {self.stderr_output}")
        
        if self.device_path:
            parts.append(f"Device: {self.device_path}")
        
        parts.append(f"Time: {self.timestamp.isoformat()}")
        
        return " | ".join(parts)


class NVMeDeviceNotFoundError(NVMeBaseException):
    """Exception for device not found errors."""
    
    def __init__(
        self,
        message: str,
        device_path: Optional[str] = None,
        available_devices: Optional[list] = None,
        timestamp: Optional[datetime] = None
    ):
        super().__init__(message, device_path, timestamp)
        self.available_devices = available_devices or []


class NVMePermissionError(NVMeBaseException):
    """Exception for permission denied errors."""
    
    def __init__(
        self,
        message: str,
        device_path: Optional[str] = None,
        required_permissions: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        super().__init__(message, device_path, timestamp)
        self.required_permissions = required_permissions


class NVMeTimeoutError(NVMeBaseException):
    """Exception for command timeout errors."""
    
    def __init__(
        self,
        message: str,
        timeout_duration: Optional[int] = None,
        device_path: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        super().__init__(message, device_path, timestamp)
        self.timeout_duration = timeout_duration


NVMeError = NVMeBaseException


def create_nvme_base_exception() -> type:
    """
    Create base exception class for NVMe operations.
    
    Returns:
        type: Base exception class
        
    Implementation Notes:
        - Inherit from Exception
        - Add device_path attribute
        - Add timestamp attribute
        - Override __str__ method for better error messages
    """
    return NVMeBaseException


def create_nvme_command_error() -> type:
    """
    Create exception for nvme-cli command execution failures.
    
    Returns:
        type: Command error exception class
        
    Implementation Notes:
        - Inherit from NVMeBaseException
        - Add command attribute to store failed command
        - Add return_code attribute
        - Add stderr_output attribute
    """
    return NVMeCommandError


def create_nvme_device_not_found_error() -> type:
    """
    Create exception for device not found errors.
    
    Returns:
        type: Device not found exception class
        
    Implementation Notes:
        - Inherit from NVMeBaseException
        - Add available_devices attribute
    """
    return NVMeDeviceNotFoundError


def create_nvme_permission_error() -> type:
    """
    Create exception for permission denied errors.
    
    Returns:
        type: Permission error exception class
        
    Implementation Notes:
        - Inherit from NVMeBaseException
        - Add required_permissions attribute
    """
    return NVMePermissionError


def create_nvme_timeout_error() -> type:
    """
    Create exception for command timeout errors.
    
    Returns:
        type: Timeout error exception class
        
    Implementation Notes:
        - Inherit from NVMeBaseException
        - Add timeout_duration attribute
    """
    return NVMeTimeoutError
