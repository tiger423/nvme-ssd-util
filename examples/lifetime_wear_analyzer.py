#!/usr/bin/env python3
"""
NVMe SSD Lifetime and Wear Status Analyzer

This example demonstrates how to analyze NVMe SSD lifetime usage and wear status,
providing detailed insights into drive aging, endurance consumption, and remaining lifespan.

LIFETIME ANALYSIS WORKFLOW:
┌─────────────────────────────────────────────────────────────────┐
│ SMART Data Collection → Wear Metrics Analysis → Lifetime       │
│ Calculation → Endurance Assessment → Remaining Life Prediction │
│ → Wear Rate Analysis → Comprehensive Report                    │
└─────────────────────────────────────────────────────────────────┘

KEY WEAR INDICATORS:
📊 Percentage Used (drive lifetime consumption)
🔋 Available Spare (wear leveling reserves)
⏱️  Power-On Hours (operational time)
🔄 Power Cycles (start/stop cycles)
📝 Data Units Written/Read (total I/O volume)
🚨 Media Errors (wear-related failures)
🌡️  Temperature History (thermal stress)
⚡ Unsafe Shutdowns (power loss events)

LIFETIME CALCULATIONS:
- Remaining lifespan estimation based on current wear rate
- Endurance consumption analysis (TBW vs actual writes)
- Wear leveling efficiency assessment
- Temperature impact on lifetime
- Write amplification factor calculation
- Predictive failure analysis

WEAR ASSESSMENT CATEGORIES:
- EXCELLENT (0-25% used): Like new condition
- GOOD (26-50% used): Normal wear, good condition
- MODERATE (51-75% used): Moderate wear, monitor closely
- HIGH (76-90% used): High wear, plan replacement
- CRITICAL (91-100% used): End of life, replace immediately

For technical documentation:
- Function reference: ../docs/FUNCTION_REFERENCE.md
- Integration patterns: ../docs/NVME_FORMAT_CODE_FLOW.md
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent))

from nvme_health_monitor.core.nvme_interface import (
    check_nvme_cli_availability,
    list_nvme_devices,
    get_smart_log,
    get_controller_info
)
from nvme_health_monitor.models.exceptions import (
    NVMeCommandError,
    NVMeDeviceNotFoundError,
    NVMePermissionError
)
from nvme_health_monitor.utils.logging_config import setup_logging


class WearLevel(Enum):
    """Wear level categories."""
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class WearMetrics:
    """Core wear and lifetime metrics."""
    percentage_used: int
    available_spare: int
    available_spare_threshold: int
    power_on_hours: int
    power_cycles: int
    unsafe_shutdowns: int
    data_units_written: int
    data_units_read: int
    host_writes: int
    host_reads: int
    media_errors: int
    error_log_entries: int


@dataclass
class LifetimeAnalysis:
    """Lifetime and endurance analysis."""
    wear_level: WearLevel
    estimated_remaining_life_days: Optional[int]
    estimated_remaining_life_years: Optional[float]
    daily_wear_rate: float
    monthly_wear_rate: float
    yearly_wear_rate: float
    total_bytes_written: int
    total_bytes_read: int
    write_amplification_factor: Optional[float]
    endurance_rating_tbw: Optional[float]
    actual_tbw: float
    endurance_consumption_percent: Optional[float]


@dataclass
class TemperatureAnalysis:
    """Temperature impact on lifetime."""
    current_temperature: int
    max_temperature: int
    temperature_impact_factor: float
    thermal_stress_level: str
    temperature_related_wear: float


@dataclass
class PowerAnalysis:
    """Power-related wear analysis."""
    power_on_years: float
    average_daily_hours: float
    power_cycle_frequency: float
    unsafe_shutdown_rate: float
    power_related_wear: float


@dataclass
class PredictiveAnalysis:
    """Predictive failure and replacement analysis."""
    replacement_urgency: str
    recommended_action: str
    monitoring_frequency: str
    backup_priority: str
    failure_risk_score: int  # 0-100
    predicted_failure_timeframe: Optional[str]


@dataclass
class ComprehensiveWearAnalysis:
    """Complete wear and lifetime analysis."""
    device_path: str
    device_model: str
    device_serial: str
    analysis_timestamp: str
    wear_metrics: WearMetrics
    lifetime_analysis: LifetimeAnalysis
    temperature_analysis: TemperatureAnalysis
    power_analysis: PowerAnalysis
    predictive_analysis: PredictiveAnalysis
    recommendations: List[str]
    raw_smart_data: Dict[str, Any]


class NVMeLifetimeAnalyzer:
    """Comprehensive NVMe lifetime and wear analyzer."""
    
    def __init__(self):
        """Initialize the lifetime analyzer."""
        self.logger = setup_logging("INFO")
        
        self.wear_thresholds = {
            WearLevel.EXCELLENT: (0, 25),
            WearLevel.GOOD: (26, 50),
            WearLevel.MODERATE: (51, 75),
            WearLevel.HIGH: (76, 90),
            WearLevel.CRITICAL: (91, 100)
        }
        
        self.temp_impact_thresholds = {
            'low': (0, 45, 1.0),      # No impact
            'moderate': (46, 65, 1.2), # 20% faster wear
            'high': (66, 80, 1.5),     # 50% faster wear
            'critical': (81, 100, 2.0) # 100% faster wear
        }

    def analyze_device_lifetime(self, device_path: str) -> ComprehensiveWearAnalysis:
        """
        Perform comprehensive lifetime and wear analysis.
        
        This function analyzes all aspects of NVMe device wear and lifetime:
        1. Collect and parse SMART wear metrics
        2. Calculate wear rates and remaining lifetime
        3. Analyze temperature impact on longevity
        4. Assess power-related wear factors
        5. Generate predictive failure analysis
        6. Provide actionable recommendations
        
        Args:
            device_path: NVMe device path (e.g., "/dev/nvme0")
            
        Returns:
            ComprehensiveWearAnalysis: Complete wear and lifetime analysis
            
        Raises:
            NVMeDeviceNotFoundError: Device not found
            NVMeCommandError: Failed to collect device data
        """
        print(f"🔍 Analyzing lifetime and wear for {device_path}...")
        
        smart_data = get_smart_log(device_path)
        device_info = get_controller_info(device_path)
        
        device_model = device_info.get('mn', 'Unknown').strip()
        device_serial = device_info.get('sn', 'Unknown').strip()
        
        wear_metrics = self._parse_wear_metrics(smart_data)
        
        lifetime_analysis = self._analyze_lifetime(wear_metrics, device_info)
        
        temperature_analysis = self._analyze_temperature_impact(smart_data)
        
        power_analysis = self._analyze_power_wear(wear_metrics)
        
        predictive_analysis = self._generate_predictive_analysis(
            wear_metrics, lifetime_analysis, temperature_analysis, power_analysis
        )
        
        recommendations = self._generate_recommendations(
            wear_metrics, lifetime_analysis, predictive_analysis
        )
        
        return ComprehensiveWearAnalysis(
            device_path=device_path,
            device_model=device_model,
            device_serial=device_serial,
            analysis_timestamp=datetime.now().isoformat(),
            wear_metrics=wear_metrics,
            lifetime_analysis=lifetime_analysis,
            temperature_analysis=temperature_analysis,
            power_analysis=power_analysis,
            predictive_analysis=predictive_analysis,
            recommendations=recommendations,
            raw_smart_data=smart_data
        )

    def _parse_wear_metrics(self, smart_data: Dict) -> WearMetrics:
        """Parse wear-related metrics from SMART data."""
        return WearMetrics(
            percentage_used=smart_data.get('percentage_used', 0),
            available_spare=smart_data.get('available_spare', 100),
            available_spare_threshold=smart_data.get('available_spare_threshold', 10),
            power_on_hours=smart_data.get('power_on_hours', 0),
            power_cycles=smart_data.get('power_cycles', 0),
            unsafe_shutdowns=smart_data.get('unsafe_shutdowns', 0),
            data_units_written=smart_data.get('data_units_written', 0),
            data_units_read=smart_data.get('data_units_read', 0),
            host_writes=smart_data.get('host_writes', 0),
            host_reads=smart_data.get('host_reads', 0),
            media_errors=smart_data.get('media_errors', 0),
            error_log_entries=smart_data.get('num_err_log_entries', 0)
        )

    def _analyze_lifetime(self, wear_metrics: WearMetrics, device_info: Dict) -> LifetimeAnalysis:
        """Analyze device lifetime and endurance consumption."""
        
        wear_level = self._determine_wear_level(wear_metrics.percentage_used)
        
        if wear_metrics.power_on_hours > 0:
            daily_wear_rate = (wear_metrics.percentage_used / wear_metrics.power_on_hours) * 24
            monthly_wear_rate = daily_wear_rate * 30
            yearly_wear_rate = daily_wear_rate * 365
        else:
            daily_wear_rate = 0
            monthly_wear_rate = 0
            yearly_wear_rate = 0
        
        remaining_life_days = None
        remaining_life_years = None
        
        if daily_wear_rate > 0 and wear_metrics.percentage_used < 100:
            remaining_percentage = 100 - wear_metrics.percentage_used
            remaining_life_days = int(remaining_percentage / daily_wear_rate)
            remaining_life_years = remaining_life_days / 365.25
        
        total_bytes_written = wear_metrics.data_units_written * 1000 * 512
        total_bytes_read = wear_metrics.data_units_read * 1000 * 512
        
        actual_tbw = total_bytes_written / (1024**4)  # Convert to TB
        
        endurance_rating_tbw = self._estimate_endurance_rating(device_info, total_bytes_written)
        
        endurance_consumption_percent = None
        if endurance_rating_tbw and endurance_rating_tbw > 0:
            endurance_consumption_percent = (actual_tbw / endurance_rating_tbw) * 100
        
        write_amplification_factor = None
        if wear_metrics.host_writes > 0 and wear_metrics.data_units_written > 0:
            host_writes_units = wear_metrics.host_writes / (1000 * 512)
            write_amplification_factor = wear_metrics.data_units_written / host_writes_units
        
        return LifetimeAnalysis(
            wear_level=wear_level,
            estimated_remaining_life_days=remaining_life_days,
            estimated_remaining_life_years=remaining_life_years,
            daily_wear_rate=daily_wear_rate,
            monthly_wear_rate=monthly_wear_rate,
            yearly_wear_rate=yearly_wear_rate,
            total_bytes_written=total_bytes_written,
            total_bytes_read=total_bytes_read,
            write_amplification_factor=write_amplification_factor,
            endurance_rating_tbw=endurance_rating_tbw,
            actual_tbw=actual_tbw,
            endurance_consumption_percent=endurance_consumption_percent
        )

    def _determine_wear_level(self, percentage_used: int) -> WearLevel:
        """Determine wear level based on percentage used."""
        for level, (min_pct, max_pct) in self.wear_thresholds.items():
            if min_pct <= percentage_used <= max_pct:
                return level
        return WearLevel.CRITICAL

    def _estimate_endurance_rating(self, device_info: Dict, total_written: int) -> Optional[float]:
        """Estimate device endurance rating in TBW."""
        
        total_capacity = device_info.get('tnvmcap', 0)
        if total_capacity == 0:
            return None
        
        capacity_gb = total_capacity / (1024**3)
        
        
        estimated_tbw = capacity_gb * 0.6 / 1024  # Convert to TB
        
        return estimated_tbw

    def _analyze_temperature_impact(self, smart_data: Dict) -> TemperatureAnalysis:
        """Analyze temperature impact on device lifetime."""
        
        current_temp = smart_data.get('temperature', 0)
        max_temp = smart_data.get('max_temperature', current_temp)
        
        impact_factor = 1.0
        stress_level = "Low"
        
        for level, (min_temp, max_temp_thresh, factor) in self.temp_impact_thresholds.items():
            if min_temp <= current_temp <= max_temp_thresh:
                impact_factor = factor
                stress_level = level.capitalize()
                break
        
        temp_wear = max(0, (current_temp - 25) * 0.1)  # Wear increases above 25°C
        
        return TemperatureAnalysis(
            current_temperature=current_temp,
            max_temperature=max_temp,
            temperature_impact_factor=impact_factor,
            thermal_stress_level=stress_level,
            temperature_related_wear=temp_wear
        )

    def _analyze_power_wear(self, wear_metrics: WearMetrics) -> PowerAnalysis:
        """Analyze power-related wear factors."""
        
        power_on_years = wear_metrics.power_on_hours / 8760 if wear_metrics.power_on_hours > 0 else 0
        
        if power_on_years > 0:
            total_days = power_on_years * 365.25
            average_daily_hours = wear_metrics.power_on_hours / total_days
        else:
            average_daily_hours = 0
        
        if power_on_years > 0:
            power_cycle_frequency = wear_metrics.power_cycles / (power_on_years * 365.25)
        else:
            power_cycle_frequency = 0
        
        if wear_metrics.power_cycles > 0:
            unsafe_shutdown_rate = (wear_metrics.unsafe_shutdowns / wear_metrics.power_cycles) * 100
        else:
            unsafe_shutdown_rate = 0
        
        power_wear = 0
        if power_cycle_frequency > 10:  # More than 10 cycles per day
            power_wear += 5
        if unsafe_shutdown_rate > 5:  # More than 5% unsafe shutdowns
            power_wear += 10
        
        return PowerAnalysis(
            power_on_years=power_on_years,
            average_daily_hours=average_daily_hours,
            power_cycle_frequency=power_cycle_frequency,
            unsafe_shutdown_rate=unsafe_shutdown_rate,
            power_related_wear=power_wear
        )

    def _generate_predictive_analysis(self, wear_metrics: WearMetrics, 
                                    lifetime_analysis: LifetimeAnalysis,
                                    temperature_analysis: TemperatureAnalysis,
                                    power_analysis: PowerAnalysis) -> PredictiveAnalysis:
        """Generate predictive failure and replacement analysis."""
        
        risk_score = 0
        
        risk_score += wear_metrics.percentage_used * 0.5
        
        if wear_metrics.available_spare < wear_metrics.available_spare_threshold:
            risk_score += 20
        elif wear_metrics.available_spare < 20:
            risk_score += 10
        
        if temperature_analysis.current_temperature > 80:
            risk_score += 15
        elif temperature_analysis.current_temperature > 70:
            risk_score += 10
        
        if wear_metrics.media_errors > 0:
            risk_score += min(wear_metrics.media_errors * 2, 20)
        
        risk_score += min(power_analysis.power_related_wear, 15)
        
        risk_score = min(100, max(0, int(risk_score)))
        
        if risk_score >= 80 or lifetime_analysis.wear_level == WearLevel.CRITICAL:
            urgency = "IMMEDIATE"
            action = "Replace drive immediately and backup all data"
            monitoring = "Daily"
            backup_priority = "CRITICAL"
            failure_timeframe = "Within 30 days"
        elif risk_score >= 60 or lifetime_analysis.wear_level == WearLevel.HIGH:
            urgency = "HIGH"
            action = "Plan replacement within 3 months"
            monitoring = "Weekly"
            backup_priority = "HIGH"
            failure_timeframe = "Within 6 months"
        elif risk_score >= 40 or lifetime_analysis.wear_level == WearLevel.MODERATE:
            urgency = "MODERATE"
            action = "Plan replacement within 12 months"
            monitoring = "Bi-weekly"
            backup_priority = "MEDIUM"
            failure_timeframe = "Within 2 years"
        elif risk_score >= 20 or lifetime_analysis.wear_level == WearLevel.GOOD:
            urgency = "LOW"
            action = "Continue monitoring, no immediate action needed"
            monitoring = "Monthly"
            backup_priority = "NORMAL"
            failure_timeframe = "More than 2 years"
        else:
            urgency = "NONE"
            action = "Drive is in excellent condition"
            monitoring = "Quarterly"
            backup_priority = "NORMAL"
            failure_timeframe = "More than 5 years"
        
        return PredictiveAnalysis(
            replacement_urgency=urgency,
            recommended_action=action,
            monitoring_frequency=monitoring,
            backup_priority=backup_priority,
            failure_risk_score=risk_score,
            predicted_failure_timeframe=failure_timeframe
        )

    def _generate_recommendations(self, wear_metrics: WearMetrics,
                                lifetime_analysis: LifetimeAnalysis,
                                predictive_analysis: PredictiveAnalysis) -> List[str]:
        """Generate actionable recommendations."""
        
        recommendations = []
        
        if lifetime_analysis.wear_level == WearLevel.CRITICAL:
            recommendations.append("URGENT: Replace drive immediately - end of life reached")
            recommendations.append("Perform immediate backup of all critical data")
        elif lifetime_analysis.wear_level == WearLevel.HIGH:
            recommendations.append("Plan drive replacement within 3-6 months")
            recommendations.append("Increase backup frequency to daily")
        elif lifetime_analysis.wear_level == WearLevel.MODERATE:
            recommendations.append("Monitor drive health weekly")
            recommendations.append("Plan for replacement within 12 months")
        
        if wear_metrics.available_spare < wear_metrics.available_spare_threshold:
            recommendations.append("Available spare below threshold - drive may fail soon")
        elif wear_metrics.available_spare < 20:
            recommendations.append("Available spare getting low - monitor closely")
        
        if lifetime_analysis.write_amplification_factor and lifetime_analysis.write_amplification_factor > 3:
            recommendations.append("High write amplification detected - optimize write patterns")
            recommendations.append("Consider enabling compression or deduplication")
        
        if wear_metrics.unsafe_shutdowns > wear_metrics.power_cycles * 0.05:
            recommendations.append("High unsafe shutdown rate - check power supply stability")
            recommendations.append("Consider UPS installation for power protection")
        
        if wear_metrics.percentage_used > 50:  # Get from temperature analysis
            recommendations.append("Monitor temperature closely as drive ages")
            recommendations.append("Ensure adequate cooling and airflow")
        
        if lifetime_analysis.endurance_consumption_percent and lifetime_analysis.endurance_consumption_percent > 80:
            recommendations.append("Drive approaching endurance limit")
            recommendations.append("Reduce write-intensive workloads if possible")
        
        if not recommendations:
            recommendations.append("Drive is in good condition - continue regular monitoring")
            recommendations.append("Maintain current backup schedule")
        
        return recommendations

    def display_wear_report(self, analysis: ComprehensiveWearAnalysis) -> None:
        """Display comprehensive wear and lifetime analysis report."""
        
        print("\n" + "="*100)
        print("⏱️  NVMe SSD LIFETIME & WEAR ANALYSIS REPORT")
        print("="*100)
        
        print(f"\n🔧 DEVICE: {analysis.device_path}")
        print(f"📱 MODEL: {analysis.device_model}")
        print(f"🔢 SERIAL: {analysis.device_serial}")
        print(f"📅 ANALYSIS TIME: {analysis.analysis_timestamp}")
        
        wear_emoji = {
            WearLevel.EXCELLENT: "🟢",
            WearLevel.GOOD: "🟡",
            WearLevel.MODERATE: "🟠",
            WearLevel.HIGH: "🔴",
            WearLevel.CRITICAL: "💀"
        }
        
        print(f"\n📊 WEAR LEVEL: {wear_emoji[analysis.lifetime_analysis.wear_level]} {analysis.lifetime_analysis.wear_level.value}")
        print(f"📈 PERCENTAGE USED: {analysis.wear_metrics.percentage_used}%")
        print(f"🔋 AVAILABLE SPARE: {analysis.wear_metrics.available_spare}%")
        
        print(f"\n⏳ LIFETIME ANALYSIS")
        print("-" * 50)
        if analysis.lifetime_analysis.estimated_remaining_life_years:
            print(f"Estimated Remaining Life: {analysis.lifetime_analysis.estimated_remaining_life_years:.1f} years")
            print(f"                         ({analysis.lifetime_analysis.estimated_remaining_life_days:,} days)")
        else:
            print("Estimated Remaining Life: Unable to calculate")
        
        print(f"Daily Wear Rate:         {analysis.lifetime_analysis.daily_wear_rate:.4f}%/day")
        print(f"Monthly Wear Rate:       {analysis.lifetime_analysis.monthly_wear_rate:.2f}%/month")
        print(f"Yearly Wear Rate:        {analysis.lifetime_analysis.yearly_wear_rate:.1f}%/year")
        
        print(f"\n📊 USAGE STATISTICS")
        print("-" * 50)
        print(f"Power-On Hours:          {analysis.wear_metrics.power_on_hours:,} hours ({analysis.power_analysis.power_on_years:.1f} years)")
        print(f"Power Cycles:            {analysis.wear_metrics.power_cycles:,}")
        print(f"Unsafe Shutdowns:        {analysis.wear_metrics.unsafe_shutdowns:,} ({analysis.power_analysis.unsafe_shutdown_rate:.1f}%)")
        print(f"Average Daily Hours:     {analysis.power_analysis.average_daily_hours:.1f} hours/day")
        print(f"Power Cycle Frequency:   {analysis.power_analysis.power_cycle_frequency:.1f} cycles/day")
        
        print(f"\n💾 DATA TRANSFER STATISTICS")
        print("-" * 50)
        print(f"Total Data Written:      {analysis.lifetime_analysis.total_bytes_written / (1024**4):.2f} TB")
        print(f"Total Data Read:         {analysis.lifetime_analysis.total_bytes_read / (1024**4):.2f} TB")
        print(f"Actual TBW:              {analysis.lifetime_analysis.actual_tbw:.2f} TB")
        
        if analysis.lifetime_analysis.endurance_rating_tbw:
            print(f"Estimated Endurance:     {analysis.lifetime_analysis.endurance_rating_tbw:.1f} TBW")
            if analysis.lifetime_analysis.endurance_consumption_percent:
                print(f"Endurance Consumption:   {analysis.lifetime_analysis.endurance_consumption_percent:.1f}%")
        
        if analysis.lifetime_analysis.write_amplification_factor:
            print(f"Write Amplification:     {analysis.lifetime_analysis.write_amplification_factor:.2f}x")
        
        print(f"\n🌡️  TEMPERATURE ANALYSIS")
        print("-" * 50)
        print(f"Current Temperature:     {analysis.temperature_analysis.current_temperature}°C")
        print(f"Maximum Temperature:     {analysis.temperature_analysis.max_temperature}°C")
        print(f"Thermal Stress Level:    {analysis.temperature_analysis.thermal_stress_level}")
        print(f"Temperature Impact:      {analysis.temperature_analysis.temperature_impact_factor:.1f}x wear rate")
        
        print(f"\n🚨 ERROR STATISTICS")
        print("-" * 50)
        print(f"Media Errors:            {analysis.wear_metrics.media_errors:,}")
        print(f"Error Log Entries:       {analysis.wear_metrics.error_log_entries:,}")
        
        print(f"\n🔮 PREDICTIVE ANALYSIS")
        print("-" * 50)
        print(f"Failure Risk Score:      {analysis.predictive_analysis.failure_risk_score}/100")
        print(f"Replacement Urgency:     {analysis.predictive_analysis.replacement_urgency}")
        print(f"Predicted Failure:       {analysis.predictive_analysis.predicted_failure_timeframe}")
        print(f"Monitoring Frequency:    {analysis.predictive_analysis.monitoring_frequency}")
        print(f"Backup Priority:         {analysis.predictive_analysis.backup_priority}")
        
        if analysis.recommendations:
            print(f"\n💡 RECOMMENDATIONS")
            print("-" * 50)
            for i, rec in enumerate(analysis.recommendations, 1):
                print(f"{i:2d}. {rec}")
        
        print(f"\n🎯 RECOMMENDED ACTION")
        print("-" * 50)
        print(f"{analysis.predictive_analysis.recommended_action}")
        
        print("="*100)

    def export_analysis_results(self, analysis: ComprehensiveWearAnalysis, filename: str) -> None:
        """Export analysis results to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(asdict(analysis), f, indent=2, default=str)
            print(f"✅ Analysis results exported to: {filename}")
        except Exception as e:
            print(f"❌ Failed to export results: {e}")


def analyze_single_device(device_path: str, export_json: bool = False) -> None:
    """Analyze lifetime and wear for a single device."""
    analyzer = NVMeLifetimeAnalyzer()
    
    try:
        analysis = analyzer.analyze_device_lifetime(device_path)
        analyzer.display_wear_report(analysis)
        
        if export_json:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            device_name = device_path.replace('/', '_')
            filename = f"nvme_wear_analysis_{device_name}_{timestamp}.json"
            analyzer.export_analysis_results(analysis, filename)
            
    except NVMeDeviceNotFoundError:
        print(f"❌ Device not found: {device_path}")
    except NVMePermissionError:
        print(f"❌ Permission denied accessing {device_path}")
        print("Try running with sudo or ensure user is in nvme group")
    except Exception as e:
        print(f"❌ Error analyzing device: {e}")


def analyze_all_devices(export_json: bool = False) -> None:
    """Analyze lifetime and wear for all devices."""
    print("🔍 Discovering NVMe devices...")
    
    try:
        devices = list_nvme_devices()
        if not devices:
            print("❌ No NVMe devices found in the system")
            return
        
        print(f"✅ Found {len(devices)} NVMe device(s)")
        
        analyzer = NVMeLifetimeAnalyzer()
        
        for i, device in enumerate(devices, 1):
            device_path = device['device_path']
            print(f"\n{'='*80}")
            print(f"⏱️  ANALYZING DEVICE {i}/{len(devices)}: {device_path}")
            print('='*80)
            
            try:
                analysis = analyzer.analyze_device_lifetime(device_path)
                analyzer.display_wear_report(analysis)
                
                if export_json:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    device_name = device_path.replace('/', '_')
                    filename = f"nvme_wear_analysis_{device_name}_{timestamp}.json"
                    analyzer.export_analysis_results(analysis, filename)
                    
            except Exception as e:
                print(f"❌ Failed to analyze {device_path}: {e}")
        
    except Exception as e:
        print(f"❌ Error discovering devices: {e}")


def main():
    """Main entry point for lifetime and wear analyzer."""
    print("⏱️  NVMe SSD Lifetime & Wear Status Analyzer")
    print("="*60)
    
    if not check_nvme_cli_availability():
        print("❌ nvme-cli not available. Please install:")
        print("   Ubuntu/Debian: sudo apt install nvme-cli")
        print("   RHEL/CentOS: sudo yum install nvme-cli")
        return 1
    
    export_json = "--json" in sys.argv or "-j" in sys.argv
    
    device_args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
    
    if device_args:
        device_path = device_args[0]
        print(f"Analyzing specific device: {device_path}")
        analyze_single_device(device_path, export_json)
    else:
        print("Analyzing all NVMe devices in system...")
        analyze_all_devices(export_json)
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Analysis cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
