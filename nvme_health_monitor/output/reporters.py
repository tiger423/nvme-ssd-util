"""
Reporting utilities for NVMe health monitoring.

This module provides functions to generate comprehensive reports
from NVMe health data, including trend analysis and health summaries.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

from ..models.health_metrics import HealthSnapshot, SystemHealthSummary, HealthStatus
from .formatters import format_health_summary_text, format_device_comparison_table


def generate_health_report(snapshots: List[HealthSnapshot], 
                          report_type: str = "summary",
                          include_trends: bool = False) -> Dict[str, Any]:
    """
    Generate comprehensive health report from snapshots.
    
    Args:
        snapshots: List of health snapshots
        report_type: Type of report ('summary', 'detailed', 'critical')
        include_trends: Whether to include trend analysis
        
    Returns:
        Health report dictionary
    """
    if not snapshots:
        return {"error": "No snapshots provided for report generation"}
    
    report = {
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "report_type": report_type,
            "device_count": len(snapshots),
            "include_trends": include_trends
        },
        "executive_summary": _generate_executive_summary(snapshots),
        "device_summaries": []
    }
    
    for snapshot in snapshots:
        device_summary = _generate_device_summary(snapshot, report_type)
        report["device_summaries"].append(device_summary)
    
    if include_trends and len(snapshots) > 1:
        report["trend_analysis"] = _generate_trend_analysis(snapshots)
    
    if report_type == "critical":
        report["critical_issues"] = _identify_critical_issues(snapshots)
    
    report["recommendations"] = _generate_recommendations(snapshots)
    
    return report


def generate_system_health_summary(snapshots: List[HealthSnapshot]) -> SystemHealthSummary:
    """
    Generate system-wide health summary from device snapshots.
    
    Args:
        snapshots: List of health snapshots
        
    Returns:
        SystemHealthSummary object
    """
    if not snapshots:
        return SystemHealthSummary(
            total_devices=0,
            healthy_devices=0,
            warning_devices=0,
            critical_devices=0,
            total_capacity_gb=0.0,
            average_temperature_celsius=0.0,
            total_errors=0,
            collection_timestamp=datetime.utcnow()
        )
    
    healthy_count = 0
    warning_count = 0
    critical_count = 0
    total_capacity = 0.0
    total_temp = 0.0
    temp_count = 0
    total_errors = 0
    
    for snapshot in snapshots:
        if snapshot.smart_data:
            status = snapshot.smart_data.health_status
            if status == HealthStatus.GOOD:
                healthy_count += 1
            elif status == HealthStatus.WARNING:
                warning_count += 1
            elif status == HealthStatus.CRITICAL:
                critical_count += 1
            
            if snapshot.smart_data.temperature:
                total_temp += snapshot.smart_data.temperature.celsius
                temp_count += 1
        
        total_capacity += snapshot.device_info.controller_info.total_capacity_gb
        
        if snapshot.error_logs:
            total_errors += len(snapshot.error_logs)
    
    avg_temp = total_temp / temp_count if temp_count > 0 else 0.0
    
    return SystemHealthSummary(
        total_devices=len(snapshots),
        healthy_devices=healthy_count,
        warning_devices=warning_count,
        critical_devices=critical_count,
        total_capacity_gb=total_capacity,
        average_temperature_celsius=avg_temp,
        total_errors=total_errors,
        collection_timestamp=datetime.utcnow()
    )


def generate_maintenance_report(snapshots: List[HealthSnapshot]) -> Dict[str, Any]:
    """
    Generate maintenance-focused report with actionable items.
    
    Args:
        snapshots: List of health snapshots
        
    Returns:
        Maintenance report dictionary
    """
    report = {
        "report_type": "maintenance",
        "generated_at": datetime.utcnow().isoformat(),
        "immediate_actions": [],
        "scheduled_maintenance": [],
        "monitoring_recommendations": [],
        "device_details": []
    }
    
    for snapshot in snapshots:
        device_path = snapshot.device_info.device_path
        smart = snapshot.smart_data
        
        device_actions = {
            "device": device_path,
            "immediate": [],
            "scheduled": [],
            "monitoring": []
        }
        
        if smart:
            if smart.critical_warning and smart.critical_warning > 0:
                device_actions["immediate"].append({
                    "priority": "CRITICAL",
                    "action": "Investigate critical warning",
                    "details": f"Critical warning code: {smart.critical_warning}"
                })
            
            if smart.temperature and smart.temperature.celsius > 80:
                device_actions["immediate"].append({
                    "priority": "HIGH",
                    "action": "Check cooling system",
                    "details": f"Temperature: {smart.temperature.celsius}°C"
                })
            
            if smart.available_spare_percent and smart.available_spare_percent < 10:
                device_actions["scheduled"].append({
                    "priority": "MEDIUM",
                    "action": "Plan device replacement",
                    "details": f"Available spare: {smart.available_spare_percent}%"
                })
            
            if smart.percentage_used and smart.percentage_used > 90:
                device_actions["scheduled"].append({
                    "priority": "MEDIUM", 
                    "action": "Plan device replacement",
                    "details": f"Percentage used: {smart.percentage_used}%"
                })
            
            if smart.media_errors and smart.media_errors > 0:
                device_actions["monitoring"].append({
                    "priority": "MEDIUM",
                    "action": "Monitor media error trend",
                    "details": f"Current media errors: {smart.media_errors}"
                })
        
        if snapshot.error_logs and len(snapshot.error_logs) > 10:
            device_actions["monitoring"].append({
                "priority": "MEDIUM",
                "action": "Monitor error log growth",
                "details": f"Current error count: {len(snapshot.error_logs)}"
            })
        
        report["device_details"].append(device_actions)
        
        report["immediate_actions"].extend(device_actions["immediate"])
        report["scheduled_maintenance"].extend(device_actions["scheduled"])
        report["monitoring_recommendations"].extend(device_actions["monitoring"])
    
    report["immediate_actions"].sort(key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}.get(x["priority"], 3))
    
    return report


def save_report_to_file(report: Dict[str, Any], output_path: str, format_type: str = "json") -> None:
    """
    Save report to file in specified format.
    
    Args:
        report: Report dictionary to save
        output_path: Output file path
        format_type: Output format ('json', 'text')
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if format_type == "json":
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
    
    elif format_type == "text":
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(_format_report_as_text(report))
    
    else:
        raise ValueError(f"Unsupported format type: {format_type}")


def _generate_executive_summary(snapshots: List[HealthSnapshot]) -> Dict[str, Any]:
    """Generate executive summary from snapshots."""
    total_devices = len(snapshots)
    healthy = sum(1 for s in snapshots if s.smart_data and s.smart_data.health_status == HealthStatus.GOOD)
    warning = sum(1 for s in snapshots if s.smart_data and s.smart_data.health_status == HealthStatus.WARNING)
    critical = sum(1 for s in snapshots if s.smart_data and s.smart_data.health_status == HealthStatus.CRITICAL)
    
    total_errors = sum(len(s.error_logs) if s.error_logs else 0 for s in snapshots)
    
    return {
        "total_devices": total_devices,
        "health_distribution": {
            "healthy": healthy,
            "warning": warning,
            "critical": critical
        },
        "total_errors": total_errors,
        "overall_status": "CRITICAL" if critical > 0 else "WARNING" if warning > 0 else "HEALTHY"
    }


def _generate_device_summary(snapshot: HealthSnapshot, report_type: str) -> Dict[str, Any]:
    """Generate summary for individual device."""
    device = snapshot.device_info
    smart = snapshot.smart_data
    
    summary = {
        "device_path": device.device_path,
        "model": device.controller_info.model_name,
        "serial": device.controller_info.serial_number,
        "capacity_gb": device.controller_info.total_capacity_gb
    }
    
    if smart:
        summary.update({
            "health_status": smart.health_status.value,
            "temperature_celsius": smart.temperature.celsius if smart.temperature else None,
            "available_spare_percent": smart.available_spare_percent,
            "percentage_used": smart.percentage_used,
            "power_on_hours": smart.power_on_hours,
            "media_errors": smart.media_errors
        })
    
    if report_type == "detailed":
        summary["error_count"] = len(snapshot.error_logs) if snapshot.error_logs else 0
        if snapshot.self_test_log and snapshot.self_test_log.entries:
            latest_test = snapshot.self_test_log.entries[0]
            summary["latest_self_test"] = {
                "type": latest_test.test_type.value,
                "result": latest_test.result.value,
                "completion_time": latest_test.completion_timestamp.isoformat() if latest_test.completion_timestamp else None
            }
    
    return summary


def _generate_trend_analysis(snapshots: List[HealthSnapshot]) -> Dict[str, Any]:
    """Generate trend analysis from multiple snapshots."""
    return {
        "note": "Trend analysis requires historical data from multiple collection periods",
        "current_snapshot_count": len(snapshots),
        "recommendation": "Implement regular monitoring to enable trend analysis"
    }


def _identify_critical_issues(snapshots: List[HealthSnapshot]) -> List[Dict[str, Any]]:
    """Identify critical issues from snapshots."""
    issues = []
    
    for snapshot in snapshots:
        device_path = snapshot.device_info.device_path
        smart = snapshot.smart_data
        
        if smart:
            if smart.critical_warning and smart.critical_warning > 0:
                issues.append({
                    "device": device_path,
                    "issue": "Critical Warning Active",
                    "severity": "CRITICAL",
                    "details": f"Warning code: {smart.critical_warning}"
                })
            
            if smart.temperature and smart.temperature.celsius > 85:
                issues.append({
                    "device": device_path,
                    "issue": "High Temperature",
                    "severity": "CRITICAL",
                    "details": f"Temperature: {smart.temperature.celsius}°C"
                })
            
            if smart.available_spare_percent and smart.available_spare_percent < 5:
                issues.append({
                    "device": device_path,
                    "issue": "Low Available Spare",
                    "severity": "CRITICAL",
                    "details": f"Available spare: {smart.available_spare_percent}%"
                })
            
            if smart.media_errors and smart.media_errors > 10:
                issues.append({
                    "device": device_path,
                    "issue": "High Media Error Count",
                    "severity": "CRITICAL",
                    "details": f"Media errors: {smart.media_errors}"
                })
    
    return issues


def _generate_recommendations(snapshots: List[HealthSnapshot]) -> List[Dict[str, Any]]:
    """Generate recommendations based on snapshot analysis."""
    recommendations = []
    
    critical_devices = [s for s in snapshots if s.smart_data and s.smart_data.health_status == HealthStatus.CRITICAL]
    warning_devices = [s for s in snapshots if s.smart_data and s.smart_data.health_status == HealthStatus.WARNING]
    
    if critical_devices:
        recommendations.append({
            "priority": "IMMEDIATE",
            "action": "Address critical device issues",
            "details": f"{len(critical_devices)} device(s) require immediate attention"
        })
    
    if warning_devices:
        recommendations.append({
            "priority": "SCHEDULED",
            "action": "Monitor warning devices closely",
            "details": f"{len(warning_devices)} device(s) showing warning signs"
        })
    
    high_temp_devices = [s for s in snapshots if s.smart_data and s.smart_data.temperature and s.smart_data.temperature.celsius > 70]
    if high_temp_devices:
        recommendations.append({
            "priority": "MEDIUM",
            "action": "Review cooling system",
            "details": f"{len(high_temp_devices)} device(s) running hot"
        })
    
    recommendations.append({
        "priority": "ONGOING",
        "action": "Implement regular monitoring",
        "details": "Schedule automated health checks every 4-6 hours"
    })
    
    return recommendations


def _format_report_as_text(report: Dict[str, Any]) -> str:
    """Format report dictionary as readable text."""
    lines = []
    
    lines.append("NVMe Health Monitoring Report")
    lines.append("=" * 50)
    lines.append(f"Generated: {report.get('report_metadata', {}).get('generated_at', 'Unknown')}")
    lines.append(f"Report Type: {report.get('report_metadata', {}).get('report_type', 'Unknown')}")
    lines.append("")
    
    if "executive_summary" in report:
        summary = report["executive_summary"]
        lines.append("Executive Summary")
        lines.append("-" * 20)
        lines.append(f"Total Devices: {summary.get('total_devices', 0)}")
        lines.append(f"Overall Status: {summary.get('overall_status', 'Unknown')}")
        
        health_dist = summary.get('health_distribution', {})
        lines.append(f"Healthy: {health_dist.get('healthy', 0)}")
        lines.append(f"Warning: {health_dist.get('warning', 0)}")
        lines.append(f"Critical: {health_dist.get('critical', 0)}")
        lines.append(f"Total Errors: {summary.get('total_errors', 0)}")
        lines.append("")
    
    if "critical_issues" in report and report["critical_issues"]:
        lines.append("Critical Issues")
        lines.append("-" * 20)
        for issue in report["critical_issues"]:
            lines.append(f"• {issue.get('device', 'Unknown')}: {issue.get('issue', 'Unknown issue')}")
            lines.append(f"  {issue.get('details', '')}")
        lines.append("")
    
    if "recommendations" in report:
        lines.append("Recommendations")
        lines.append("-" * 20)
        for rec in report["recommendations"]:
            lines.append(f"• [{rec.get('priority', 'UNKNOWN')}] {rec.get('action', 'Unknown action')}")
            lines.append(f"  {rec.get('details', '')}")
        lines.append("")
    
    return "\n".join(lines)
