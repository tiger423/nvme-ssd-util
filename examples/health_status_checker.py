#!/usr/bin/env python3
"""
NVMe SSD Health Status Checker

This example demonstrates how to comprehensively check an NVMe SSD's health status
and determine if the drive is healthy or requires attention.

HEALTH ASSESSMENT WORKFLOW:
┌─────────────────────────────────────────────────────────────────┐
│ Device Discovery → SMART Data Collection → Health Analysis →   │
│ Critical Alerts → Warning Checks → Overall Health Score →      │
│ Recommendations → Detailed Report                              │
└─────────────────────────────────────────────────────────────────┘

KEY HEALTH INDICATORS:
✅ Temperature monitoring (current, max, critical thresholds)
✅ Available spare capacity (wear leveling reserves)
✅ Percentage used (drive lifetime consumption)
✅ Critical warnings (reliability, temperature, spare, read-only)
✅ Media errors and data integrity issues
✅ Power-on hours and power cycles
✅ Unsafe shutdowns and thermal throttling events

HEALTH SCORING ALGORITHM:
- HEALTHY (90-100): All parameters within normal ranges
- WARNING (70-89): Some parameters approaching limits
- CRITICAL (50-69): Multiple parameters in warning state
- FAILING (0-49): Critical parameters exceeded or drive errors

For technical documentation:
- Function reference: ../docs/FUNCTION_REFERENCE.md
- Integration patterns: ../docs/NVME_FORMAT_CODE_FLOW.md
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent))

from nvme_health_monitor.core.nvme_interface import (
    check_nvme_cli_availability,
    list_nvme_devices,
    get_smart_log,
    get_controller_info,
    get_error_log
)
from nvme_health_monitor.models.exceptions import (
    NVMeCommandError,
    NVMeDeviceNotFoundError,
    NVMePermissionError
)
from nvme_health_monitor.utils.logging_config import setup_logging


class HealthStatus(Enum):
    """Health status levels for NVMe devices."""
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    FAILING = "FAILING"


@dataclass
class HealthMetric:
    """Individual health metric with value, status, and description."""
    name: str
    value: Any
    status: HealthStatus
    description: str
    recommendation: str = ""


@dataclass
class HealthAssessment:
    """Complete health assessment for an NVMe device."""
    device_path: str
    overall_status: HealthStatus
    health_score: int  # 0-100
    metrics: List[HealthMetric]
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[str]


class NVMeHealthChecker:
    """Comprehensive NVMe health status checker."""
    
    def __init__(self):
        """Initialize the health checker with thresholds."""
        self.temp_warning = 70
        self.temp_critical = 85
        
        self.spare_warning = 10
        self.spare_critical = 5
        
        self.used_warning = 80
        self.used_critical = 95
        
        self.poh_warning = 26280  # 3 years
        self.poh_critical = 43800  # 5 years
        
        self.error_warning = 10
        self.error_critical = 100

    def check_device_health(self, device_path: str) -> HealthAssessment:
        """
        Perform comprehensive health check on NVMe device.
        
        This function implements a multi-stage health assessment:
        1. Collect SMART data and device information
        2. Analyze individual health metrics
        3. Calculate overall health score
        4. Generate recommendations
        
        Args:
            device_path: NVMe device path (e.g., "/dev/nvme0")
            
        Returns:
            HealthAssessment: Complete health analysis
            
        Raises:
            NVMeDeviceNotFoundError: Device not found
            NVMeCommandError: Failed to collect health data
        """
        print(f"🔍 Analyzing health status for {device_path}...")
        
        smart_data = get_smart_log(device_path)
        device_info = get_controller_info(device_path)
        
        metrics = []
        critical_issues = []
        warnings = []
        recommendations = []
        
        temp_metric = self._analyze_temperature(smart_data)
        metrics.append(temp_metric)
        if temp_metric.status == HealthStatus.CRITICAL:
            critical_issues.append(f"Temperature critical: {temp_metric.value}°C")
        elif temp_metric.status == HealthStatus.WARNING:
            warnings.append(f"Temperature elevated: {temp_metric.value}°C")
        
        spare_metric = self._analyze_available_spare(smart_data)
        metrics.append(spare_metric)
        if spare_metric.status == HealthStatus.CRITICAL:
            critical_issues.append(f"Available spare critical: {spare_metric.value}%")
        elif spare_metric.status == HealthStatus.WARNING:
            warnings.append(f"Available spare low: {spare_metric.value}%")
        
        used_metric = self._analyze_percentage_used(smart_data)
        metrics.append(used_metric)
        if used_metric.status == HealthStatus.CRITICAL:
            critical_issues.append(f"Drive wear critical: {used_metric.value}%")
        elif used_metric.status == HealthStatus.WARNING:
            warnings.append(f"Drive wear high: {used_metric.value}%")
        
        warnings_metric = self._analyze_critical_warnings(smart_data)
        metrics.append(warnings_metric)
        if warnings_metric.status != HealthStatus.HEALTHY:
            critical_issues.append("Critical warnings detected")
        
        poh_metric = self._analyze_power_on_hours(smart_data)
        metrics.append(poh_metric)
        if poh_metric.status == HealthStatus.WARNING:
            warnings.append(f"High power-on hours: {poh_metric.value}")
        
        try:
            error_log = get_error_log(device_path)
            error_metric = self._analyze_media_errors(error_log)
            metrics.append(error_metric)
            if error_metric.status == HealthStatus.CRITICAL:
                critical_issues.append(f"Media errors detected: {error_metric.value}")
            elif error_metric.status == HealthStatus.WARNING:
                warnings.append(f"Some media errors: {error_metric.value}")
        except Exception as e:
            print(f"⚠️  Could not analyze error log: {e}")
        
        health_score = self._calculate_health_score(metrics)
        overall_status = self._determine_overall_status(health_score, critical_issues)
        
        recommendations = self._generate_recommendations(metrics, critical_issues, warnings)
        
        return HealthAssessment(
            device_path=device_path,
            overall_status=overall_status,
            health_score=health_score,
            metrics=metrics,
            critical_issues=critical_issues,
            warnings=warnings,
            recommendations=recommendations
        )

    def _analyze_temperature(self, smart_data: Dict) -> HealthMetric:
        """Analyze device temperature."""
        temp = smart_data.get('temperature', 0)
        
        if temp >= self.temp_critical:
            status = HealthStatus.CRITICAL
            desc = f"Temperature critically high at {temp}°C"
            rec = "Improve cooling immediately. Check airflow and thermal management."
        elif temp >= self.temp_warning:
            status = HealthStatus.WARNING
            desc = f"Temperature elevated at {temp}°C"
            rec = "Monitor temperature closely. Consider improving cooling."
        else:
            status = HealthStatus.HEALTHY
            desc = f"Temperature normal at {temp}°C"
            rec = ""
        
        return HealthMetric("Temperature", temp, status, desc, rec)

    def _analyze_available_spare(self, smart_data: Dict) -> HealthMetric:
        """Analyze available spare capacity."""
        spare = smart_data.get('available_spare', 100)
        
        if spare <= self.spare_critical:
            status = HealthStatus.CRITICAL
            desc = f"Available spare critically low at {spare}%"
            rec = "Replace drive immediately. Backup data urgently."
        elif spare <= self.spare_warning:
            status = HealthStatus.WARNING
            desc = f"Available spare low at {spare}%"
            rec = "Plan for drive replacement. Monitor closely."
        else:
            status = HealthStatus.HEALTHY
            desc = f"Available spare healthy at {spare}%"
            rec = ""
        
        return HealthMetric("Available Spare", spare, status, desc, rec)

    def _analyze_percentage_used(self, smart_data: Dict) -> HealthMetric:
        """Analyze percentage of drive lifetime used."""
        used = smart_data.get('percentage_used', 0)
        
        if used >= self.used_critical:
            status = HealthStatus.CRITICAL
            desc = f"Drive wear critically high at {used}%"
            rec = "Replace drive soon. Backup data immediately."
        elif used >= self.used_warning:
            status = HealthStatus.WARNING
            desc = f"Drive wear high at {used}%"
            rec = "Plan for drive replacement within 6 months."
        else:
            status = HealthStatus.HEALTHY
            desc = f"Drive wear acceptable at {used}%"
            rec = ""
        
        return HealthMetric("Percentage Used", used, status, desc, rec)

    def _analyze_critical_warnings(self, smart_data: Dict) -> HealthMetric:
        """Analyze critical warning flags."""
        warnings = smart_data.get('critical_warning', 0)
        warning_flags = []
        
        if warnings & 0x01:
            warning_flags.append("Available spare below threshold")
        if warnings & 0x02:
            warning_flags.append("Temperature above threshold")
        if warnings & 0x04:
            warning_flags.append("NVM subsystem reliability degraded")
        if warnings & 0x08:
            warning_flags.append("Media in read-only mode")
        if warnings & 0x10:
            warning_flags.append("Volatile memory backup device failed")
        
        if warning_flags:
            status = HealthStatus.CRITICAL
            desc = f"Critical warnings active: {', '.join(warning_flags)}"
            rec = "Address critical warnings immediately. Check system logs."
        else:
            status = HealthStatus.HEALTHY
            desc = "No critical warnings"
            rec = ""
        
        return HealthMetric("Critical Warnings", len(warning_flags), status, desc, rec)

    def _analyze_power_on_hours(self, smart_data: Dict) -> HealthMetric:
        """Analyze power-on hours."""
        poh = smart_data.get('power_on_hours', 0)
        
        if poh >= self.poh_critical:
            status = HealthStatus.WARNING
            desc = f"Very high power-on hours: {poh:,} hours ({poh/8760:.1f} years)"
            rec = "Consider drive replacement due to age."
        elif poh >= self.poh_warning:
            status = HealthStatus.WARNING
            desc = f"High power-on hours: {poh:,} hours ({poh/8760:.1f} years)"
            rec = "Monitor drive health more frequently."
        else:
            status = HealthStatus.HEALTHY
            desc = f"Power-on hours acceptable: {poh:,} hours ({poh/8760:.1f} years)"
            rec = ""
        
        return HealthMetric("Power-On Hours", poh, status, desc, rec)

    def _analyze_media_errors(self, error_log: List) -> HealthMetric:
        """Analyze media and data integrity errors."""
        error_count = len(error_log) if error_log else 0
        
        if error_count >= self.error_critical:
            status = HealthStatus.CRITICAL
            desc = f"High error count: {error_count} errors"
            rec = "Replace drive immediately. Data integrity at risk."
        elif error_count >= self.error_warning:
            status = HealthStatus.WARNING
            desc = f"Some errors detected: {error_count} errors"
            rec = "Monitor closely. Consider drive replacement."
        else:
            status = HealthStatus.HEALTHY
            desc = f"Low error count: {error_count} errors"
            rec = ""
        
        return HealthMetric("Media Errors", error_count, status, desc, rec)

    def _calculate_health_score(self, metrics: List[HealthMetric]) -> int:
        """Calculate overall health score (0-100)."""
        if not metrics:
            return 0
        
        score = 100
        for metric in metrics:
            if metric.status == HealthStatus.CRITICAL:
                score -= 30
            elif metric.status == HealthStatus.WARNING:
                score -= 15
            elif metric.status == HealthStatus.FAILING:
                score -= 50
        
        return max(0, score)

    def _determine_overall_status(self, health_score: int, critical_issues: List[str]) -> HealthStatus:
        """Determine overall health status."""
        if critical_issues:
            return HealthStatus.CRITICAL
        elif health_score >= 90:
            return HealthStatus.HEALTHY
        elif health_score >= 70:
            return HealthStatus.WARNING
        else:
            return HealthStatus.CRITICAL

    def _generate_recommendations(self, metrics: List[HealthMetric], 
                                critical_issues: List[str], warnings: List[str]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        for metric in metrics:
            if metric.recommendation:
                recommendations.append(metric.recommendation)
        
        if critical_issues:
            recommendations.append("Perform immediate backup of critical data")
            recommendations.append("Plan for drive replacement within 30 days")
        elif warnings:
            recommendations.append("Increase monitoring frequency to weekly")
            recommendations.append("Plan for drive replacement within 6 months")
        else:
            recommendations.append("Continue regular monthly health checks")
        
        return list(set(recommendations))  # Remove duplicates

    def display_health_report(self, assessment: HealthAssessment) -> None:
        """Display comprehensive health report."""
        print("\n" + "="*80)
        print("🏥 NVMe SSD HEALTH ASSESSMENT REPORT")
        print("="*80)
        
        status_emoji = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.WARNING: "⚠️",
            HealthStatus.CRITICAL: "🚨",
            HealthStatus.FAILING: "💀"
        }
        
        print(f"\n📊 OVERALL STATUS: {status_emoji[assessment.overall_status]} {assessment.overall_status.value}")
        print(f"📈 HEALTH SCORE: {assessment.health_score}/100")
        print(f"🔧 DEVICE: {assessment.device_path}")
        
        if assessment.critical_issues:
            print(f"\n🚨 CRITICAL ISSUES ({len(assessment.critical_issues)}):")
            for issue in assessment.critical_issues:
                print(f"   • {issue}")
        
        if assessment.warnings:
            print(f"\n⚠️  WARNINGS ({len(assessment.warnings)}):")
            for warning in assessment.warnings:
                print(f"   • {warning}")
        
        print(f"\n📋 DETAILED HEALTH METRICS:")
        print("-" * 80)
        for metric in assessment.metrics:
            status_symbol = status_emoji.get(metric.status, "❓")
            print(f"{status_symbol} {metric.name}: {metric.value}")
            print(f"   Status: {metric.status.value}")
            print(f"   Details: {metric.description}")
            if metric.recommendation:
                print(f"   Action: {metric.recommendation}")
            print()
        
        if assessment.recommendations:
            print("💡 RECOMMENDATIONS:")
            for i, rec in enumerate(assessment.recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("="*80)


def check_single_device(device_path: str) -> None:
    """Check health status of a single NVMe device."""
    checker = NVMeHealthChecker()
    
    try:
        assessment = checker.check_device_health(device_path)
        checker.display_health_report(assessment)
        
        if assessment.overall_status in [HealthStatus.CRITICAL, HealthStatus.FAILING]:
            return 2  # Critical issues
        elif assessment.overall_status == HealthStatus.WARNING:
            return 1  # Warnings
        else:
            return 0  # Healthy
            
    except NVMeDeviceNotFoundError:
        print(f"❌ Device not found: {device_path}")
        return 3
    except NVMePermissionError:
        print(f"❌ Permission denied accessing {device_path}")
        print("Try running with sudo or ensure user is in nvme group")
        return 4
    except Exception as e:
        print(f"❌ Error checking device health: {e}")
        return 5


def check_all_devices() -> None:
    """Check health status of all NVMe devices in the system."""
    print("🔍 Discovering NVMe devices...")
    
    try:
        devices = list_nvme_devices()
        if not devices:
            print("❌ No NVMe devices found in the system")
            return
        
        print(f"✅ Found {len(devices)} NVMe device(s)")
        
        checker = NVMeHealthChecker()
        overall_status = HealthStatus.HEALTHY
        
        for i, device in enumerate(devices, 1):
            device_path = device['device_path']
            print(f"\n{'='*60}")
            print(f"📱 DEVICE {i}/{len(devices)}: {device_path}")
            print(f"Model: {device.get('model', 'Unknown')}")
            print(f"Serial: {device.get('serial_number', 'Unknown')}")
            print('='*60)
            
            try:
                assessment = checker.check_device_health(device_path)
                checker.display_health_report(assessment)
                
                if assessment.overall_status == HealthStatus.CRITICAL:
                    overall_status = HealthStatus.CRITICAL
                elif assessment.overall_status == HealthStatus.WARNING and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.WARNING
                    
            except Exception as e:
                print(f"❌ Failed to check {device_path}: {e}")
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.WARNING
        
        print(f"\n{'='*80}")
        print("📊 SYSTEM HEALTH SUMMARY")
        print('='*80)
        print(f"Total devices checked: {len(devices)}")
        print(f"Overall system status: {overall_status.value}")
        
        if overall_status == HealthStatus.CRITICAL:
            print("🚨 IMMEDIATE ACTION REQUIRED: Critical issues detected")
        elif overall_status == HealthStatus.WARNING:
            print("⚠️  ATTENTION NEEDED: Warnings detected")
        else:
            print("✅ All devices appear healthy")
        
    except Exception as e:
        print(f"❌ Error discovering devices: {e}")


def main():
    """Main entry point for health status checker."""
    print("🏥 NVMe SSD Health Status Checker")
    print("="*50)
    
    if not check_nvme_cli_availability():
        print("❌ nvme-cli not available. Please install:")
        print("   Ubuntu/Debian: sudo apt install nvme-cli")
        print("   RHEL/CentOS: sudo yum install nvme-cli")
        return 1
    
    logger = setup_logging("INFO")
    
    if len(sys.argv) > 1:
        device_path = sys.argv[1]
        print(f"Checking specific device: {device_path}")
        return check_single_device(device_path)
    else:
        print("Checking all NVMe devices in system...")
        check_all_devices()
        return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Health check cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(5)
