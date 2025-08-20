"""
NVMe Health Monitor - Data Processing Module

This module handles validation, analysis, and processing of collected NVMe health data.
It provides functions for data validation, health analysis, and trend detection.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from statistics import mean, median, stdev

from ..models.health_metrics import (
    DeviceInfo,
    SMARTData,
    SystemHealthSummary,
    HealthStatus,
    ErrorLogEntry,
    SelfTestEntry,
    SelfTestResult,
    TemperatureReading
)
from ..models.exceptions import NVMeBaseException


logger = logging.getLogger(__name__)


class HealthThresholds:
    """Health threshold configuration for NVMe devices."""
    
    TEMP_WARNING = 70.0
    TEMP_CRITICAL = 85.0
    
    USAGE_WARNING = 80.0
    USAGE_CRITICAL = 95.0
    
    SPARE_WARNING = 10.0
    SPARE_CRITICAL = 5.0
    
    ERROR_WARNING = 10
    ERROR_CRITICAL = 50
    
    POWER_CYCLE_WARNING = 10000
    POWER_CYCLE_CRITICAL = 50000
    
    UNSAFE_SHUTDOWN_WARNING = 100
    UNSAFE_SHUTDOWN_CRITICAL = 500


class DataProcessor:
    """Main data processing engine for NVMe health analysis."""
    
    def __init__(self, thresholds: Optional[HealthThresholds] = None):
        """
        Initialize data processor.
        
        Args:
            thresholds: Custom health thresholds (uses defaults if None)
        """
        self.thresholds = thresholds or HealthThresholds()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_smart_data(self, smart_data: SMARTData) -> Dict[str, Any]:
        """
        Validate SMART data for consistency and completeness.
        
        Args:
            smart_data: SMART data to validate
            
        Returns:
            Dict containing validation results and issues found
        """
        self.logger.debug(f"Validating SMART data for {smart_data.device_path}")
        
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'critical_issues': []
        }
        
        if smart_data.temperature.celsius <= 0:
            validation_result['issues'].append("Invalid temperature reading")
            validation_result['valid'] = False
        
        if smart_data.available_spare < 0 or smart_data.available_spare > 100:
            validation_result['issues'].append("Invalid available spare percentage")
            validation_result['valid'] = False
        
        if smart_data.percentage_used < 0 or smart_data.percentage_used > 100:
            validation_result['issues'].append("Invalid percentage used")
            validation_result['valid'] = False
        
        if smart_data.temperature.celsius > 150:
            validation_result['warnings'].append("Extremely high temperature reading")
        
        if smart_data.power_on_hours > 100000:  # ~11 years
            validation_result['warnings'].append("Very high power-on hours")
        
        if smart_data.critical_warning > 0:
            validation_result['critical_issues'].append(f"Critical warning flags set: {smart_data.critical_warning}")
        
        if smart_data.media_errors > 0:
            validation_result['critical_issues'].append(f"Media errors detected: {smart_data.media_errors}")
        
        self.logger.debug(f"SMART validation complete: {len(validation_result['issues'])} issues, "
                         f"{len(validation_result['warnings'])} warnings")
        
        return validation_result
    
    def analyze_device_health(self, device_info: DeviceInfo) -> Dict[str, Any]:
        """
        Perform comprehensive health analysis on device data.
        
        Args:
            device_info: Complete device information
            
        Returns:
            Dict containing detailed health analysis
        """
        self.logger.info(f"Analyzing health for device {device_info.device_path}")
        
        analysis = {
            'device_path': device_info.device_path,
            'overall_status': device_info.health_status,
            'timestamp': datetime.now(),
            'smart_analysis': {},
            'error_analysis': {},
            'self_test_analysis': {},
            'recommendations': [],
            'risk_factors': [],
            'health_score': 0
        }
        
        if device_info.smart_data:
            analysis['smart_analysis'] = self._analyze_smart_data(device_info.smart_data)
        
        analysis['error_analysis'] = self._analyze_error_logs(device_info.error_log)
        
        analysis['self_test_analysis'] = self._analyze_self_test_logs(device_info.self_test_log)
        
        analysis['health_score'] = self._calculate_health_score(device_info)
        
        analysis['recommendations'] = self._generate_recommendations(device_info, analysis)
        
        analysis['risk_factors'] = self._identify_risk_factors(device_info, analysis)
        
        self.logger.info(f"Health analysis complete for {device_info.device_path}: "
                        f"Score {analysis['health_score']}/100, Status {analysis['overall_status']}")
        
        return analysis
    
    def _analyze_smart_data(self, smart_data: SMARTData) -> Dict[str, Any]:
        """Analyze SMART data for health indicators."""
        analysis = {
            'temperature_status': 'normal',
            'usage_status': 'normal',
            'spare_status': 'normal',
            'wear_level': 'normal',
            'critical_warnings': [],
            'metrics': {}
        }
        
        temp_c = smart_data.temperature.celsius
        if temp_c >= self.thresholds.TEMP_CRITICAL:
            analysis['temperature_status'] = 'critical'
        elif temp_c >= self.thresholds.TEMP_WARNING:
            analysis['temperature_status'] = 'warning'
        
        usage_pct = smart_data.percentage_used
        if usage_pct >= self.thresholds.USAGE_CRITICAL:
            analysis['usage_status'] = 'critical'
        elif usage_pct >= self.thresholds.USAGE_WARNING:
            analysis['usage_status'] = 'warning'
        
        spare_pct = smart_data.available_spare
        if spare_pct <= self.thresholds.SPARE_CRITICAL:
            analysis['spare_status'] = 'critical'
        elif spare_pct <= self.thresholds.SPARE_WARNING:
            analysis['spare_status'] = 'warning'
        
        if usage_pct > 90:
            analysis['wear_level'] = 'high'
        elif usage_pct > 70:
            analysis['wear_level'] = 'moderate'
        
        if smart_data.critical_warning & 0x01:
            analysis['critical_warnings'].append('Available spare below threshold')
        if smart_data.critical_warning & 0x02:
            analysis['critical_warnings'].append('Temperature above threshold')
        if smart_data.critical_warning & 0x04:
            analysis['critical_warnings'].append('NVM subsystem reliability degraded')
        if smart_data.critical_warning & 0x08:
            analysis['critical_warnings'].append('Media in read-only mode')
        if smart_data.critical_warning & 0x10:
            analysis['critical_warnings'].append('Volatile memory backup device failed')
        
        analysis['metrics'] = {
            'temperature_celsius': temp_c,
            'percentage_used': usage_pct,
            'available_spare': spare_pct,
            'power_on_hours': smart_data.power_on_hours,
            'power_cycles': smart_data.power_cycles,
            'unsafe_shutdowns': smart_data.unsafe_shutdowns,
            'media_errors': smart_data.media_errors,
            'error_log_entries': smart_data.error_log_entries
        }
        
        return analysis
    
    def _analyze_error_logs(self, error_logs: List[ErrorLogEntry]) -> Dict[str, Any]:
        """Analyze error log entries."""
        analysis = {
            'total_errors': len(error_logs),
            'error_status': 'normal',
            'error_types': {},
            'recent_errors': 0,
            'critical_errors': 0
        }
        
        if analysis['total_errors'] == 0:
            return analysis
        
        for error in error_logs:
            error_type = error.status_field
            if error_type not in analysis['error_types']:
                analysis['error_types'][error_type] = 0
            analysis['error_types'][error_type] += 1
        
        if analysis['total_errors'] >= self.thresholds.ERROR_CRITICAL:
            analysis['error_status'] = 'critical'
        elif analysis['total_errors'] >= self.thresholds.ERROR_WARNING:
            analysis['error_status'] = 'warning'
        
        return analysis
    
    def _analyze_self_test_logs(self, test_logs: List[SelfTestEntry]) -> Dict[str, Any]:
        """Analyze self-test log entries."""
        analysis = {
            'total_tests': len(test_logs),
            'last_test_result': 'none',
            'test_status': 'normal',
            'failed_tests': 0,
            'test_history': []
        }
        
        if analysis['total_tests'] == 0:
            return analysis
        
        latest_test = test_logs[0]  # Assuming sorted by recency
        analysis['last_test_result'] = latest_test.test_result.value
        
        failed_results = [
            SelfTestResult.UNKNOWN_TEST_ERROR,
            SelfTestResult.COMPLETED_WITH_SEGMENT_ERROR,
            SelfTestResult.FAILED_SEGMENT,
            SelfTestResult.UNKNOWN_FAILURE
        ]
        
        analysis['failed_tests'] = sum(1 for test in test_logs if test.test_result in failed_results)
        
        if analysis['failed_tests'] > 0:
            analysis['test_status'] = 'warning'
        
        for test in test_logs[:10]:  # Last 10 tests
            analysis['test_history'].append({
                'type': test.test_type.value,
                'result': test.test_result.value,
                'power_on_hours': test.power_on_hours
            })
        
        return analysis
    
    def _calculate_health_score(self, device_info: DeviceInfo) -> int:
        """Calculate overall health score (0-100)."""
        score = 100
        
        if not device_info.smart_data:
            return 50  # Unknown health
        
        smart = device_info.smart_data
        
        temp_c = smart.temperature.celsius
        if temp_c >= self.thresholds.TEMP_CRITICAL:
            score -= 30
        elif temp_c >= self.thresholds.TEMP_WARNING:
            score -= 15
        
        usage_pct = smart.percentage_used
        if usage_pct >= self.thresholds.USAGE_CRITICAL:
            score -= 25
        elif usage_pct >= self.thresholds.USAGE_WARNING:
            score -= 10
        
        spare_pct = smart.available_spare
        if spare_pct <= self.thresholds.SPARE_CRITICAL:
            score -= 25
        elif spare_pct <= self.thresholds.SPARE_WARNING:
            score -= 10
        
        if smart.media_errors > 0:
            score -= 20
        
        if len(device_info.error_log) >= self.thresholds.ERROR_CRITICAL:
            score -= 15
        elif len(device_info.error_log) >= self.thresholds.ERROR_WARNING:
            score -= 5
        
        if smart.critical_warning > 0:
            score -= 20
        
        if smart.unsafe_shutdowns >= self.thresholds.UNSAFE_SHUTDOWN_CRITICAL:
            score -= 10
        elif smart.unsafe_shutdowns >= self.thresholds.UNSAFE_SHUTDOWN_WARNING:
            score -= 5
        
        return max(0, min(100, score))
    
    def _generate_recommendations(self, device_info: DeviceInfo, analysis: Dict[str, Any]) -> List[str]:
        """Generate health recommendations."""
        recommendations = []
        
        if not device_info.smart_data:
            recommendations.append("Unable to assess device health - SMART data unavailable")
            return recommendations
        
        smart = device_info.smart_data
        
        if smart.temperature.celsius >= self.thresholds.TEMP_CRITICAL:
            recommendations.append("CRITICAL: Improve system cooling immediately - temperature too high")
        elif smart.temperature.celsius >= self.thresholds.TEMP_WARNING:
            recommendations.append("WARNING: Monitor temperature - consider improving cooling")
        
        if smart.percentage_used >= self.thresholds.USAGE_CRITICAL:
            recommendations.append("CRITICAL: Drive nearing end of life - plan replacement immediately")
        elif smart.percentage_used >= self.thresholds.USAGE_WARNING:
            recommendations.append("WARNING: Drive showing significant wear - monitor closely")
        
        if smart.available_spare <= self.thresholds.SPARE_CRITICAL:
            recommendations.append("CRITICAL: Available spare capacity very low - replace drive")
        elif smart.available_spare <= self.thresholds.SPARE_WARNING:
            recommendations.append("WARNING: Available spare capacity low - monitor for degradation")
        
        if smart.media_errors > 0:
            recommendations.append("CRITICAL: Media errors detected - backup data and replace drive")
        
        if len(device_info.error_log) >= self.thresholds.ERROR_WARNING:
            recommendations.append("WARNING: Multiple errors logged - investigate error patterns")
        
        if device_info.self_test_log:
            latest_test = device_info.self_test_log[0]
            if latest_test.test_result in [SelfTestResult.UNKNOWN_TEST_ERROR, SelfTestResult.FAILED_SEGMENT]:
                recommendations.append("WARNING: Self-test failures detected - run extended self-test")
        else:
            recommendations.append("INFO: No self-test history - consider running periodic self-tests")
        
        if smart.unsafe_shutdowns >= self.thresholds.UNSAFE_SHUTDOWN_WARNING:
            recommendations.append("WARNING: High unsafe shutdown count - check power stability")
        
        if not recommendations:
            recommendations.append("Device appears healthy - continue regular monitoring")
        
        return recommendations
    
    def _identify_risk_factors(self, device_info: DeviceInfo, analysis: Dict[str, Any]) -> List[str]:
        """Identify potential risk factors."""
        risk_factors = []
        
        if not device_info.smart_data:
            risk_factors.append("No SMART data available for assessment")
            return risk_factors
        
        smart = device_info.smart_data
        
        if smart.power_on_hours > 50000:  # ~5.7 years
            risk_factors.append("High power-on hours indicate aging device")
        
        if smart.power_cycles > self.thresholds.POWER_CYCLE_WARNING:
            risk_factors.append("High power cycle count may indicate frequent power events")
        
        write_ratio = smart.data_units_written / max(smart.data_units_read, 1)
        if write_ratio > 2.0:
            risk_factors.append("Write-heavy usage pattern may accelerate wear")
        
        if smart.temperature.celsius > 60:
            risk_factors.append("Elevated operating temperature may reduce lifespan")
        
        if len(device_info.error_log) > 0:
            risk_factors.append("Error history indicates potential reliability issues")
        
        return risk_factors


def validate_device_data(device_info: DeviceInfo) -> Dict[str, Any]:
    """
    Validate device data for consistency and completeness.
    
    Args:
        device_info: Device information to validate
        
    Returns:
        Dict containing validation results
        
    Implementation Notes:
        - Check data consistency across different sources
        - Validate ranges and formats
        - Identify missing or suspicious data
        - Return structured validation report
    """
    processor = DataProcessor()
    
    validation_result = {
        'valid': True,
        'issues': [],
        'warnings': []
    }
    
    if device_info.smart_data:
        smart_validation = processor.validate_smart_data(device_info.smart_data)
        validation_result['valid'] &= smart_validation['valid']
        validation_result['issues'].extend(smart_validation['issues'])
        validation_result['warnings'].extend(smart_validation['warnings'])
    
    return validation_result


def analyze_health_trends(device_history: List[DeviceInfo]) -> Dict[str, Any]:
    """
    Analyze health trends over time for a device.
    
    Args:
        device_history: Historical device data (chronologically ordered)
        
    Returns:
        Dict containing trend analysis
        
    Implementation Notes:
        - Calculate trends for key metrics
        - Identify degradation patterns
        - Predict potential issues
        - Include statistical analysis
    """
    if len(device_history) < 2:
        return {'error': 'Insufficient data for trend analysis'}
    
    trends = {
        'device_path': device_history[0].device_path,
        'analysis_period': {
            'start': device_history[0].collection_timestamp,
            'end': device_history[-1].collection_timestamp
        },
        'temperature_trend': {},
        'usage_trend': {},
        'error_trend': {},
        'predictions': []
    }
    
    timestamps = [d.collection_timestamp for d in device_history]
    temperatures = [d.smart_data.temperature.celsius for d in device_history if d.smart_data]
    usage_percentages = [d.smart_data.percentage_used for d in device_history if d.smart_data]
    error_counts = [len(d.error_log) for d in device_history]
    
    if len(temperatures) >= 2:
        trends['temperature_trend'] = {
            'average': mean(temperatures),
            'min': min(temperatures),
            'max': max(temperatures),
            'trend': 'increasing' if temperatures[-1] > temperatures[0] else 'decreasing',
            'volatility': stdev(temperatures) if len(temperatures) > 1 else 0
        }
    
    if len(usage_percentages) >= 2:
        trends['usage_trend'] = {
            'current': usage_percentages[-1],
            'rate_of_change': (usage_percentages[-1] - usage_percentages[0]) / len(usage_percentages),
            'trend': 'increasing' if usage_percentages[-1] > usage_percentages[0] else 'stable'
        }
    
    trends['error_trend'] = {
        'current_count': error_counts[-1],
        'trend': 'increasing' if error_counts[-1] > error_counts[0] else 'stable',
        'total_new_errors': error_counts[-1] - error_counts[0]
    }
    
    return trends


def calculate_health_score(device_info: DeviceInfo) -> int:
    """
    Calculate overall health score for a device (0-100).
    
    Args:
        device_info: Device information
        
    Returns:
        int: Health score (0=critical, 100=excellent)
        
    Implementation Notes:
        - Weight different health factors appropriately
        - Consider temperature, usage, errors, self-tests
        - Use configurable thresholds
        - Return standardized 0-100 score
    """
    processor = DataProcessor()
    return processor._calculate_health_score(device_info)


def generate_health_recommendations(device_info: DeviceInfo) -> List[str]:
    """
    Generate actionable health recommendations for a device.
    
    Args:
        device_info: Device information
        
    Returns:
        List[str]: List of recommendations
        
    Implementation Notes:
        - Analyze current health status
        - Identify potential issues
        - Provide specific actionable advice
        - Prioritize by severity
    """
    processor = DataProcessor()
    analysis = processor.analyze_device_health(device_info)
    return analysis['recommendations']


def detect_anomalies(device_info: DeviceInfo) -> List[Dict[str, Any]]:
    """
    Detect anomalies in device health data.
    
    Args:
        device_info: Device information
        
    Returns:
        List[Dict]: List of detected anomalies
        
    Implementation Notes:
        - Compare against normal ranges
        - Identify unusual patterns
        - Flag potential hardware issues
        - Include confidence levels
    """
    anomalies = []
    
    if not device_info.smart_data:
        return anomalies
    
    smart = device_info.smart_data
    
    if smart.temperature.celsius > 100:
        anomalies.append({
            'type': 'temperature',
            'severity': 'critical',
            'description': f'Extremely high temperature: {smart.temperature.celsius}°C',
            'confidence': 0.95
        })
    
    if smart.percentage_used > 100:
        anomalies.append({
            'type': 'usage',
            'severity': 'critical', 
            'description': f'Invalid usage percentage: {smart.percentage_used}%',
            'confidence': 1.0
        })
    
    if smart.power_cycles > smart.power_on_hours:
        anomalies.append({
            'type': 'power_cycles',
            'severity': 'warning',
            'description': 'Power cycles exceed power-on hours (unusual pattern)',
            'confidence': 0.8
        })
    
    return anomalies
