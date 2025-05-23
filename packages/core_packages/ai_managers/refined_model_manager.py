#!/usr/bin/env python
# refined_model_manager.py - Management system for refined models in GlowingGoldenGlobe

import os
import json
from tkinter import messagebox

class RefinedModelManager:
    """A class to manage refined models and their status"""
    
    def __init__(self, config_path="agent_mode_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except:
                pass
        
        # Return default configuration
        return {
            "development_mode": "refined_model",
            "time_limit_hours": 1,
            "auto_save_interval": 5,
            "auto_continue": True,
            "selected_version": "1",
            "refined_models": [],  # List of model versions that are marked as refined
        }
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save configuration: {str(e)}")
            return False
    
    def is_refined_model(self, version):
        """Check if the specified model version is a refined model"""
        # Check if this version is in the list of refined models in config
        refined_models = self.config.get("refined_models", [])
        return version in refined_models
    
    def mark_as_refined(self, version):
        """Mark a model version as refined"""
        # Get the list of refined models
        refined_models = self.config.get("refined_models", [])
        
        # Add this version if not already in the list
        if version not in refined_models:
            refined_models.append(version)
            
        # Update config
        self.config["refined_models"] = refined_models
        
        # Save to file
        success = self.save_config()
        return success
    
    def unmark_as_refined(self, version):
        """Remove refined status from a model version"""
        # Get the list of refined models
        refined_models = self.config.get("refined_models", [])
        
        # Remove this version from the list
        if version in refined_models:
            refined_models.remove(version)
            
        # Update config
        self.config["refined_models"] = refined_models
        
        # Save to file
        success = self.save_config()
        return success
    
    def get_all_refined_models(self):
        """Get a list of all refined model versions"""
        return self.config.get("refined_models", [])
    
    def update_config_from_dict(self, config_dict):
        """Update this object's config from another config dictionary"""
        # Only update refined_models from external config
        if "refined_models" in config_dict:
            self.config["refined_models"] = config_dict["refined_models"]
            return True
        return False
