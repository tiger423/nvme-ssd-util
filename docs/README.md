# NVMe SSD Utility Documentation

This directory contains comprehensive documentation for the NVMe Health Monitor utility and its examples.

## 📖 Core Documentation

### Function References
- [Function Reference](FUNCTION_REFERENCE.md) - Complete API documentation for all utility functions
- [NVMe Format Code Flow](NVME_FORMAT_CODE_FLOW.md) - Detailed NVMe formatting workflow and implementation

## 📊 Example Documentation

### Analysis Examples Code Flow
- [Health Status Checker Flow](HEALTH_STATUS_CHECKER_FLOW.md) - Multi-parameter health assessment with scoring algorithms
- [Device Info Analyzer Flow](DEVICE_INFO_ANALYZER_FLOW.md) - Comprehensive device information extraction and analysis
- [Device Detector Flow](DEVICE_DETECTOR_FLOW.md) - System-wide device discovery and PCIe topology analysis
- [Lifetime & Wear Analyzer Flow](LIFETIME_WEAR_ANALYZER_FLOW.md) - Wear level assessment and lifespan prediction
- [WAF Calculator Flow](WAF_CALCULATOR_FLOW.md) - Write amplification factor calculation and optimization

## 🎯 Documentation Features

Each code flow document includes:
- **Detailed Architecture Diagrams** - Visual representation of code flow and data processing
- **Function-by-Function Breakdown** - Comprehensive explanation of each function's purpose and implementation
- **Data Class Structures** - Complete documentation of data models and their relationships
- **Usage Examples** - Practical examples for different use cases and integration patterns
- **Error Handling** - Common issues and troubleshooting guidance
- **Performance Considerations** - Optimization tips and resource usage information
- **Integration Patterns** - Examples for monitoring systems, automation, and reporting

## 🔗 Quick Navigation

| Example | Purpose | Documentation |
|---------|---------|---------------|
| Health Status Checker | Assess SSD health with pass/fail determination | [Flow Doc](HEALTH_STATUS_CHECKER_FLOW.md) |
| Device Info Analyzer | Extract detailed device specifications | [Flow Doc](DEVICE_INFO_ANALYZER_FLOW.md) |
| Device Detector | Discover and enumerate all NVMe devices | [Flow Doc](DEVICE_DETECTOR_FLOW.md) |
| Lifetime & Wear Analyzer | Analyze wear levels and predict lifespan | [Flow Doc](LIFETIME_WEAR_ANALYZER_FLOW.md) |
| WAF Calculator | Calculate write amplification and optimize | [Flow Doc](WAF_CALCULATOR_FLOW.md) |

## 🚀 Getting Started

1. **Start with the examples** in the [examples/](../examples/) directory
2. **Read the relevant code flow documentation** for detailed understanding
3. **Refer to the Function Reference** for API details
4. **Use the integration patterns** for production deployments

## 📝 Contributing

When adding new examples or modifying existing ones:
1. Update the corresponding code flow documentation
2. Include comprehensive function explanations
3. Add usage examples and integration patterns
4. Update this README with links to new documentation

## 🔧 Development

All documentation follows the established patterns:
- Comprehensive code flow diagrams
- Detailed function breakdowns with implementation notes
- Real-world usage examples
- Integration patterns for production use
- Performance considerations and optimization tips
- Troubleshooting guides and common issues

This documentation is designed to be educational and practical for developers implementing NVMe monitoring solutions.
