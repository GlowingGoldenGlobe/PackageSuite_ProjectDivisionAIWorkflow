"""Duty Cycle Manager - Work/rest period scheduling

Implements hardware rest periods to extend component lifespan.
Integrates with existing hardware_monitor.py
"""

import time
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable

logger = logging.getLogger(__name__)

class DutyCycleManager:
    """Manages work/rest cycles for hardware longevity"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.cycle_state = "active"
        self.cycle_start = datetime.now()
        self.callbacks = []
        self.night_mode = False
        self._scheduler_thread = None
        self._running = False
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load duty cycle configuration"""
        default_config = {
            "cycles": {
                "heavy_compute": {
                    "work_minutes": 45,
                    "rest_minutes": 15,
                    "max_continuous_hours": 3
                },
                "normal": {
                    "work_minutes": 55,
                    "rest_minutes": 5,
                    "max_continuous_hours": 6
                }
            },
            "night_mode": {
                "enabled": True,
                "start_hour": 22,
                "end_hour": 6,
                "resource_reduction": 0.5
            },
            "maintenance_windows": [
                {"day": "sunday", "hour": 3, "duration_minutes": 30}
            ]
        }
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
                
        return default_config
    
    def get_cycle_state(self, workload_type: str = "normal") -> Dict[str, any]:
        """Get current duty cycle state and recommendations"""
        cycle_config = self.config["cycles"].get(workload_type, self.config["cycles"]["normal"])
        elapsed = (datetime.now() - self.cycle_start).total_seconds() / 60
        
        # Check night mode
        current_hour = datetime.now().hour
        night_config = self.config["night_mode"]
        if night_config["enabled"]:
            if night_config["start_hour"] <= current_hour or current_hour < night_config["end_hour"]:
                self.night_mode = True
            else:
                self.night_mode = False
        
        # Determine if rest needed
        work_minutes = cycle_config["work_minutes"]
        rest_minutes = cycle_config["rest_minutes"]
        cycle_duration = work_minutes + rest_minutes
        
        cycle_position = elapsed % cycle_duration
        needs_rest = cycle_position >= work_minutes
        
        # Check continuous operation limit
        continuous_hours = elapsed / 60
        force_extended_rest = continuous_hours >= cycle_config["max_continuous_hours"]
        
        return {
            "state": "rest" if needs_rest or force_extended_rest else "active",
            "elapsed_minutes": elapsed,
            "next_transition_minutes": work_minutes - cycle_position if not needs_rest else cycle_duration - cycle_position,
            "night_mode": self.night_mode,
            "resource_scale": night_config["resource_reduction"] if self.night_mode else 1.0,
            "force_extended_rest": force_extended_rest,
            "recommended_action": self._get_recommendation(needs_rest, force_extended_rest)
        }
    
    def _get_recommendation(self, needs_rest: bool, force_extended: bool) -> str:
        """Get recommendation based on cycle state"""
        if force_extended:
            return "Extended rest required - pause heavy computations for 30 minutes"
        elif needs_rest:
            return "Short rest period - reduce workload or pause non-critical tasks"
        elif self.night_mode:
            return "Night mode active - operating at reduced capacity"
        else:
            return "Normal operation"
    
    def register_monitor_callbacks(self, hardware_monitor):
        """Integrate with existing hardware_monitor.py"""
        # Add duty cycle info to monitoring
        def add_duty_cycle_info(original_stats):
            stats = original_stats.copy()
            cycle_info = self.get_cycle_state()
            
            stats["duty_cycle"] = {
                "state": cycle_info["state"],
                "night_mode": cycle_info["night_mode"],
                "resource_scale": cycle_info["resource_scale"],
                "recommendation": cycle_info["recommended_action"]
            }
            
            # Apply resource scaling if in rest or night mode
            if cycle_info["state"] == "rest" or cycle_info["night_mode"]:
                scale = 0.5 if cycle_info["state"] == "rest" else cycle_info["resource_scale"]
                
                # Add recommendation to reduce load
                if "alerts" not in stats:
                    stats["alerts"] = []
                stats["alerts"].append({
                    "level": "info",
                    "message": cycle_info["recommended_action"],
                    "resource_scale": scale
                })
                
            return stats
        
        # Wrap the get_stats method
        original_get_stats = hardware_monitor.get_system_stats
        hardware_monitor.get_system_stats = lambda: add_duty_cycle_info(original_get_stats())
        
        logger.info("Duty cycle manager integrated with hardware monitor")
    
    def start_scheduler(self):
        """Start background scheduler for maintenance windows"""
        if self._running:
            return
            
        self._running = True
        self._scheduler_thread = threading.Thread(target=self._schedule_loop, daemon=True)
        self._scheduler_thread.start()
        
    def stop_scheduler(self):
        """Stop background scheduler"""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
    
    def _schedule_loop(self):
        """Background loop for maintenance windows"""
        while self._running:
            try:
                # Check for maintenance windows
                now = datetime.now()
                for window in self.config.get("maintenance_windows", []):
                    if (now.strftime("%A").lower() == window["day"].lower() and
                        now.hour == window["hour"] and
                        now.minute < 5):  # Check within first 5 minutes
                        
                        logger.info(f"Maintenance window starting: {window}")
                        for callback in self.callbacks:
                            callback("maintenance", window)
                        
                        # Sleep through maintenance window
                        time.sleep(window["duration_minutes"] * 60)
                        
                # Sleep 5 minutes before next check
                time.sleep(300)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
    
    def add_callback(self, callback: Callable):
        """Add callback for duty cycle events"""
        self.callbacks.append(callback)
        
    def reset_cycle(self):
        """Reset duty cycle timer"""
        self.cycle_start = datetime.now()
        self.cycle_state = "active"
        logger.info("Duty cycle reset")