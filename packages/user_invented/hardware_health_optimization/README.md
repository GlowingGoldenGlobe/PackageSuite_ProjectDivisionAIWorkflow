# Hardware Health Optimization Package

## Overview
This package provides advanced thermal and duty cycle management for local GPU/CPU hardware. It's designed to extend hardware lifespan through intelligent temperature management and work/rest scheduling.

## Features
- **Thermal Management**: Maintains optimal GPU (70°C) and CPU (65°C) temperatures
- **Power Limiting**: Sets GPU power to 85% for longevity
- **Duty Cycles**: Implements work/rest periods based on workload intensity
- **Night Mode**: Reduces resource usage during off-hours (10 PM - 6 AM)
- **Maintenance Windows**: Scheduled system maintenance periods

## Non-Redundant Design
This package complements existing modules without duplication:
- Integrates with `resource_manager.py` for thermal-aware allocation
- Hooks into `hardware_monitor.py` for duty cycle reporting
- Works alongside `claude_resource_monitor.py` for parallel execution

### Files NOT Included (Already Exist in Project)
From the original 20+ file concept, these were excluded as redundant:

**Already in `hardware_monitor.py`:**
- CPU/memory/disk monitoring
- Threshold alerts
- Resource history tracking
- System summaries

**Already in `resource_manager.py`:**
- Process throttling
- Memory optimization
- Disk cleanup
- Critical resource handling

**Already in `windows_resource_monitor.py`:**
- WMI monitoring
- Task Manager metrics
- Performance alerts

**Already in `claude_resource_monitor.py`:**
- Claude-specific monitoring
- Adaptive allocation
- Task-based limits

**Already in GUI system:**
- `gui/system_monitor_integration.py` - GUI displays
- Alert handling
- Threshold management

### Unique Features in This Package
Only features NOT available elsewhere:
- GPU temperature targeting (70°C optimal)
- Power limit management (85% for longevity)
- Duty cycle scheduling (45/15 min work/rest)
- Night mode scheduling (10 PM - 6 AM)
- Maintenance window automation

## Deployment
**Local Only** - This package is excluded from cloud deployments (AWS, Azure, GCP) as cloud providers manage their own hardware optimization.

## Installation
```bash
# From pkg-suite directory
python -m pip install -e packages/user_invented/hardware_health_optimization
```

## Usage
```python
from hardware_health_optimization import ThermalOptimizer, DutyCycleManager

# Initialize managers
thermal = ThermalOptimizer()
duty_cycle = DutyCycleManager()

# Integrate with existing systems
thermal.integrate_with_resource_manager(resource_manager)
duty_cycle.register_monitor_callbacks(hardware_monitor)

# Start duty cycle scheduler
duty_cycle.start_scheduler()
```

## Configuration
Edit `health_config.json` to customize:
- Temperature targets
- Power limits
- Duty cycle durations
- Night mode hours
- Maintenance windows

## Requirements
- Local hardware deployment
- Minimum 4GB GPU memory
- psutil >= 5.8.0
- pynvml >= 11.0.0 (for NVIDIA GPUs)