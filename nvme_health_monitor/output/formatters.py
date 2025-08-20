"""
Output formatting functions for NVMe health data.

This module provides functions to format health snapshots and device data
into various output formats including JSON, CSV, and human-readable text.
"""

import json
import csv
from io import StringIO
from typing import List, Dict, Any
from datetime import datetime

from ..models.health_metrics import HealthSnapshot, SystemHealthSummary


def format_health_snapshot_json(snapshot: HealthSnapshot, pretty: bool = True) -> str:
    """
    Format health snapshot as JSON string.
    
    Args:
        snapshot: Health snapshot to format
        pretty: Whether to use pretty printing
        
    Returns:
        JSON string representation
    """
    try:
        if pretty:
            return snapshot.model_dump_json(indent=2, exclude_none=True)
        else:
            return snapshot.model_dump_json(exclude_none=True)
    except Exception as e:
        return json.dumps({"error": f"Failed to format snapshot: {str(e)}"}, indent=2 if pretty else None)


def format_multiple_snapshots_json(snapshots: List[HealthSnapshot]) -> str:
    """
    Format multiple health snapshots as JSON array.
    
    Args:
        snapshots: List of health snapshots
        
    Returns:
        JSON array string
    """
    try:
        collection_time = datetime.utcnow().isoformat()
        device_count = len(snapshots)
        
        result = {
            "metadata": {
                "collection_time": collection_time,
                "device_count": device_count,
                "format_version": "1.0"
            },
            "devices": [snapshot.model_dump(exclude_none=True) for snapshot in snapshots]
        }
        
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": f"Failed to format snapshots: {str(e)}"}, indent=2)


def format_smart_data_csv(snapshots: List[HealthSnapshot]) -> str:
    """
    Format SMART data from multiple snapshots as CSV.
    
    Args:
        snapshots: List of health snapshots
        
    Returns:
        CSV string with SMART data
    """
    output = StringIO()
    writer = csv.writer(output)
    
    headers = [
        "device_path", "timestamp", "temperature_celsius", "available_spare_percent",
        "available_spare_threshold", "percentage_used", "data_units_read",
        "data_units_written", "host_read_commands", "host_write_commands",
        "controller_busy_time", "power_cycles", "power_on_hours",
        "unsafe_shutdowns", "media_errors", "error_info_log_entries",
        "critical_warning", "health_status"
    ]
    
    writer.writerow(headers)
    
    for snapshot in sorted(snapshots, key=lambda x: x.device_info.device_path):
        if snapshot.smart_data:
            smart = snapshot.smart_data
            row = [
                snapshot.device_info.device_path,
                snapshot.timestamp.isoformat(),
                smart.temperature.celsius if smart.temperature else "",
                smart.available_spare or "",
                smart.available_spare_threshold or "",
                smart.percentage_used or "",
                smart.data_units_read or "",
                smart.data_units_written or "",
                smart.host_read_commands or "",
                smart.host_write_commands or "",
                smart.controller_busy_time or "",
                smart.power_cycles or "",
                smart.power_on_hours or "",
                smart.unsafe_shutdowns or "",
                smart.media_errors or "",
                smart.error_log_entries or "",
                smart.critical_warning or "",
                smart.health_status.value if smart.health_status else ""
            ]
            writer.writerow(row)
    
    return output.getvalue()


def format_error_summary_csv(snapshots: List[HealthSnapshot]) -> str:
    """
    Format error summary data as CSV.
    
    Args:
        snapshots: List of health snapshots
        
    Returns:
        CSV string with error summary
    """
    output = StringIO()
    writer = csv.writer(output)
    
    headers = [
        "device_path", "timestamp", "total_errors", "media_errors",
        "data_integrity_errors", "read_errors", "write_errors",
        "recent_error_count", "critical_errors"
    ]
    
    writer.writerow(headers)
    
    for snapshot in sorted(snapshots, key=lambda x: x.device_info.device_path):
        error_logs = snapshot.error_logs or []
        total_errors = len(error_logs)
        
        media_errors = sum(1 for log in error_logs if "media" in log.error_type.lower())
        data_integrity_errors = sum(1 for log in error_logs if "integrity" in log.error_type.lower())
        read_errors = sum(1 for log in error_logs if "read" in log.error_type.lower())
        write_errors = sum(1 for log in error_logs if "write" in log.error_type.lower())
        
        recent_errors = sum(1 for log in error_logs if log.timestamp and 
                          (datetime.utcnow() - log.timestamp).days <= 7)
        
        critical_errors = sum(1 for log in error_logs if log.severity == "critical")
        
        row = [
            snapshot.device_info.device_path,
            snapshot.timestamp.isoformat(),
            total_errors,
            media_errors,
            data_integrity_errors,
            read_errors,
            write_errors,
            recent_errors,
            critical_errors
        ]
        writer.writerow(row)
    
    return output.getvalue()


def format_health_summary_text(snapshot: HealthSnapshot) -> str:
    """
    Format health snapshot as human-readable text summary.
    
    Args:
        snapshot: Health snapshot to format
        
    Returns:
        Formatted text summary
    """
    lines = []
    device = snapshot.device_info
    smart = snapshot.smart_data
    
    lines.append("=" * 60)
    lines.append(f"NVMe Device Health Summary")
    lines.append("=" * 60)
    lines.append(f"Device Path:     {device.device_path}")
    lines.append(f"Model:           {device.controller_info.model_number}")
    lines.append(f"Serial Number:   {device.controller_info.serial_number}")
    lines.append(f"Firmware:        {device.controller_info.firmware_revision}")
    lines.append(f"Capacity:        {device.controller_info.total_nvm_capacity / (1024**3):.1f} GB")
    lines.append(f"Collection Time: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")
    
    if smart:
        lines.append("SMART Health Status")
        lines.append("-" * 30)
        lines.append(f"Overall Status:       {smart.health_status.value.upper()}")
        lines.append(f"Temperature:          {smart.temperature.celsius}°C")
        lines.append(f"Available Spare:      {smart.available_spare}%")
        lines.append(f"Percentage Used:      {smart.percentage_used}%")
        lines.append(f"Power On Hours:       {smart.power_on_hours:,}")
        lines.append(f"Power Cycles:         {smart.power_cycles:,}")
        lines.append(f"Unsafe Shutdowns:     {smart.unsafe_shutdowns:,}")
        lines.append(f"Media Errors:         {smart.media_errors:,}")
        lines.append("")
        
        if smart.critical_warning and smart.critical_warning > 0:
            lines.append("⚠️  CRITICAL WARNINGS DETECTED")
            lines.append(f"Critical Warning Code: {smart.critical_warning}")
            lines.append("")
    
    error_logs = snapshot.error_logs or []
    if error_logs:
        lines.append(f"Error Log Summary ({len(error_logs)} entries)")
        lines.append("-" * 30)
        recent_errors = [log for log in error_logs if log.timestamp and 
                        (datetime.utcnow() - log.timestamp).days <= 7]
        lines.append(f"Recent Errors (7 days): {len(recent_errors)}")
        lines.append(f"Total Error Entries:    {len(error_logs)}")
        lines.append("")
    
    self_test = snapshot.self_test_log
    if self_test and self_test.entries:
        latest_test = self_test.entries[0]
        lines.append("Latest Self-Test")
        lines.append("-" * 20)
        lines.append(f"Test Type:   {latest_test.test_type.value}")
        lines.append(f"Result:      {latest_test.test_result.value}")
        if latest_test.timestamp:
            lines.append(f"Completed:   {latest_test.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)


def format_device_comparison_table(snapshots: List[HealthSnapshot]) -> str:
    """
    Format multiple devices as comparison table.
    
    Args:
        snapshots: List of health snapshots
        
    Returns:
        Formatted comparison table
    """
    if not snapshots:
        return "No devices found."
    
    lines = []
    lines.append("NVMe Device Health Comparison")
    lines.append("=" * 120)
    
    header = f"{'Device':<20} {'Model':<25} {'Health':<10} {'Temp':<6} {'Spare':<6} {'Used':<6} {'Errors':<8} {'Hours':<10}"
    lines.append(header)
    lines.append("-" * 120)
    
    sorted_snapshots = sorted(snapshots, key=lambda x: (
        x.smart_data.health_status.value if x.smart_data else "unknown",
        x.device_info.device_path
    ))
    
    for snapshot in sorted_snapshots:
        device = snapshot.device_info
        smart = snapshot.smart_data
        
        device_path = device.device_path[-18:] if len(device.device_path) > 18 else device.device_path
        model = device.controller_info.model_number[:23] if len(device.controller_info.model_number) > 23 else device.controller_info.model_number
        
        if smart:
            health = smart.health_status.value.upper()
            temp = f"{smart.temperature.celsius}°C" if smart.temperature else "N/A"
            spare = f"{smart.available_spare}%" if smart.available_spare else "N/A"
            used = f"{smart.percentage_used}%" if smart.percentage_used else "N/A"
            hours = f"{smart.power_on_hours:,}" if smart.power_on_hours else "N/A"
        else:
            health = "UNKNOWN"
            temp = spare = used = hours = "N/A"
        
        error_count = len(snapshot.error_logs) if snapshot.error_logs else 0
        
        status_indicator = "🔴" if health == "CRITICAL" else "🟡" if health == "WARNING" else "🟢"
        
        row = f"{device_path:<20} {model:<25} {status_indicator} {health:<8} {temp:<6} {spare:<6} {used:<6} {error_count:<8} {hours:<10}"
        lines.append(row)
    
    lines.append("-" * 120)
    lines.append(f"Total Devices: {len(snapshots)}")
    
    healthy_count = sum(1 for s in snapshots if s.smart_data and s.smart_data.health_status.value == "good")
    warning_count = sum(1 for s in snapshots if s.smart_data and s.smart_data.health_status.value == "warning")
    critical_count = sum(1 for s in snapshots if s.smart_data and s.smart_data.health_status.value == "critical")
    
    lines.append(f"🟢 Healthy: {healthy_count}  🟡 Warning: {warning_count}  🔴 Critical: {critical_count}")
    lines.append("")
    
    return "\n".join(lines)
