"""Thermal Optimizer - GPU/CPU temperature management

Non-redundant features focused on thermal health optimization.
Integrates with existing resource_manager.py
"""

import psutil
import json
import logging
from typing import Dict, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class ThermalOptimizer:
    """Manages thermal targets and power limits for hardware longevity"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.gpu_available = self._check_gpu()
        self.callbacks = []
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load thermal configuration"""
        default_config = {
            "gpu": {
                "temp_target_c": 70,
                "temp_max_c": 80,
                "power_limit_percent": 85
            },
            "cpu": {
                "temp_target_c": 65,
                "temp_max_c": 75,
                "turbo_disable_temp_c": 70
            }
        }
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
                
        return default_config
    
    def _check_gpu(self) -> bool:
        """Check if GPU monitoring available"""
        try:
            import pynvml
            pynvml.nvmlInit()
            return True
        except:
            return False
            
    def get_thermal_adjustment(self) -> Dict[str, float]:
        """Calculate resource adjustments based on temperature"""
        adjustments = {
            "cpu_scale": 1.0,
            "gpu_scale": 1.0,
            "gpu_power_limit": self.config["gpu"]["power_limit_percent"]
        }
        
        # CPU temperature check
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                cpu_temps = []
                for name, entries in temps.items():
                    if 'cpu' in name.lower() or 'core' in name.lower():
                        cpu_temps.extend([e.current for e in entries])
                
                if cpu_temps:
                    avg_cpu_temp = sum(cpu_temps) / len(cpu_temps)
                    target = self.config["cpu"]["temp_target_c"]
                    max_temp = self.config["cpu"]["temp_max_c"]
                    
                    if avg_cpu_temp > max_temp:
                        adjustments["cpu_scale"] = 0.7
                    elif avg_cpu_temp > target:
                        # Linear scale between target and max
                        scale_factor = (max_temp - avg_cpu_temp) / (max_temp - target)
                        adjustments["cpu_scale"] = 0.7 + (0.3 * scale_factor)
        except:
            pass
            
        # GPU temperature check
        if self.gpu_available:
            try:
                import pynvml
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                
                target = self.config["gpu"]["temp_target_c"]
                max_temp = self.config["gpu"]["temp_max_c"]
                
                if gpu_temp > max_temp:
                    adjustments["gpu_scale"] = 0.6
                    adjustments["gpu_power_limit"] = 70
                elif gpu_temp > target:
                    scale_factor = (max_temp - gpu_temp) / (max_temp - target)
                    adjustments["gpu_scale"] = 0.6 + (0.4 * scale_factor)
                    adjustments["gpu_power_limit"] = 70 + (15 * scale_factor)
            except:
                pass
                
        return adjustments
    
    def integrate_with_resource_manager(self, resource_manager):
        """Hook into existing resource_manager.py"""
        # Add thermal checks to resource allocation
        original_check = resource_manager.check_resources
        
        def thermal_aware_check():
            resources = original_check()
            thermal = self.get_thermal_adjustment()
            
            # Apply thermal adjustments
            if "cpu" in resources:
                resources["cpu"]["available"] *= thermal["cpu_scale"]
            if "gpu" in resources:
                resources["gpu"]["available"] *= thermal["gpu_scale"]
                
            return resources
            
        resource_manager.check_resources = thermal_aware_check
        logger.info("Thermal optimizer integrated with resource manager")
        
    def set_gpu_power_limit(self, percent: int):
        """Set GPU power limit (requires admin on Windows)"""
        if not self.gpu_available:
            return False
            
        try:
            import pynvml
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            
            # Get power limit range
            min_limit = pynvml.nvmlDeviceGetPowerManagementLimitConstraints(handle)[0]
            max_limit = pynvml.nvmlDeviceGetPowerManagementLimitConstraints(handle)[1]
            
            # Calculate target in milliwatts
            target_mw = min_limit + (max_limit - min_limit) * percent // 100
            
            # This requires elevated privileges
            pynvml.nvmlDeviceSetPowerManagementLimit(handle, target_mw)
            return True
        except Exception as e:
            logger.warning(f"Could not set GPU power limit: {e}")
            return False