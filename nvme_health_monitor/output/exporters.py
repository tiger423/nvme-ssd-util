"""
Export utilities for NVMe health monitoring data.

This module provides functions to export health data to various formats
and external systems for integration and analysis.
"""

import json
import csv
import xml.etree.ElementTree as ET
from io import StringIO
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ..models.health_metrics import HealthSnapshot, SystemHealthSummary


def export_to_json(data: Any, output_path: str, pretty: bool = True) -> None:
    """
    Export data to JSON file.
    
    Args:
        data: Data to export (HealthSnapshot, list, or dict)
        output_path: Output file path
        pretty: Whether to use pretty printing
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if hasattr(data, 'model_dump'):
        json_data = data.model_dump()
    elif isinstance(data, list) and data and hasattr(data[0], 'model_dump'):
        json_data = [item.model_dump() for item in data]
    else:
        json_data = data
    
    with open(output_file, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(json_data, f, indent=2, default=str, ensure_ascii=False)
        else:
            json.dump(json_data, f, default=str, ensure_ascii=False)


def export_to_csv(snapshots: List[HealthSnapshot], output_path: str, 
                  include_errors: bool = False) -> None:
    """
    Export health snapshots to CSV file.
    
    Args:
        snapshots: List of health snapshots to export
        output_path: Output file path
        include_errors: Whether to include error log data
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if include_errors:
        _export_error_data_csv(snapshots, output_file)
    else:
        _export_health_data_csv(snapshots, output_file)


def export_to_xml(snapshots: List[HealthSnapshot], output_path: str) -> None:
    """
    Export health snapshots to XML file.
    
    Args:
        snapshots: List of health snapshots to export
        output_path: Output file path
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    root = ET.Element("nvme_health_data")
    root.set("generated_at", datetime.utcnow().isoformat())
    root.set("device_count", str(len(snapshots)))
    
    for snapshot in snapshots:
        device_elem = ET.SubElement(root, "device")
        device_elem.set("path", snapshot.device_info.device_path)
        device_elem.set("timestamp", snapshot.timestamp.isoformat())
        
        device_info_elem = ET.SubElement(device_elem, "device_info")
        controller = snapshot.device_info.controller_info
        
        ET.SubElement(device_info_elem, "model").text = controller.model_name
        ET.SubElement(device_info_elem, "serial").text = controller.serial_number
        ET.SubElement(device_info_elem, "firmware").text = controller.firmware_revision
        ET.SubElement(device_info_elem, "capacity_gb").text = str(controller.total_capacity_gb)
        
        if snapshot.smart_data:
            smart_elem = ET.SubElement(device_elem, "smart_data")
            smart = snapshot.smart_data
            
            ET.SubElement(smart_elem, "health_status").text = smart.health_status.value
            ET.SubElement(smart_elem, "critical_warning").text = str(smart.critical_warning or 0)
            
            if smart.temperature:
                ET.SubElement(smart_elem, "temperature_celsius").text = str(smart.temperature.celsius)
            
            if smart.available_spare_percent is not None:
                ET.SubElement(smart_elem, "available_spare_percent").text = str(smart.available_spare_percent)
            
            if smart.percentage_used is not None:
                ET.SubElement(smart_elem, "percentage_used").text = str(smart.percentage_used)
            
            if smart.power_on_hours is not None:
                ET.SubElement(smart_elem, "power_on_hours").text = str(smart.power_on_hours)
            
            if smart.media_errors is not None:
                ET.SubElement(smart_elem, "media_errors").text = str(smart.media_errors)
        
        if snapshot.error_logs:
            errors_elem = ET.SubElement(device_elem, "error_logs")
            errors_elem.set("count", str(len(snapshot.error_logs)))
            
            for error in snapshot.error_logs[:10]:
                error_elem = ET.SubElement(errors_elem, "error")
                error_elem.set("count", str(error.error_count))
                error_elem.set("type", error.error_type)
                error_elem.set("severity", error.severity)
                if error.timestamp:
                    error_elem.set("timestamp", error.timestamp.isoformat())
    
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)


def export_to_yaml(data: Any, output_path: str) -> None:
    """
    Export data to YAML file.
    
    Args:
        data: Data to export
        output_path: Output file path
    """
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required for YAML export. Install with: pip install pyyaml")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if hasattr(data, 'model_dump'):
        yaml_data = data.model_dump()
    elif isinstance(data, list) and data and hasattr(data[0], 'model_dump'):
        yaml_data = [item.model_dump() for item in data]
    else:
        yaml_data = data
    
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def export_summary_report(snapshots: List[HealthSnapshot], output_path: str, 
                         format_type: str = "json") -> None:
    """
    Export summary report in specified format.
    
    Args:
        snapshots: List of health snapshots
        output_path: Output file path
        format_type: Export format ('json', 'csv', 'xml', 'yaml')
    """
    from .reporters import generate_system_health_summary, generate_health_report
    
    system_summary = generate_system_health_summary(snapshots)
    health_report = generate_health_report(snapshots, report_type="summary")
    
    export_data = {
        "system_summary": system_summary.model_dump(),
        "health_report": health_report
    }
    
    if format_type == "json":
        export_to_json(export_data, output_path)
    elif format_type == "yaml":
        export_to_yaml(export_data, output_path)
    elif format_type == "xml":
        _export_summary_xml(export_data, output_path)
    elif format_type == "csv":
        _export_summary_csv(snapshots, output_path)
    else:
        raise ValueError(f"Unsupported export format: {format_type}")


def export_for_monitoring_system(snapshots: List[HealthSnapshot], 
                                system_type: str, output_path: str) -> None:
    """
    Export data in format suitable for monitoring systems.
    
    Args:
        snapshots: List of health snapshots
        system_type: Monitoring system type ('prometheus', 'grafana', 'nagios')
        output_path: Output file path
    """
    if system_type == "prometheus":
        _export_prometheus_metrics(snapshots, output_path)
    elif system_type == "grafana":
        _export_grafana_json(snapshots, output_path)
    elif system_type == "nagios":
        _export_nagios_format(snapshots, output_path)
    else:
        raise ValueError(f"Unsupported monitoring system: {system_type}")


def _export_health_data_csv(snapshots: List[HealthSnapshot], output_file: Path) -> None:
    """Export health data to CSV format."""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        headers = [
            "device_path", "timestamp", "model", "serial", "capacity_gb",
            "health_status", "temperature_celsius", "available_spare_percent",
            "percentage_used", "power_on_hours", "power_cycles", "media_errors",
            "error_log_entries", "critical_warning"
        ]
        writer.writerow(headers)
        
        for snapshot in snapshots:
            device = snapshot.device_info
            smart = snapshot.smart_data
            
            row = [
                device.device_path,
                snapshot.timestamp.isoformat(),
                device.controller_info.model_number,
                device.controller_info.serial_number,
                device.total_capacity_gb
            ]
            
            if smart:
                row.extend([
                    smart.health_status.value,
                    smart.temperature.celsius if smart.temperature else "",
                    smart.available_spare or "",
                    smart.percentage_used or "",
                    smart.power_on_hours or "",
                    smart.power_cycles or "",
                    smart.media_errors or "",
                    smart.error_log_entries or "",
                    smart.critical_warning or ""
                ])
            else:
                row.extend([""] * 9)
            
            writer.writerow(row)


def _export_error_data_csv(snapshots: List[HealthSnapshot], output_file: Path) -> None:
    """Export error log data to CSV format."""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        headers = [
            "device_path", "error_count", "timestamp", "error_type", "severity",
            "sqid", "cmdid", "status_field", "lba", "nsid", "description"
        ]
        writer.writerow(headers)
        
        for snapshot in snapshots:
            device_path = snapshot.device_info.device_path
            
            if snapshot.error_logs:
                for error in snapshot.error_logs:
                    row = [
                        device_path,
                        error.error_count,
                        error.timestamp.isoformat() if error.timestamp else "",
                        error.error_type,
                        error.severity,
                        error.sqid or "",
                        error.cmdid or "",
                        error.status_field or "",
                        error.lba or "",
                        error.nsid or "",
                        error.description or ""
                    ]
                    writer.writerow(row)
            else:
                row = [device_path] + [""] * (len(headers) - 1)
                writer.writerow(row)


def _export_summary_xml(export_data: Dict[str, Any], output_path: str) -> None:
    """Export summary data to XML format."""
    root = ET.Element("nvme_health_summary")
    root.set("generated_at", datetime.utcnow().isoformat())
    
    system_summary = export_data["system_summary"]
    summary_elem = ET.SubElement(root, "system_summary")
    
    for key, value in system_summary.items():
        elem = ET.SubElement(summary_elem, key)
        elem.text = str(value)
    
    health_report = export_data["health_report"]
    report_elem = ET.SubElement(root, "health_report")
    
    if "executive_summary" in health_report:
        exec_elem = ET.SubElement(report_elem, "executive_summary")
        for key, value in health_report["executive_summary"].items():
            if isinstance(value, dict):
                sub_elem = ET.SubElement(exec_elem, key)
                for sub_key, sub_value in value.items():
                    ET.SubElement(sub_elem, sub_key).text = str(sub_value)
            else:
                ET.SubElement(exec_elem, key).text = str(value)
    
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)


def _export_summary_csv(snapshots: List[HealthSnapshot], output_path: str) -> None:
    """Export summary data to CSV format."""
    from .reporters import generate_system_health_summary
    
    system_summary = generate_system_health_summary(snapshots)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Devices", system_summary.total_devices])
        writer.writerow(["Healthy Devices", system_summary.healthy_devices])
        writer.writerow(["Warning Devices", system_summary.warning_devices])
        writer.writerow(["Critical Devices", system_summary.critical_devices])
        writer.writerow(["Total Capacity (GB)", system_summary.total_capacity_gb])
        writer.writerow(["Average Temperature (°C)", f"{system_summary.average_temperature_celsius:.1f}"])
        writer.writerow(["Total Errors", system_summary.total_errors])
        writer.writerow(["Collection Time", system_summary.collection_timestamp.isoformat()])


def _export_prometheus_metrics(snapshots: List[HealthSnapshot], output_path: str) -> None:
    """Export data in Prometheus metrics format."""
    lines = []
    lines.append("# HELP nvme_health_status NVMe device health status (0=good, 1=warning, 2=critical)")
    lines.append("# TYPE nvme_health_status gauge")
    
    for snapshot in snapshots:
        device = snapshot.device_info.device_path
        if snapshot.smart_data:
            status_value = {"good": 0, "warning": 1, "critical": 2}.get(snapshot.smart_data.health_status.value, 3)
            lines.append(f'nvme_health_status{{device="{device}"}} {status_value}')
    
    lines.append("")
    lines.append("# HELP nvme_temperature_celsius NVMe device temperature in Celsius")
    lines.append("# TYPE nvme_temperature_celsius gauge")
    
    for snapshot in snapshots:
        device = snapshot.device_info.device_path
        if snapshot.smart_data and snapshot.smart_data.temperature:
            temp = snapshot.smart_data.temperature.celsius
            lines.append(f'nvme_temperature_celsius{{device="{device}"}} {temp}')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def _export_grafana_json(snapshots: List[HealthSnapshot], output_path: str) -> None:
    """Export data in Grafana JSON format."""
    grafana_data = {
        "dashboard": {
            "title": "NVMe Health Monitoring",
            "panels": [],
            "time": {
                "from": "now-1h",
                "to": "now"
            }
        },
        "data": []
    }
    
    for snapshot in snapshots:
        device_data = {
            "device": snapshot.device_info.device_path,
            "timestamp": snapshot.timestamp.isoformat(),
            "metrics": {}
        }
        
        if snapshot.smart_data:
            smart = snapshot.smart_data
            device_data["metrics"] = {
                "health_status": smart.health_status.value,
                "temperature": smart.temperature.celsius if smart.temperature else None,
                "available_spare": smart.available_spare_percent,
                "percentage_used": smart.percentage_used,
                "power_on_hours": smart.power_on_hours,
                "media_errors": smart.media_errors
            }
        
        grafana_data["data"].append(device_data)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(grafana_data, f, indent=2, default=str)


def _export_nagios_format(snapshots: List[HealthSnapshot], output_path: str) -> None:
    """Export data in Nagios-compatible format."""
    nagios_data = []
    
    for snapshot in snapshots:
        device = snapshot.device_info.device_path
        
        if snapshot.smart_data:
            smart = snapshot.smart_data
            
            if smart.health_status.value == "critical":
                status = "CRITICAL"
                exit_code = 2
            elif smart.health_status.value == "warning":
                status = "WARNING"
                exit_code = 1
            else:
                status = "OK"
                exit_code = 0
            
            message = f"NVMe {device} - {status}"
            if smart.temperature:
                message += f" | temp={smart.temperature.celsius}°C"
            if smart.available_spare_percent is not None:
                message += f" spare={smart.available_spare_percent}%"
            if smart.percentage_used is not None:
                message += f" used={smart.percentage_used}%"
            
            nagios_data.append({
                "device": device,
                "status": status,
                "exit_code": exit_code,
                "message": message,
                "timestamp": snapshot.timestamp.isoformat()
            })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(nagios_data, f, indent=2, default=str)
