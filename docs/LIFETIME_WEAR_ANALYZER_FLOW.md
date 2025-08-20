# Lifetime & Wear Analyzer - Code Flow and Function Documentation

## Overview

The `lifetime_wear_analyzer.py` example demonstrates comprehensive NVMe SSD lifetime usage and wear status analysis. This tool evaluates wear levels, estimates remaining lifespan, analyzes endurance consumption, and provides predictive failure analysis with actionable maintenance recommendations.

## Code Architecture

```
NVMeLifetimeAnalyzer
├── Device Wear Assessment
├── Lifetime Usage Analysis
├── Endurance Consumption Tracking
├── Temperature Impact Analysis
├── Power-Related Wear Factors
├── Predictive Failure Analysis
├── Replacement Recommendations
└── Comprehensive Reporting
```

## Detailed Code Flow

### 1. Data Classes Structure

The analyzer uses structured data classes to organize wear analysis results:

#### Wear Level Classification
```python
class WearLevel(Enum):
    EXCELLENT = "excellent"    # 0-20% used
    GOOD = "good"             # 21-50% used
    MODERATE = "moderate"     # 51-70% used
    HIGH = "high"            # 71-90% used
    CRITICAL = "critical"    # 91-100% used
```

#### Wear Metrics
```python
@dataclass
class WearMetrics:
    percentage_used: int
    available_spare: int
    spare_threshold: int
    power_on_hours: int
    power_cycles: int
    unsafe_shutdowns: int
    media_errors: int
    error_log_entries: int
    temperature_celsius: int
    thermal_throttle_events: int
```

#### Lifetime Analysis
```python
@dataclass
class LifetimeAnalysis:
    wear_level: WearLevel
    estimated_endurance_rating: int  # TBW
    endurance_consumed_tbw: float
    remaining_endurance_tbw: float
    estimated_remaining_days: int
    daily_wear_rate: float
    monthly_wear_rate: float
    yearly_wear_rate: float
    replacement_urgency: str
    lifespan_category: str
```

#### Temperature Analysis
```python
@dataclass
class TemperatureAnalysis:
    current_temperature: int
    average_temperature_estimate: int
    temperature_impact_factor: float
    thermal_stress_level: str
    cooling_recommendation: str
```

#### Power Analysis
```python
@dataclass
class PowerAnalysis:
    total_power_cycles: int
    unsafe_shutdown_rate: float
    power_stability_score: int
    power_related_wear_factor: float
    power_recommendations: List[str]
```

#### Predictive Analysis
```python
@dataclass
class PredictiveAnalysis:
    failure_risk_level: str
    estimated_failure_timeframe: str
    key_risk_factors: List[str]
    monitoring_recommendations: List[str]
    preventive_actions: List[str]
```

### 2. Main Analysis Function

```python
def analyze_device_lifetime(self, device_path: str) -> ComprehensiveWearAnalysis:
```

**Flow Diagram**:
```
Device Path Input
       ↓
Device Validation
       ↓
Data Collection Phase
├── SMART Data ← get_smart_log()
└── Device Info ← get_controller_info()
       ↓
Wear Metrics Parsing ← _parse_wear_metrics()
       ↓
Analysis Phase
├── Lifetime Analysis ← _analyze_lifetime()
├── Temperature Impact ← _analyze_temperature_impact()
├── Power Wear Analysis ← _analyze_power_wear()
└── Predictive Analysis ← _generate_predictive_analysis()
       ↓
Recommendations Generation ← _generate_recommendations()
       ↓
ComprehensiveWearAnalysis Assembly
```

### 3. Wear Metrics Parsing

```python
def _parse_wear_metrics(self, smart_data: Dict, device_info: Dict) -> WearMetrics:
```

**Metrics Extraction Process**:
```python
# Core wear indicators
percentage_used = smart_data.get('percentage_used', 0)
available_spare = smart_data.get('available_spare', 100)
spare_threshold = smart_data.get('available_spare_threshold', 10)

# Usage metrics
power_on_hours = smart_data.get('power_on_hours', 0)
power_cycles = smart_data.get('power_cycles', 0)
unsafe_shutdowns = smart_data.get('unsafe_shutdowns', 0)

# Error metrics
media_errors = smart_data.get('media_errors', 0)
error_log_entries = smart_data.get('num_err_log_entries', 0)

# Thermal metrics
temperature_kelvin = smart_data.get('temperature', 273)
temperature_celsius = temperature_kelvin - 273
thermal_throttle_events = smart_data.get('thermal_mgmt_temp1_trans_count', 0)
```

**Data Validation and Normalization**:
```python
# Ensure percentage_used is within valid range
percentage_used = max(0, min(100, percentage_used))

# Validate spare capacity values
available_spare = max(0, min(100, available_spare))

# Handle missing or invalid temperature data
if temperature_celsius < -40 or temperature_celsius > 150:
    temperature_celsius = 25  # Default room temperature
```

### 4. Lifetime Analysis

```python
def _analyze_lifetime(self, metrics: WearMetrics, device_info: Dict) -> LifetimeAnalysis:
```

**Wear Level Determination**:
```python
def _determine_wear_level(self, percentage_used: int) -> WearLevel:
    if percentage_used <= 20:
        return WearLevel.EXCELLENT
    elif percentage_used <= 50:
        return WearLevel.GOOD
    elif percentage_used <= 70:
        return WearLevel.MODERATE
    elif percentage_used <= 90:
        return WearLevel.HIGH
    else:
        return WearLevel.CRITICAL
```

**Endurance Rating Estimation**:
```python
def _estimate_endurance_rating(self, device_info: Dict) -> int:
    """Estimate Total Bytes Written (TBW) rating based on device characteristics."""
    
    # Get total capacity
    total_capacity_bytes = device_info.get('tnvmcap', 0)
    total_capacity_gb = total_capacity_bytes / (1000**3)
    
    # Estimate TBW based on capacity and device class
    model_name = device_info.get('mn', '').lower()
    
    # Consumer SSDs: typically 0.3-0.6 TBW per GB
    # Enterprise SSDs: typically 1-10 TBW per GB
    if any(term in model_name for term in ['pro', 'enterprise', 'datacenter']):
        tbw_per_gb = 3.0  # Enterprise class
    elif any(term in model_name for term in ['evo', 'consumer', 'gaming']):
        tbw_per_gb = 0.6  # Consumer class
    else:
        tbw_per_gb = 1.0  # Default estimate
    
    estimated_tbw = int(total_capacity_gb * tbw_per_gb)
    return max(100, estimated_tbw)  # Minimum 100 TBW
```

**Remaining Lifespan Calculation**:
```python
# Calculate consumed and remaining endurance
endurance_consumed_tbw = (percentage_used / 100) * estimated_endurance_rating
remaining_endurance_tbw = estimated_endurance_rating - endurance_consumed_tbw

# Calculate wear rates
if power_on_hours > 0:
    days_in_use = power_on_hours / 24
    daily_wear_rate = percentage_used / days_in_use if days_in_use > 0 else 0
    monthly_wear_rate = daily_wear_rate * 30
    yearly_wear_rate = daily_wear_rate * 365
    
    # Estimate remaining days
    if daily_wear_rate > 0:
        remaining_percentage = 100 - percentage_used
        estimated_remaining_days = int(remaining_percentage / daily_wear_rate)
    else:
        estimated_remaining_days = 999999  # Effectively unlimited
else:
    daily_wear_rate = 0
    monthly_wear_rate = 0
    yearly_wear_rate = 0
    estimated_remaining_days = 999999
```

**Replacement Urgency Assessment**:
```python
def determine_replacement_urgency(wear_level: WearLevel, remaining_days: int) -> str:
    if wear_level == WearLevel.CRITICAL or remaining_days < 30:
        return "IMMEDIATE"
    elif wear_level == WearLevel.HIGH or remaining_days < 90:
        return "HIGH"
    elif wear_level == WearLevel.MODERATE or remaining_days < 365:
        return "MEDIUM"
    else:
        return "LOW"
```

### 5. Temperature Impact Analysis

```python
def _analyze_temperature_impact(self, metrics: WearMetrics) -> TemperatureAnalysis:
```

**Temperature Impact Assessment**:
```python
# Estimate average temperature based on current reading
# This is simplified - real implementation might use historical data
current_temp = metrics.temperature_celsius
estimated_avg_temp = current_temp - 5  # Assume current is slightly above average

# Calculate temperature impact factor
def calculate_temp_impact_factor(avg_temp: int) -> float:
    """Calculate how temperature affects SSD lifespan."""
    if avg_temp <= 25:
        return 1.0  # Optimal temperature range
    elif avg_temp <= 40:
        return 0.95  # Slight impact
    elif avg_temp <= 55:
        return 0.85  # Moderate impact
    elif avg_temp <= 70:
        return 0.70  # High impact
    else:
        return 0.50  # Severe impact

temp_impact_factor = calculate_temp_impact_factor(estimated_avg_temp)

# Determine thermal stress level
def determine_thermal_stress(temp: int, throttle_events: int) -> str:
    if temp > 85 or throttle_events > 100:
        return "SEVERE"
    elif temp > 70 or throttle_events > 10:
        return "HIGH"
    elif temp > 55 or throttle_events > 0:
        return "MODERATE"
    else:
        return "LOW"

thermal_stress = determine_thermal_stress(current_temp, metrics.thermal_throttle_events)
```

**Cooling Recommendations**:
```python
def generate_cooling_recommendation(temp: int, stress_level: str) -> str:
    if stress_level == "SEVERE":
        return "CRITICAL: Improve cooling immediately. Consider additional fans or heat sinks."
    elif stress_level == "HIGH":
        return "Improve system ventilation and consider thermal management solutions."
    elif stress_level == "MODERATE":
        return "Monitor temperature trends and ensure adequate airflow."
    else:
        return "Temperature management is adequate."
```

### 6. Power-Related Wear Analysis

```python
def _analyze_power_wear(self, metrics: WearMetrics) -> PowerAnalysis:
```

**Power Stability Assessment**:
```python
# Calculate unsafe shutdown rate
if metrics.power_cycles > 0:
    unsafe_shutdown_rate = (metrics.unsafe_shutdowns / metrics.power_cycles) * 100
else:
    unsafe_shutdown_rate = 0

# Calculate power stability score
def calculate_power_stability_score(unsafe_rate: float, total_cycles: int) -> int:
    score = 100
    
    # Penalize high unsafe shutdown rate
    if unsafe_rate > 10:
        score -= 40
    elif unsafe_rate > 5:
        score -= 25
    elif unsafe_rate > 1:
        score -= 10
    
    # Consider total power cycles (more cycles = more stress)
    if total_cycles > 10000:
        score -= 15
    elif total_cycles > 5000:
        score -= 10
    elif total_cycles > 1000:
        score -= 5
    
    return max(0, score)

power_stability_score = calculate_power_stability_score(unsafe_shutdown_rate, metrics.power_cycles)

# Calculate power-related wear factor
def calculate_power_wear_factor(stability_score: int) -> float:
    """Higher scores mean less power-related wear."""
    return 1.0 - ((100 - stability_score) / 200)  # Range: 0.5 to 1.0

power_wear_factor = calculate_power_wear_factor(power_stability_score)
```

**Power Recommendations Generation**:
```python
recommendations = []

if unsafe_shutdown_rate > 5:
    recommendations.append("Install UPS to prevent unsafe shutdowns")
    recommendations.append("Check power supply stability")

if metrics.power_cycles > 5000:
    recommendations.append("Consider reducing unnecessary power cycles")
    recommendations.append("Enable power management features")

if power_stability_score < 70:
    recommendations.append("Investigate power quality issues")
    recommendations.append("Monitor system power events")
```

### 7. Predictive Failure Analysis

```python
def _generate_predictive_analysis(self, metrics: WearMetrics, lifetime: LifetimeAnalysis, 
                                 temp_analysis: TemperatureAnalysis, 
                                 power_analysis: PowerAnalysis) -> PredictiveAnalysis:
```

**Risk Assessment Algorithm**:
```python
# Calculate composite risk score
risk_factors = []
risk_score = 0

# Wear level risk
if lifetime.wear_level == WearLevel.CRITICAL:
    risk_score += 40
    risk_factors.append("Critical wear level (>90% used)")
elif lifetime.wear_level == WearLevel.HIGH:
    risk_score += 25
    risk_factors.append("High wear level (>70% used)")

# Spare capacity risk
if metrics.available_spare < 5:
    risk_score += 30
    risk_factors.append("Very low spare capacity (<5%)")
elif metrics.available_spare < 10:
    risk_score += 15
    risk_factors.append("Low spare capacity (<10%)")

# Temperature risk
if temp_analysis.thermal_stress_level == "SEVERE":
    risk_score += 25
    risk_factors.append("Severe thermal stress")
elif temp_analysis.thermal_stress_level == "HIGH":
    risk_score += 15
    risk_factors.append("High operating temperature")

# Power stability risk
if power_analysis.power_stability_score < 50:
    risk_score += 20
    risk_factors.append("Poor power stability")

# Media error risk
if metrics.media_errors > 0:
    risk_score += 20
    risk_factors.append("Media errors detected")

# Error log entries risk
if metrics.error_log_entries > 10:
    risk_score += 10
    risk_factors.append("Multiple error log entries")
```

**Failure Risk Level Determination**:
```python
def determine_failure_risk_level(risk_score: int) -> str:
    if risk_score >= 80:
        return "CRITICAL"
    elif risk_score >= 60:
        return "HIGH"
    elif risk_score >= 40:
        return "MODERATE"
    elif risk_score >= 20:
        return "LOW"
    else:
        return "MINIMAL"

failure_risk_level = determine_failure_risk_level(risk_score)
```

**Failure Timeframe Estimation**:
```python
def estimate_failure_timeframe(risk_level: str, remaining_days: int) -> str:
    if risk_level == "CRITICAL":
        return "0-30 days"
    elif risk_level == "HIGH":
        return "1-6 months"
    elif risk_level == "MODERATE":
        return "6-12 months"
    elif risk_level == "LOW":
        return "1-2 years"
    else:
        return ">2 years"

estimated_timeframe = estimate_failure_timeframe(failure_risk_level, lifetime.estimated_remaining_days)
```

### 8. Comprehensive Recommendations

```python
def _generate_recommendations(self, analysis: ComprehensiveWearAnalysis) -> List[str]:
```

**Recommendation Categories**:

#### Immediate Actions (Critical/High Risk)
```python
if analysis.predictive.failure_risk_level in ["CRITICAL", "HIGH"]:
    recommendations.extend([
        "🚨 URGENT: Backup all critical data immediately",
        "🚨 Plan for immediate SSD replacement",
        "🚨 Enable read-only mode if possible to preserve data",
        "🚨 Contact vendor support for warranty evaluation"
    ])
```

#### Wear Management
```python
if analysis.lifetime.wear_level in [WearLevel.HIGH, WearLevel.CRITICAL]:
    recommendations.extend([
        "📉 Reduce write-intensive workloads",
        "📉 Enable write caching and optimization",
        "📉 Implement data lifecycle management",
        "📉 Consider workload migration to newer drives"
    ])
```

#### Temperature Management
```python
if analysis.temperature.thermal_stress_level in ["HIGH", "SEVERE"]:
    recommendations.extend([
        "🌡️ Improve system cooling and ventilation",
        "🌡️ Check thermal paste and heat sink contact",
        "🌡️ Monitor temperature trends regularly",
        "🌡️ Consider thermal throttling settings"
    ])
```

#### Power Management
```python
if analysis.power.power_stability_score < 70:
    recommendations.extend([
        "⚡ Install UPS for power protection",
        "⚡ Check power supply quality and stability",
        "⚡ Enable proper shutdown procedures",
        "⚡ Monitor power events and cycles"
    ])
```

#### Monitoring and Maintenance
```python
recommendations.extend([
    "📊 Schedule regular health monitoring",
    "📊 Set up automated alerts for critical metrics",
    "📊 Document wear progression trends",
    "📊 Plan replacement based on wear projections"
])
```

### 9. Report Generation

```python
def display_wear_report(self, analysis: ComprehensiveWearAnalysis):
```

**Report Structure**:
```
🔬 NVMe SSD Lifetime & Wear Analysis Report
├── 📱 Device Information
├── 📊 Wear Metrics Summary
├── ⏱️ Lifetime Analysis
├── 🌡️ Temperature Impact Assessment
├── ⚡ Power-Related Wear Analysis
├── 🔮 Predictive Failure Analysis
└── 💡 Recommendations & Action Items
```

**Detailed Report Sections**:

#### Wear Metrics Summary
```python
print(f"📊 Wear Metrics Summary:")
print(f"   Percentage Used: {metrics.percentage_used}% ({lifetime.wear_level.value.title()})")
print(f"   Available Spare: {metrics.available_spare}% (Threshold: {metrics.spare_threshold}%)")
print(f"   Power-On Hours: {metrics.power_on_hours:,} hours ({metrics.power_on_hours/24:.1f} days)")
print(f"   Power Cycles: {metrics.power_cycles:,}")
print(f"   Unsafe Shutdowns: {metrics.unsafe_shutdowns}")
print(f"   Media Errors: {metrics.media_errors}")
```

#### Lifetime Analysis
```python
print(f"⏱️ Lifetime Analysis:")
print(f"   Wear Level: {lifetime.wear_level.value.title()}")
print(f"   Estimated Endurance: {lifetime.estimated_endurance_rating} TBW")
print(f"   Endurance Consumed: {lifetime.endurance_consumed_tbw:.1f} TBW")
print(f"   Remaining Endurance: {lifetime.remaining_endurance_tbw:.1f} TBW")
print(f"   Daily Wear Rate: {lifetime.daily_wear_rate:.3f}%")
print(f"   Estimated Remaining: {lifetime.estimated_remaining_days} days")
print(f"   Replacement Urgency: {lifetime.replacement_urgency}")
```

#### Predictive Analysis
```python
print(f"🔮 Predictive Failure Analysis:")
print(f"   Failure Risk Level: {predictive.failure_risk_level}")
print(f"   Estimated Timeframe: {predictive.estimated_failure_timeframe}")
print(f"   Key Risk Factors:")
for factor in predictive.key_risk_factors:
    print(f"     • {factor}")
```

## Function Reference

### Core NVMe Interface Functions Used

#### `get_smart_log(device_path: str) -> Dict[str, Any]`
**Purpose**: Retrieves comprehensive SMART/Health data for wear analysis

**Key Wear-Related Data**:
- `percentage_used`: Percentage of rated endurance consumed
- `available_spare`: Available spare capacity percentage
- `available_spare_threshold`: Spare capacity threshold
- `power_on_hours`: Total device power-on time
- `power_cycles`: Number of power cycles
- `unsafe_shutdowns`: Count of unsafe shutdowns
- `media_errors`: Media and data integrity errors
- `num_err_log_entries`: Number of error log entries
- `temperature`: Current temperature in Kelvin
- `thermal_mgmt_temp1_trans_count`: Thermal throttling events

#### `get_controller_info(device_path: str) -> Dict[str, Any]`
**Purpose**: Retrieves device identification for endurance estimation

**Key Data Used**:
- `mn`: Model number for device classification
- `tnvmcap`: Total NVM capacity for TBW estimation
- `sn`: Serial number for device tracking
- `fr`: Firmware revision for compatibility

## Usage Examples

### Basic Wear Analysis
```python
analyzer = NVMeLifetimeAnalyzer()
analysis = analyzer.analyze_device_lifetime("/dev/nvme0")
analyzer.display_wear_report(analysis)
```

### Automated Wear Monitoring
```python
class WearMonitoringService:
    def __init__(self):
        self.analyzer = NVMeLifetimeAnalyzer()
        self.alert_thresholds = {
            'critical_wear': 90,
            'low_spare': 10,
            'high_temp': 70,
            'high_risk_score': 60
        }
    
    def monitor_device_wear(self, device_path: str):
        analysis = self.analyzer.analyze_device_lifetime(device_path)
        
        alerts = []
        
        # Check wear level
        if analysis.wear_metrics.percentage_used >= self.alert_thresholds['critical_wear']:
            alerts.append(f"CRITICAL: Device wear at {analysis.wear_metrics.percentage_used}%")
        
        # Check spare capacity
        if analysis.wear_metrics.available_spare <= self.alert_thresholds['low_spare']:
            alerts.append(f"WARNING: Low spare capacity at {analysis.wear_metrics.available_spare}%")
        
        # Check temperature
        if analysis.wear_metrics.temperature_celsius >= self.alert_thresholds['high_temp']:
            alerts.append(f"WARNING: High temperature at {analysis.wear_metrics.temperature_celsius}°C")
        
        # Send alerts if any
        if alerts:
            self.send_alerts(device_path, alerts, analysis)
        
        return analysis
    
    def send_alerts(self, device_path: str, alerts: List[str], analysis):
        # Implementation for sending alerts (email, Slack, etc.)
        pass
```

### Wear Trend Analysis
```python
class WearTrendAnalyzer:
    def __init__(self):
        self.analyzer = NVMeLifetimeAnalyzer()
        self.historical_data = {}
    
    def track_wear_progression(self, device_path: str):
        analysis = self.analyzer.analyze_device_lifetime(device_path)
        
        # Store current analysis
        timestamp = datetime.now()
        if device_path not in self.historical_data:
            self.historical_data[device_path] = []
        
        self.historical_data[device_path].append({
            'timestamp': timestamp,
            'percentage_used': analysis.wear_metrics.percentage_used,
            'available_spare': analysis.wear_metrics.available_spare,
            'power_on_hours': analysis.wear_metrics.power_on_hours,
            'temperature': analysis.wear_metrics.temperature_celsius
        })
        
        # Analyze trends if we have enough data
        if len(self.historical_data[device_path]) >= 2:
            return self.calculate_wear_trends(device_path)
        
        return None
    
    def calculate_wear_trends(self, device_path: str):
        data = self.historical_data[device_path]
        if len(data) < 2:
            return None
        
        # Calculate wear rate trends
        latest = data[-1]
        previous = data[-2]
        
        time_diff_hours = (latest['timestamp'] - previous['timestamp']).total_seconds() / 3600
        
        wear_rate_per_hour = (latest['percentage_used'] - previous['percentage_used']) / time_diff_hours
        spare_decline_rate = (previous['available_spare'] - latest['available_spare']) / time_diff_hours
        
        return {
            'wear_rate_per_hour': wear_rate_per_hour,
            'wear_rate_per_day': wear_rate_per_hour * 24,
            'spare_decline_rate_per_hour': spare_decline_rate,
            'projected_failure_days': (100 - latest['percentage_used']) / (wear_rate_per_hour * 24) if wear_rate_per_hour > 0 else float('inf')
        }
```

## Integration Patterns

### Maintenance Scheduling
```python
def generate_maintenance_schedule():
    analyzer = NVMeLifetimeAnalyzer()
    devices = list_nvme_devices()
    
    maintenance_schedule = []
    
    for device in devices:
        analysis = analyzer.analyze_device_lifetime(device['DevicePath'])
        
        # Determine maintenance priority
        if analysis.lifetime.replacement_urgency == "IMMEDIATE":
            priority = 1
            action = "Replace immediately"
        elif analysis.lifetime.replacement_urgency == "HIGH":
            priority = 2
            action = "Schedule replacement within 30 days"
        elif analysis.lifetime.replacement_urgency == "MEDIUM":
            priority = 3
            action = "Plan replacement within 90 days"
        else:
            priority = 4
            action = "Monitor and reassess in 6 months"
        
        maintenance_schedule.append({
            'device': device['DevicePath'],
            'model': analysis.device_model,
            'serial': analysis.device_serial,
            'priority': priority,
            'action': action,
            'wear_level': analysis.lifetime.wear_level.value,
            'estimated_remaining_days': analysis.lifetime.estimated_remaining_days
        })
    
    # Sort by priority
    maintenance_schedule.sort(key=lambda x: x['priority'])
    return maintenance_schedule
```

This comprehensive documentation provides complete understanding of the lifetime and wear analyzer's assessment algorithms, predictive capabilities, and maintenance planning integration for effective NVMe SSD lifecycle management.
