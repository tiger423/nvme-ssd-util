#!/usr/bin/env python3
"""
NVMe SSD Write Amplification Factor (WAF) Calculator

This example demonstrates how to calculate and analyze the Write Amplification Factor
for NVMe SSDs, providing insights into write efficiency and optimization opportunities.

WAF CALCULATION WORKFLOW:
┌─────────────────────────────────────────────────────────────────┐
│ SMART Data Collection → Host Writes Analysis → NAND Writes     │
│ Analysis → WAF Calculation → Trend Analysis → Optimization     │
│ Recommendations → Performance Impact Assessment                 │
└─────────────────────────────────────────────────────────────────┘

WRITE AMPLIFICATION ANALYSIS:
📊 WAF Calculation (NAND writes / Host writes)
📈 Write Pattern Analysis (sequential vs random)
🔄 Garbage Collection Impact Assessment
💾 Over-provisioning Efficiency Analysis
🗂️  File System Impact Evaluation
⚡ Performance Impact Assessment
📉 Optimization Recommendations

WAF INTERPRETATION:
- WAF = 1.0: Perfect (theoretical minimum)
- WAF = 1.0-2.0: Excellent (well-optimized workload)
- WAF = 2.0-3.0: Good (typical for most workloads)
- WAF = 3.0-5.0: Moderate (room for optimization)
- WAF = 5.0+: High (significant optimization needed)

FACTORS AFFECTING WAF:
🔹 Write Pattern (sequential vs random)
🔹 Block Size Alignment
🔹 Over-provisioning Level
🔹 Garbage Collection Efficiency
🔹 File System Type and Settings
🔹 Application Write Behavior
🔹 Drive Utilization Level
🔹 TRIM/Discard Support

For technical documentation:
- Function reference: ../docs/FUNCTION_REFERENCE.md
- Integration patterns: ../docs/NVME_FORMAT_CODE_FLOW.md
"""

import sys
import json
import time
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


class WAFLevel(Enum):
    """WAF performance levels."""
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class WriteMetrics:
    """Core write-related metrics."""
    host_writes: int
    host_write_commands: int
    data_units_written: int
    nand_bytes_written: int
    total_lbas_written: int
    write_commands_total: int
    timestamp: str


@dataclass
class WAFCalculation:
    """Write Amplification Factor calculation results."""
    current_waf: float
    waf_level: WAFLevel
    host_writes_tb: float
    nand_writes_tb: float
    amplification_bytes: int
    efficiency_percentage: float
    calculation_method: str
    confidence_level: str


@dataclass
class WritePatternAnalysis:
    """Analysis of write patterns and their impact on WAF."""
    average_write_size: float
    write_command_frequency: float
    sequential_write_ratio: float
    random_write_ratio: float
    small_write_penalty: float
    alignment_efficiency: float


@dataclass
class GarbageCollectionAnalysis:
    """Garbage collection impact analysis."""
    gc_efficiency_score: int
    over_provisioning_ratio: float
    free_space_ratio: float
    gc_triggered_writes: int
    gc_impact_on_waf: float


@dataclass
class OptimizationRecommendations:
    """WAF optimization recommendations."""
    primary_recommendations: List[str]
    file_system_optimizations: List[str]
    application_optimizations: List[str]
    hardware_optimizations: List[str]
    expected_waf_improvement: float


@dataclass
class PerformanceImpact:
    """Performance impact of current WAF."""
    write_performance_penalty: float
    endurance_impact: float
    power_consumption_increase: float
    thermal_impact: float
    cost_of_amplification: float


@dataclass
class WAFTrendAnalysis:
    """WAF trend analysis over time."""
    trend_direction: str
    trend_rate: float
    historical_waf_values: List[Tuple[str, float]]
    prediction_30_days: Optional[float]
    prediction_90_days: Optional[float]


@dataclass
class ComprehensiveWAFAnalysis:
    """Complete WAF analysis results."""
    device_path: str
    device_model: str
    device_serial: str
    analysis_timestamp: str
    write_metrics: WriteMetrics
    waf_calculation: WAFCalculation
    write_pattern_analysis: WritePatternAnalysis
    gc_analysis: GarbageCollectionAnalysis
    performance_impact: PerformanceImpact
    optimization_recommendations: OptimizationRecommendations
    trend_analysis: Optional[WAFTrendAnalysis]
    raw_smart_data: Dict[str, Any]


class NVMeWAFCalculator:
    """Comprehensive NVMe Write Amplification Factor calculator and analyzer."""
    
    def __init__(self):
        """Initialize the WAF calculator."""
        self.logger = setup_logging("INFO")
        
        self.waf_thresholds = {
            WAFLevel.EXCELLENT: (1.0, 2.0),
            WAFLevel.GOOD: (2.0, 3.0),
            WAFLevel.MODERATE: (3.0, 5.0),
            WAFLevel.HIGH: (5.0, 8.0),
            WAFLevel.CRITICAL: (8.0, float('inf'))
        }
        
        self.historical_data: Dict[str, List[Tuple[str, Dict]]] = {}

    def calculate_waf(self, device_path: str, monitoring_duration: int = 0) -> ComprehensiveWAFAnalysis:
        """
        Calculate comprehensive Write Amplification Factor analysis.
        
        This function performs detailed WAF calculation and analysis:
        1. Collect current SMART write metrics
        2. Calculate WAF using multiple methods
        3. Analyze write patterns and their impact
        4. Assess garbage collection efficiency
        5. Evaluate performance impact
        6. Generate optimization recommendations
        7. Perform trend analysis if historical data available
        
        Args:
            device_path: NVMe device path (e.g., "/dev/nvme0")
            monitoring_duration: Duration in seconds for real-time monitoring (0 = snapshot)
            
        Returns:
            ComprehensiveWAFAnalysis: Complete WAF analysis
            
        Raises:
            NVMeDeviceNotFoundError: Device not found
            NVMeCommandError: Failed to collect device data
        """
        print(f"🔍 Calculating WAF for {device_path}...")
        
        if monitoring_duration > 0:
            print(f"📊 Monitoring writes for {monitoring_duration} seconds...")
            return self._calculate_waf_with_monitoring(device_path, monitoring_duration)
        else:
            return self._calculate_waf_snapshot(device_path)

    def _calculate_waf_snapshot(self, device_path: str) -> ComprehensiveWAFAnalysis:
        """Calculate WAF from current SMART data snapshot."""
        
        smart_data = get_smart_log(device_path)
        device_info = get_controller_info(device_path)
        
        device_model = device_info.get('mn', 'Unknown').strip()
        device_serial = device_info.get('sn', 'Unknown').strip()
        
        write_metrics = self._parse_write_metrics(smart_data)
        
        waf_calculation = self._calculate_waf_from_metrics(write_metrics, smart_data)
        
        write_pattern_analysis = self._analyze_write_patterns(smart_data, device_info)
        
        gc_analysis = self._analyze_garbage_collection(smart_data, device_info)
        
        performance_impact = self._assess_performance_impact(waf_calculation, write_pattern_analysis)
        
        optimization_recommendations = self._generate_optimization_recommendations(
            waf_calculation, write_pattern_analysis, gc_analysis
        )
        
        trend_analysis = self._analyze_waf_trends(device_path, waf_calculation.current_waf)
        
        return ComprehensiveWAFAnalysis(
            device_path=device_path,
            device_model=device_model,
            device_serial=device_serial,
            analysis_timestamp=datetime.now().isoformat(),
            write_metrics=write_metrics,
            waf_calculation=waf_calculation,
            write_pattern_analysis=write_pattern_analysis,
            gc_analysis=gc_analysis,
            performance_impact=performance_impact,
            optimization_recommendations=optimization_recommendations,
            trend_analysis=trend_analysis,
            raw_smart_data=smart_data
        )

    def _calculate_waf_with_monitoring(self, device_path: str, duration: int) -> ComprehensiveWAFAnalysis:
        """Calculate WAF with real-time monitoring over specified duration."""
        
        print("📊 Starting baseline measurement...")
        baseline_smart = get_smart_log(device_path)
        baseline_time = time.time()
        
        print(f"⏱️  Monitoring for {duration} seconds...")
        time.sleep(duration)
        
        print("📊 Taking final measurement...")
        final_smart = get_smart_log(device_path)
        final_time = time.time()
        
        delta_time = final_time - baseline_time
        delta_host_writes = final_smart.get('host_writes', 0) - baseline_smart.get('host_writes', 0)
        delta_data_units_written = final_smart.get('data_units_written', 0) - baseline_smart.get('data_units_written', 0)
        
        write_metrics = WriteMetrics(
            host_writes=delta_host_writes,
            host_write_commands=final_smart.get('host_write_commands', 0) - baseline_smart.get('host_write_commands', 0),
            data_units_written=delta_data_units_written,
            nand_bytes_written=delta_data_units_written * 1000 * 512,  # Convert to bytes
            total_lbas_written=delta_host_writes // 512,  # Estimate LBAs
            write_commands_total=final_smart.get('write_commands', 0) - baseline_smart.get('write_commands', 0),
            timestamp=datetime.now().isoformat()
        )
        
        if delta_host_writes > 0 and delta_data_units_written > 0:
            host_bytes = delta_host_writes
            nand_bytes = delta_data_units_written * 1000 * 512
            current_waf = nand_bytes / host_bytes if host_bytes > 0 else 0
            
            waf_calculation = WAFCalculation(
                current_waf=current_waf,
                waf_level=self._determine_waf_level(current_waf),
                host_writes_tb=host_bytes / (1024**4),
                nand_writes_tb=nand_bytes / (1024**4),
                amplification_bytes=nand_bytes - host_bytes,
                efficiency_percentage=(host_bytes / nand_bytes * 100) if nand_bytes > 0 else 0,
                calculation_method="Real-time monitoring",
                confidence_level="High"
            )
        else:
            print("⚠️  No writes detected during monitoring period, using snapshot method")
            return self._calculate_waf_snapshot(device_path)
        
        device_info = get_controller_info(device_path)
        device_model = device_info.get('mn', 'Unknown').strip()
        device_serial = device_info.get('sn', 'Unknown').strip()
        
        write_pattern_analysis = self._analyze_write_patterns(final_smart, device_info)
        gc_analysis = self._analyze_garbage_collection(final_smart, device_info)
        performance_impact = self._assess_performance_impact(waf_calculation, write_pattern_analysis)
        optimization_recommendations = self._generate_optimization_recommendations(
            waf_calculation, write_pattern_analysis, gc_analysis
        )
        trend_analysis = self._analyze_waf_trends(device_path, waf_calculation.current_waf)
        
        return ComprehensiveWAFAnalysis(
            device_path=device_path,
            device_model=device_model,
            device_serial=device_serial,
            analysis_timestamp=datetime.now().isoformat(),
            write_metrics=write_metrics,
            waf_calculation=waf_calculation,
            write_pattern_analysis=write_pattern_analysis,
            gc_analysis=gc_analysis,
            performance_impact=performance_impact,
            optimization_recommendations=optimization_recommendations,
            trend_analysis=trend_analysis,
            raw_smart_data=final_smart
        )

    def _parse_write_metrics(self, smart_data: Dict) -> WriteMetrics:
        """Parse write-related metrics from SMART data."""
        
        host_writes = smart_data.get('host_writes', 0)
        data_units_written = smart_data.get('data_units_written', 0)
        
        nand_bytes_written = data_units_written * 1000 * 512
        
        return WriteMetrics(
            host_writes=host_writes,
            host_write_commands=smart_data.get('host_write_commands', 0),
            data_units_written=data_units_written,
            nand_bytes_written=nand_bytes_written,
            total_lbas_written=smart_data.get('total_lbas_written', 0),
            write_commands_total=smart_data.get('write_commands', 0),
            timestamp=datetime.now().isoformat()
        )

    def _calculate_waf_from_metrics(self, write_metrics: WriteMetrics, smart_data: Dict) -> WAFCalculation:
        """Calculate WAF from write metrics."""
        
        if write_metrics.host_writes > 0 and write_metrics.nand_bytes_written > 0:
            current_waf = write_metrics.nand_bytes_written / write_metrics.host_writes
            calculation_method = "SMART data analysis"
            confidence_level = "Medium"
        elif write_metrics.host_writes > 0 and write_metrics.data_units_written > 0:
            nand_bytes = write_metrics.data_units_written * 1000 * 512
            current_waf = nand_bytes / write_metrics.host_writes
            calculation_method = "Data units estimation"
            confidence_level = "Low"
        else:
            current_waf = 2.5  # Typical WAF for consumer SSDs
            calculation_method = "Industry average estimation"
            confidence_level = "Very Low"
        
        waf_level = self._determine_waf_level(current_waf)
        
        host_writes_tb = write_metrics.host_writes / (1024**4)
        nand_writes_tb = write_metrics.nand_bytes_written / (1024**4)
        amplification_bytes = write_metrics.nand_bytes_written - write_metrics.host_writes
        efficiency_percentage = (write_metrics.host_writes / write_metrics.nand_bytes_written * 100) if write_metrics.nand_bytes_written > 0 else 0
        
        return WAFCalculation(
            current_waf=current_waf,
            waf_level=waf_level,
            host_writes_tb=host_writes_tb,
            nand_writes_tb=nand_writes_tb,
            amplification_bytes=amplification_bytes,
            efficiency_percentage=efficiency_percentage,
            calculation_method=calculation_method,
            confidence_level=confidence_level
        )

    def _determine_waf_level(self, waf: float) -> WAFLevel:
        """Determine WAF performance level."""
        for level, (min_waf, max_waf) in self.waf_thresholds.items():
            if min_waf <= waf < max_waf:
                return level
        return WAFLevel.CRITICAL

    def _analyze_write_patterns(self, smart_data: Dict, device_info: Dict) -> WritePatternAnalysis:
        """Analyze write patterns and their impact on WAF."""
        
        host_writes = smart_data.get('host_writes', 0)
        write_commands = smart_data.get('host_write_commands', 0)
        
        if write_commands > 0:
            average_write_size = host_writes / write_commands
        else:
            average_write_size = 4096  # Default assumption
        
        power_on_hours = smart_data.get('power_on_hours', 1)
        write_command_frequency = write_commands / (power_on_hours * 3600) if power_on_hours > 0 else 0
        
        if average_write_size > 64 * 1024:  # Large writes likely sequential
            sequential_write_ratio = 0.8
            random_write_ratio = 0.2
        elif average_write_size > 16 * 1024:  # Medium writes mixed
            sequential_write_ratio = 0.5
            random_write_ratio = 0.5
        else:  # Small writes likely random
            sequential_write_ratio = 0.2
            random_write_ratio = 0.8
        
        small_write_penalty = max(0, (4096 - average_write_size) / 4096 * 2)
        
        alignment_efficiency = 0.9 if average_write_size % 4096 == 0 else 0.7
        
        return WritePatternAnalysis(
            average_write_size=average_write_size,
            write_command_frequency=write_command_frequency,
            sequential_write_ratio=sequential_write_ratio,
            random_write_ratio=random_write_ratio,
            small_write_penalty=small_write_penalty,
            alignment_efficiency=alignment_efficiency
        )

    def _analyze_garbage_collection(self, smart_data: Dict, device_info: Dict) -> GarbageCollectionAnalysis:
        """Analyze garbage collection efficiency and impact."""
        
        total_capacity = device_info.get('tnvmcap', 0)
        user_capacity = device_info.get('unvmcap', total_capacity)
        
        if total_capacity > 0:
            over_provisioning_ratio = ((total_capacity - user_capacity) / user_capacity) * 100
        else:
            over_provisioning_ratio = 7.0  # Typical OP for consumer SSDs
        
        percentage_used = smart_data.get('percentage_used', 0)
        free_space_ratio = max(0, 100 - percentage_used - over_provisioning_ratio)
        
        gc_efficiency_score = 100
        if over_provisioning_ratio < 5:
            gc_efficiency_score -= 20
        if free_space_ratio < 10:
            gc_efficiency_score -= 30
        if percentage_used > 80:
            gc_efficiency_score -= 25
        
        gc_efficiency_score = max(0, gc_efficiency_score)
        
        data_units_written = smart_data.get('data_units_written', 0)
        host_writes = smart_data.get('host_writes', 0)
        
        if host_writes > 0:
            gc_triggered_writes = max(0, data_units_written * 1000 * 512 - host_writes)
        else:
            gc_triggered_writes = 0
        
        gc_impact_on_waf = (100 - gc_efficiency_score) / 100 * 2  # Max 2x impact
        
        return GarbageCollectionAnalysis(
            gc_efficiency_score=gc_efficiency_score,
            over_provisioning_ratio=over_provisioning_ratio,
            free_space_ratio=free_space_ratio,
            gc_triggered_writes=gc_triggered_writes,
            gc_impact_on_waf=gc_impact_on_waf
        )

    def _assess_performance_impact(self, waf_calculation: WAFCalculation, 
                                 write_pattern_analysis: WritePatternAnalysis) -> PerformanceImpact:
        """Assess performance impact of current WAF."""
        
        base_penalty = (waf_calculation.current_waf - 1.0) * 20  # 20% penalty per WAF point
        pattern_penalty = write_pattern_analysis.small_write_penalty * 10
        write_performance_penalty = min(80, base_penalty + pattern_penalty)
        
        endurance_impact = (waf_calculation.current_waf - 1.0) * 100  # Direct correlation
        
        power_consumption_increase = (waf_calculation.current_waf - 1.0) * 15  # 15% per WAF point
        
        thermal_impact = write_performance_penalty * 0.3  # Thermal follows performance
        
        cost_of_amplification = waf_calculation.amplification_bytes / (1024**3)  # GB of extra writes
        
        return PerformanceImpact(
            write_performance_penalty=write_performance_penalty,
            endurance_impact=endurance_impact,
            power_consumption_increase=power_consumption_increase,
            thermal_impact=thermal_impact,
            cost_of_amplification=cost_of_amplification
        )

    def _generate_optimization_recommendations(self, waf_calculation: WAFCalculation,
                                             write_pattern_analysis: WritePatternAnalysis,
                                             gc_analysis: GarbageCollectionAnalysis) -> OptimizationRecommendations:
        """Generate WAF optimization recommendations."""
        
        primary_recommendations = []
        file_system_optimizations = []
        application_optimizations = []
        hardware_optimizations = []
        
        if waf_calculation.waf_level in [WAFLevel.HIGH, WAFLevel.CRITICAL]:
            primary_recommendations.extend([
                "URGENT: WAF is critically high - immediate optimization required",
                "Analyze and optimize write patterns in applications",
                "Consider workload redistribution to reduce write intensity"
            ])
        elif waf_calculation.waf_level == WAFLevel.MODERATE:
            primary_recommendations.extend([
                "WAF has room for improvement - consider optimization",
                "Monitor write patterns and identify optimization opportunities"
            ])
        
        if write_pattern_analysis.small_write_penalty > 1.0:
            file_system_optimizations.extend([
                "Enable write coalescing in file system",
                "Increase file system block size to match SSD page size",
                "Configure file system for SSD optimization (noatime, etc.)"
            ])
        
        if write_pattern_analysis.alignment_efficiency < 0.8:
            file_system_optimizations.append("Ensure proper partition alignment (4KB boundaries)")
        
        if write_pattern_analysis.random_write_ratio > 0.6:
            application_optimizations.extend([
                "Optimize applications to use larger, sequential writes",
                "Implement write buffering and batching",
                "Consider using memory-mapped files for small writes"
            ])
        
        if write_pattern_analysis.write_command_frequency > 1000:  # High frequency
            application_optimizations.extend([
                "Reduce write frequency through batching",
                "Implement write-back caching where appropriate"
            ])
        
        if gc_analysis.over_provisioning_ratio < 10:
            hardware_optimizations.extend([
                "Consider drive with higher over-provisioning",
                "Leave 10-20% of drive capacity unallocated"
            ])
        
        if gc_analysis.free_space_ratio < 20:
            hardware_optimizations.extend([
                "Maintain at least 20% free space for optimal performance",
                "Consider drive capacity upgrade"
            ])
        
        expected_improvement = 0
        if len(primary_recommendations) > 0:
            expected_improvement += 1.0
        if len(file_system_optimizations) > 0:
            expected_improvement += 0.5
        if len(application_optimizations) > 0:
            expected_improvement += 0.8
        if len(hardware_optimizations) > 0:
            expected_improvement += 0.3
        
        return OptimizationRecommendations(
            primary_recommendations=primary_recommendations,
            file_system_optimizations=file_system_optimizations,
            application_optimizations=application_optimizations,
            hardware_optimizations=hardware_optimizations,
            expected_waf_improvement=min(expected_improvement, waf_calculation.current_waf - 1.0)
        )

    def _analyze_waf_trends(self, device_path: str, current_waf: float) -> Optional[WAFTrendAnalysis]:
        """Analyze WAF trends over time."""
        
        device_key = device_path.replace('/', '_')
        timestamp = datetime.now().isoformat()
        
        if device_key not in self.historical_data:
            self.historical_data[device_key] = []
        
        self.historical_data[device_key].append((timestamp, current_waf))
        
        self.historical_data[device_key] = self.historical_data[device_key][-30:]
        
        if len(self.historical_data[device_key]) < 3:
            return None
        
        historical_values = [(ts, waf) for ts, waf in self.historical_data[device_key]]
        waf_values = [waf for _, waf in historical_values]
        
        if len(waf_values) >= 2:
            recent_avg = sum(waf_values[-3:]) / len(waf_values[-3:])
            older_avg = sum(waf_values[:-3]) / len(waf_values[:-3]) if len(waf_values) > 3 else recent_avg
            
            trend_rate = (recent_avg - older_avg) / len(waf_values) * 30  # Monthly rate
            
            if trend_rate > 0.1:
                trend_direction = "Increasing"
            elif trend_rate < -0.1:
                trend_direction = "Decreasing"
            else:
                trend_direction = "Stable"
        else:
            trend_direction = "Insufficient data"
            trend_rate = 0
        
        prediction_30_days = current_waf + trend_rate if trend_rate != 0 else None
        prediction_90_days = current_waf + (trend_rate * 3) if trend_rate != 0 else None
        
        return WAFTrendAnalysis(
            trend_direction=trend_direction,
            trend_rate=trend_rate,
            historical_waf_values=historical_values,
            prediction_30_days=prediction_30_days,
            prediction_90_days=prediction_90_days
        )

    def display_waf_report(self, analysis: ComprehensiveWAFAnalysis) -> None:
        """Display comprehensive WAF analysis report."""
        
        print("\n" + "="*100)
        print("📊 NVMe SSD WRITE AMPLIFICATION FACTOR (WAF) ANALYSIS REPORT")
        print("="*100)
        
        print(f"\n🔧 DEVICE: {analysis.device_path}")
        print(f"📱 MODEL: {analysis.device_model}")
        print(f"🔢 SERIAL: {analysis.device_serial}")
        print(f"📅 ANALYSIS TIME: {analysis.analysis_timestamp}")
        
        waf_emoji = {
            WAFLevel.EXCELLENT: "🟢",
            WAFLevel.GOOD: "🟡",
            WAFLevel.MODERATE: "🟠",
            WAFLevel.HIGH: "🔴",
            WAFLevel.CRITICAL: "💀"
        }
        
        print(f"\n📊 WRITE AMPLIFICATION FACTOR")
        print("-" * 50)
        print(f"Current WAF:             {waf_emoji[analysis.waf_calculation.waf_level]} {analysis.waf_calculation.current_waf:.2f}x")
        print(f"WAF Level:               {analysis.waf_calculation.waf_level.value}")
        print(f"Write Efficiency:        {analysis.waf_calculation.efficiency_percentage:.1f}%")
        print(f"Calculation Method:      {analysis.waf_calculation.calculation_method}")
        print(f"Confidence Level:        {analysis.waf_calculation.confidence_level}")
        
        print(f"\n💾 WRITE STATISTICS")
        print("-" * 50)
        print(f"Host Writes:             {analysis.waf_calculation.host_writes_tb:.3f} TB")
        print(f"NAND Writes:             {analysis.waf_calculation.nand_writes_tb:.3f} TB")
        print(f"Amplification Overhead:  {analysis.waf_calculation.amplification_bytes / (1024**3):.2f} GB")
        print(f"Total Write Commands:    {analysis.write_metrics.write_commands_total:,}")
        
        print(f"\n📈 WRITE PATTERN ANALYSIS")
        print("-" * 50)
        print(f"Average Write Size:      {analysis.write_pattern_analysis.average_write_size:.0f} bytes")
        print(f"Write Command Frequency: {analysis.write_pattern_analysis.write_command_frequency:.2f} commands/sec")
        print(f"Sequential Writes:       {analysis.write_pattern_analysis.sequential_write_ratio:.1%}")
        print(f"Random Writes:           {analysis.write_pattern_analysis.random_write_ratio:.1%}")
        print(f"Small Write Penalty:     {analysis.write_pattern_analysis.small_write_penalty:.2f}x")
        print(f"Alignment Efficiency:    {analysis.write_pattern_analysis.alignment_efficiency:.1%}")
        
        print(f"\n🗑️  GARBAGE COLLECTION ANALYSIS")
        print("-" * 50)
        print(f"GC Efficiency Score:     {analysis.gc_analysis.gc_efficiency_score}/100")
        print(f"Over-Provisioning:       {analysis.gc_analysis.over_provisioning_ratio:.1f}%")
        print(f"Free Space Ratio:        {analysis.gc_analysis.free_space_ratio:.1f}%")
        print(f"GC-Triggered Writes:     {analysis.gc_analysis.gc_triggered_writes / (1024**3):.2f} GB")
        print(f"GC Impact on WAF:        +{analysis.gc_analysis.gc_impact_on_waf:.2f}x")
        
        print(f"\n⚡ PERFORMANCE IMPACT")
        print("-" * 50)
        print(f"Write Performance Loss:  {analysis.performance_impact.write_performance_penalty:.1f}%")
        print(f"Endurance Impact:        {analysis.performance_impact.endurance_impact:.1f}% faster wear")
        print(f"Power Consumption:       +{analysis.performance_impact.power_consumption_increase:.1f}%")
        print(f"Thermal Impact:          +{analysis.performance_impact.thermal_impact:.1f}°C estimated")
        print(f"Wasted Write Capacity:   {analysis.performance_impact.cost_of_amplification:.2f} GB")
        
        if analysis.trend_analysis:
            print(f"\n📊 TREND ANALYSIS")
            print("-" * 50)
            print(f"Trend Direction:         {analysis.trend_analysis.trend_direction}")
            print(f"Trend Rate:              {analysis.trend_analysis.trend_rate:.3f}/month")
            if analysis.trend_analysis.prediction_30_days:
                print(f"30-Day Prediction:       {analysis.trend_analysis.prediction_30_days:.2f}x")
            if analysis.trend_analysis.prediction_90_days:
                print(f"90-Day Prediction:       {analysis.trend_analysis.prediction_90_days:.2f}x")
        
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS")
        print("-" * 50)
        
        if analysis.optimization_recommendations.primary_recommendations:
            print("🎯 PRIMARY ACTIONS:")
            for i, rec in enumerate(analysis.optimization_recommendations.primary_recommendations, 1):
                print(f"   {i}. {rec}")
        
        if analysis.optimization_recommendations.file_system_optimizations:
            print("\n📁 FILE SYSTEM OPTIMIZATIONS:")
            for i, rec in enumerate(analysis.optimization_recommendations.file_system_optimizations, 1):
                print(f"   {i}. {rec}")
        
        if analysis.optimization_recommendations.application_optimizations:
            print("\n💻 APPLICATION OPTIMIZATIONS:")
            for i, rec in enumerate(analysis.optimization_recommendations.application_optimizations, 1):
                print(f"   {i}. {rec}")
        
        if analysis.optimization_recommendations.hardware_optimizations:
            print("\n🔧 HARDWARE OPTIMIZATIONS:")
            for i, rec in enumerate(analysis.optimization_recommendations.hardware_optimizations, 1):
                print(f"   {i}. {rec}")
        
        if analysis.optimization_recommendations.expected_waf_improvement > 0:
            print(f"\n📈 EXPECTED IMPROVEMENT: -{analysis.optimization_recommendations.expected_waf_improvement:.2f}x WAF reduction")
        
        print("="*100)

    def export_waf_analysis(self, analysis: ComprehensiveWAFAnalysis, filename: str) -> None:
        """Export WAF analysis to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(asdict(analysis), f, indent=2, default=str)
            print(f"✅ WAF analysis exported to: {filename}")
        except Exception as e:
            print(f"❌ Failed to export analysis: {e}")


def analyze_single_device(device_path: str, monitoring_duration: int = 0, export_json: bool = False) -> None:
    """Analyze WAF for a single device."""
    calculator = NVMeWAFCalculator()
    
    try:
        analysis = calculator.calculate_waf(device_path, monitoring_duration)
        calculator.display_waf_report(analysis)
        
        if export_json:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            device_name = device_path.replace('/', '_')
            filename = f"nvme_waf_analysis_{device_name}_{timestamp}.json"
            calculator.export_waf_analysis(analysis, filename)
            
    except NVMeDeviceNotFoundError:
        print(f"❌ Device not found: {device_path}")
    except NVMePermissionError:
        print(f"❌ Permission denied accessing {device_path}")
        print("Try running with sudo or ensure user is in nvme group")
    except Exception as e:
        print(f"❌ Error analyzing device: {e}")


def analyze_all_devices(monitoring_duration: int = 0, export_json: bool = False) -> None:
    """Analyze WAF for all devices."""
    print("🔍 Discovering NVMe devices...")
    
    try:
        devices = list_nvme_devices()
        if not devices:
            print("❌ No NVMe devices found in the system")
            return
        
        print(f"✅ Found {len(devices)} NVMe device(s)")
        
        calculator = NVMeWAFCalculator()
        
        for i, device in enumerate(devices, 1):
            device_path = device['device_path']
            print(f"\n{'='*80}")
            print(f"📊 ANALYZING DEVICE {i}/{len(devices)}: {device_path}")
            print('='*80)
            
            try:
                analysis = calculator.calculate_waf(device_path, monitoring_duration)
                calculator.display_waf_report(analysis)
                
                if export_json:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    device_name = device_path.replace('/', '_')
                    filename = f"nvme_waf_analysis_{device_name}_{timestamp}.json"
                    calculator.export_waf_analysis(analysis, filename)
                    
            except Exception as e:
                print(f"❌ Failed to analyze {device_path}: {e}")
        
    except Exception as e:
        print(f"❌ Error discovering devices: {e}")


def main():
    """Main entry point for WAF calculator."""
    print("📊 NVMe SSD Write Amplification Factor (WAF) Calculator")
    print("="*70)
    
    if not check_nvme_cli_availability():
        print("❌ nvme-cli not available. Please install:")
        print("   Ubuntu/Debian: sudo apt install nvme-cli")
        print("   RHEL/CentOS: sudo yum install nvme-cli")
        return 1
    
    export_json = "--json" in sys.argv or "-j" in sys.argv
    
    monitoring_duration = 0
    for arg in sys.argv:
        if arg.startswith("--monitor="):
            try:
                monitoring_duration = int(arg.split("=")[1])
            except ValueError:
                print("❌ Invalid monitoring duration. Use --monitor=<seconds>")
                return 1
    
    device_args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
    
    if device_args:
        device_path = device_args[0]
        print(f"Analyzing specific device: {device_path}")
        if monitoring_duration > 0:
            print(f"With real-time monitoring for {monitoring_duration} seconds")
        analyze_single_device(device_path, monitoring_duration, export_json)
    else:
        print("Analyzing all NVMe devices in system...")
        if monitoring_duration > 0:
            print(f"With real-time monitoring for {monitoring_duration} seconds per device")
        analyze_all_devices(monitoring_duration, export_json)
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 WAF analysis cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
