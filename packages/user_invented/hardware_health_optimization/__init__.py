"""Hardware Health Optimization Package

Provides advanced thermal and duty cycle management for local GPU/CPU hardware.
This package complements existing resource managers with health-focused features.

Local-only deployment - not for cloud environments.
"""

from .thermal_optimizer import ThermalOptimizer
from .duty_cycle_manager import DutyCycleManager

__version__ = "1.0.0"
__all__ = ["ThermalOptimizer", "DutyCycleManager"]

def is_local_deployment() -> bool:
    """Check if running on local hardware (not cloud)"""
    import os
    cloud_indicators = [
        "AWS_EXECUTION_ENV",
        "AZURE_FUNCTIONS_ENVIRONMENT", 
        "GCP_PROJECT",
        "KUBERNETES_SERVICE_HOST",
        "ECS_CONTAINER_METADATA_URI"
    ]
    return not any(os.environ.get(var) for var in cloud_indicators)