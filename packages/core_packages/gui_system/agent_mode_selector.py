#!/usr/bin/env python
"""
Agent Mode Selector for GlowingGoldenGlobe

This module provides intelligent AgentModeSelector that:
1. Verifies model availability and capabilities
2. Checks context reasoning levels for each mode
3. Compares API token costs vs Claude Code subscription benefits
4. Auto-decides optimal mode based on user preferences and task requirements
5. Handles parallel execution optimization
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
import subprocess
import sys
import requests
import threading
from datetime import datetime
from pathlib import Path

class ModelCapabilityAnalyzer:
    """Analyzes and verifies model capabilities for different modes"""
    
    # Define minimum requirements for high-level reasoning tasks
    MINIMUM_CONTEXT_TOKENS = 100000  # 100K tokens minimum for mass context reasoning
    REQUIRED_CAPABILITIES = [
        "code_analysis", "complex_reasoning", "long_context", 
        "parallel_processing", "error_handling"
    ]
    
    @staticmethod
    def check_vscode_models():
        """Check VSCode extension available models and their capabilities"""
        try:
            # Check if VSCode Claude extension is installed
            vscode_extensions = subprocess.run(
                ["code", "--list-extensions"], 
                capture_output=True, text=True, timeout=10
            )
            
            claude_extension = "anthropic.claude-dev" in vscode_extensions.stdout
            
            if not claude_extension:
                return {
                    "available": False,
                    "reason": "VSCode Claude extension not installed",
                    "models": [],
                    "recommendation": "install_extension"
                }
            
            # VSCode extension typically uses lower-tier models with limited context
            vscode_models = [
                {
                    "name": "claude-3-haiku",
                    "context_limit": 200000,  # Actually good for most tasks
                    "reasoning_level": "medium",
                    "cost_tier": "low"
                },
                {
                    "name": "claude-3-sonnet", 
                    "context_limit": 200000,
                    "reasoning_level": "high",
                    "cost_tier": "medium"
                }
            ]
            
            # Check if any model meets our requirements
            suitable_models = [
                m for m in vscode_models 
                if m["context_limit"] >= ModelCapabilityAnalyzer.MINIMUM_CONTEXT_TOKENS
                and m["reasoning_level"] in ["high", "very_high"]
            ]
            
            return {
                "available": True,
                "models": vscode_models,
                "suitable_models": suitable_models,
                "meets_requirements": len(suitable_models) > 0,
                "limitation": "Limited to extension-supported models only"
            }
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {
                "available": False,
                "reason": "VSCode not found or not accessible",
                "models": [],
                "recommendation": "check_vscode_installation"
            }
    
    @staticmethod
    def check_api_key_models(api_key=None):
        """Check API key access and available models"""
        if not api_key:
            return {
                "available": False,
                "reason": "No API key provided",
                "models": [],
                "cost_estimate": "unknown"
            }
        
        try:
            # Test API access (mock for now - would need actual Anthropic API)
            available_models = [
                {
                    "name": "claude-3-opus-20240229",
                    "context_limit": 200000,
                    "reasoning_level": "very_high", 
                    "cost_per_1k_tokens": {"input": 0.015, "output": 0.075},
                    "ideal_for": "complex_reasoning"
                },
                {
                    "name": "claude-3-sonnet-20240229",
                    "context_limit": 200000,
                    "reasoning_level": "high",
                    "cost_per_1k_tokens": {"input": 0.003, "output": 0.015},
                    "ideal_for": "balanced_performance"
                },
                {
                    "name": "claude-3-haiku-20240307", 
                    "context_limit": 200000,
                    "reasoning_level": "medium",
                    "cost_per_1k_tokens": {"input": 0.00025, "output": 0.00125},
                    "ideal_for": "fast_simple_tasks"
                }
            ]
            
            # All API models meet our context requirements
            suitable_models = [
                m for m in available_models
                if m["reasoning_level"] in ["high", "very_high"]
            ]
            
            return {
                "available": True,
                "models": available_models,
                "suitable_models": suitable_models,
                "meets_requirements": len(suitable_models) > 0,
                "cost_warning": "Token-based billing applies"
            }
            
        except Exception as e:
            return {
                "available": False,
                "reason": f"API validation failed: {str(e)}",
                "models": []
            }
    
    @staticmethod 
    def check_claude_code_availability():
        """Check Claude Code subscription status and capabilities"""
        try:
            # Check if we're running in Claude Code environment
            claude_code_indicators = [
                os.getenv("CLAUDE_CODE_SESSION"),
                os.getenv("ANTHROPIC_CLI"),
                "claude-code" in sys.argv[0] if sys.argv else False
            ]
            
            in_claude_code = any(claude_code_indicators)
            
            if in_claude_code:
                return {
                    "available": True,
                    "models": [
                        {
                            "name": "claude-3-5-sonnet-20241022",
                            "context_limit": 200000,
                            "reasoning_level": "very_high",
                            "cost": "subscription_included",
                            "ideal_for": "all_tasks"
                        }
                    ],
                    "meets_requirements": True,
                    "cost_advantage": "No additional token costs",
                    "recommendation": "preferred_mode"
                }
            else:
                return {
                    "available": False,
                    "reason": "Not running in Claude Code environment",
                    "models": [],
                    "recommendation": "use_claude_code_cli"
                }
                
        except Exception as e:
            return {
                "available": False, 
                "reason": f"Claude Code check failed: {str(e)}",
                "models": []
            }


class IntelligentModeDecision:
    """Makes intelligent decisions about which mode to use"""
    
    def __init__(self, user_preferences=None):
        self.user_preferences = user_preferences or {}
        self.mode_capabilities = {}
        self.cost_analysis = {}
    
    def analyze_all_modes(self, api_key=None):
        """Analyze capabilities of all available modes"""
        self.mode_capabilities = {
            "claude_code": ModelCapabilityAnalyzer.check_claude_code_availability(),
            "api_key": ModelCapabilityAnalyzer.check_api_key_models(api_key),
            "vscode": ModelCapabilityAnalyzer.check_vscode_models()
        }
        
        return self.mode_capabilities
    
    def calculate_cost_comparison(self, estimated_tokens=10000):
        """Compare costs between modes for estimated token usage"""
        costs = {}
        
        # Claude Code - subscription included
        if self.mode_capabilities.get("claude_code", {}).get("available"):
            costs["claude_code"] = {
                "monetary_cost": 0,
                "limitation": "session_limits",
                "value_score": 10  # Highest value
            }
        
        # API Key - token-based billing
        if self.mode_capabilities.get("api_key", {}).get("available"):
            api_models = self.mode_capabilities["api_key"].get("suitable_models", [])
            if api_models:
                # Use most cost-effective suitable model
                cheapest_suitable = min(api_models, 
                    key=lambda m: m["cost_per_1k_tokens"]["input"] + m["cost_per_1k_tokens"]["output"])
                
                input_cost = (estimated_tokens / 1000) * cheapest_suitable["cost_per_1k_tokens"]["input"]
                output_cost = (estimated_tokens / 1000) * cheapest_suitable["cost_per_1k_tokens"]["output"] 
                total_cost = input_cost + output_cost
                
                costs["api_key"] = {
                    "monetary_cost": total_cost,
                    "model": cheapest_suitable["name"],
                    "limitation": "token_budget", 
                    "value_score": 7  # Good but costs money
                }
        
        # VSCode - limited capabilities
        if self.mode_capabilities.get("vscode", {}).get("available"):
            costs["vscode"] = {
                "monetary_cost": 0,
                "limitation": "model_capabilities",
                "value_score": 3 if self.mode_capabilities["vscode"]["meets_requirements"] else 1
            }
        
        self.cost_analysis = costs
        return costs
    
    def recommend_mode(self, task_complexity="medium", user_budget_preference="low"):
        """Recommend the best mode based on analysis"""
        if not self.mode_capabilities:
            return {"mode": None, "reason": "No analysis performed"}
        
        # Check user disabled modes
        disabled_modes = self.user_preferences.get("disabled_modes", [])
        
        available_modes = []
        for mode, capabilities in self.mode_capabilities.items():
            if capabilities.get("available") and mode not in disabled_modes:
                available_modes.append(mode)
        
        if not available_modes:
            return {"mode": None, "reason": "No available modes after filtering"}
        
        # Decision logic based on task complexity and preferences
        if task_complexity in ["high", "very_high"]:
            # High complexity tasks need best reasoning models
            if "claude_code" in available_modes and self.mode_capabilities["claude_code"]["meets_requirements"]:
                return {
                    "mode": "claude_code",
                    "reason": "Best reasoning capability with no token costs",
                    "confidence": "high"
                }
            elif "api_key" in available_modes and self.mode_capabilities["api_key"]["meets_requirements"]:
                return {
                    "mode": "api_key", 
                    "reason": "High reasoning capability (token costs apply)",
                    "confidence": "medium",
                    "warning": "Will incur API costs"
                }
        
        elif task_complexity == "medium":
            # Medium tasks - prefer cost-effective options
            if user_budget_preference == "low":
                if "claude_code" in available_modes:
                    return {
                        "mode": "claude_code",
                        "reason": "No additional costs, good capabilities",
                        "confidence": "high"
                    }
                elif "vscode" in available_modes and self.mode_capabilities["vscode"]["meets_requirements"]:
                    return {
                        "mode": "vscode",
                        "reason": "No token costs, adequate for medium tasks", 
                        "confidence": "medium"
                    }
            else:
                # User willing to pay for better performance
                if "api_key" in available_modes:
                    return {
                        "mode": "api_key",
                        "reason": "Best performance for medium tasks",
                        "confidence": "high"
                    }
        
        # Fallback to any available mode
        fallback_mode = available_modes[0]
        return {
            "mode": fallback_mode,
            "reason": f"Fallback to available mode: {fallback_mode}",
            "confidence": "low"
        }


class AgentModeSelector:
    """Intelligent UI component for selecting optimal AI agent mode"""
    
    def __init__(self, parent_frame, config=None):
        self.parent_frame = parent_frame
        self.config = config or {}
        self.selected_mode = tk.StringVar(value=self.config.get("agent_mode", "auto"))
        self.mode_frame = None
        self.status_frame = None
        self.analyzer = ModelCapabilityAnalyzer()
        self.decision_engine = IntelligentModeDecision(self.config.get("user_preferences", {}))
        self.mode_status = {}
        self.auto_decide_enabled = tk.BooleanVar(value=self.config.get("auto_decide", True))
        
    def create_selector(self, row=0, column=0, columnspan=1, sticky="ew", padx=5, pady=5):
        """Create the intelligent agent mode selector UI"""
        
        # Create main frame for agent mode selection
        self.mode_frame = ttk.LabelFrame(self.parent_frame, text="Intelligent AI Agent Selection")
        self.mode_frame.pack(fill=tk.X, padx=padx, pady=pady)
        
        # Auto-decision toggle
        auto_frame = ttk.Frame(self.mode_frame)
        auto_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(
            auto_frame,
            text="Auto-decide optimal mode (recommended)",
            variable=self.auto_decide_enabled,
            command=self._on_auto_decide_change
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            auto_frame,
            text="Analyze Modes",
            command=self._analyze_modes_async
        ).pack(side=tk.RIGHT)
        
        # Mode selection frame
        selection_frame = ttk.Frame(self.mode_frame)
        selection_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Agent mode options with intelligent status
        modes = [
            ("auto", "Auto-Select Best Mode", "Automatically choose optimal mode based on analysis"),
            ("claude_code", "Claude Code (Preferred)", "Subscription-based, no token costs"),
            ("api_key", "API-Key Mode", "Direct API access with token billing"),
            ("vscode", "VSCode Agent Mode", "Limited models, may not meet requirements")
        ]
        
        self.mode_radios = {}
        self.status_labels = {}
        
        # Create radio buttons with status indicators
        for i, (mode_key, display_name, description) in enumerate(modes):
            # Create a frame for each mode option
            mode_option_frame = ttk.Frame(selection_frame)
            mode_option_frame.pack(fill=tk.X, pady=2)
            
            mode_radio = ttk.Radiobutton(
                mode_option_frame,
                text=display_name,
                variable=self.selected_mode,
                value=mode_key,
                command=self._on_mode_change
            )
            mode_radio.pack(side=tk.LEFT, anchor="w")
            self.mode_radios[mode_key] = mode_radio
            
            # Status indicator (will be updated by analysis)
            status_label = ttk.Label(
                mode_option_frame,
                text="⚪ Checking...",
                font=("Arial", 8)
            )
            status_label.pack(side=tk.LEFT, padx=(10, 5))
            self.status_labels[mode_key] = status_label
            
            # Description label
            desc_label = ttk.Label(
                mode_option_frame,
                text=f"→ {description}",
                font=("Arial", 8),
                foreground="gray"
            )
            desc_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Status frame for detailed analysis results
        self.status_frame = ttk.LabelFrame(self.mode_frame, text="Mode Analysis Results")
        self.status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_text = tk.Text(self.status_frame, height=4, wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(self.mode_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame,
            text="Configure Selected Mode",
            command=self._configure_mode
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Disable Mode",
            command=self._disable_mode
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="User Preferences",
            command=self._open_preferences
        ).pack(side=tk.LEFT, padx=5)
        
        # Start initial analysis
        self.parent_frame.after(100, self._analyze_modes_async)
        
        return self.mode_frame
    
    def _on_mode_change(self):
        """Handle mode selection change with intelligent feedback"""
        selected = self.selected_mode.get()
        
        # Update configuration
        if self.config:
            self.config["agent_mode"] = selected
        
        # Provide intelligent feedback
        if selected == "auto":
            self._auto_select_mode()
        else:
            self._validate_selected_mode(selected)
    
    def _on_auto_decide_change(self):
        """Handle auto-decide toggle change"""
        if self.auto_decide_enabled.get():
            self.selected_mode.set("auto")
            self._auto_select_mode()
    
    def _analyze_modes_async(self):
        """Analyze modes in background thread"""
        def analyze():
            try:
                api_key = self.config.get("api_key")
                capabilities = self.decision_engine.analyze_all_modes(api_key)
                costs = self.decision_engine.calculate_cost_comparison()
                
                # Update UI on main thread
                self.parent_frame.after(0, lambda: self._update_mode_status(capabilities, costs))
            except Exception as e:
                self.parent_frame.after(0, lambda: self._show_analysis_error(str(e)))
        
        threading.Thread(target=analyze, daemon=True).start()
    
    def _update_mode_status(self, capabilities, costs):
        """Update mode status indicators based on analysis"""
        status_symbols = {
            "available_good": "🟢",
            "available_limited": "🟡", 
            "unavailable": "🔴",
            "preferred": "⭐"
        }
        
        # Update each mode's status
        for mode, capability in capabilities.items():
            if mode == "claude_code":
                if capability.get("available"):
                    symbol = status_symbols["preferred"]
                    text = "Available (Recommended)"
                else:
                    symbol = status_symbols["unavailable"]
                    text = capability.get("reason", "Not available")
            
            elif mode == "api_key":
                if capability.get("available") and capability.get("meets_requirements"):
                    symbol = status_symbols["available_good"]
                    text = "Available (Token costs apply)"
                elif capability.get("available"):
                    symbol = status_symbols["available_limited"]
                    text = "Available (Limited models)"
                else:
                    symbol = status_symbols["unavailable"] 
                    text = capability.get("reason", "Not available")
            
            elif mode == "vscode":
                if capability.get("available") and capability.get("meets_requirements"):
                    symbol = status_symbols["available_good"]
                    text = "Available (Limited context)"
                elif capability.get("available"):
                    symbol = status_symbols["available_limited"]
                    text = "Available (May not meet requirements)"
                else:
                    symbol = status_symbols["unavailable"]
                    text = capability.get("reason", "Extension not found")
            
            if mode in self.status_labels:
                self.status_labels[mode].config(text=f"{symbol} {text}")
        
        # Set auto mode status
        recommendation = self.decision_engine.recommend_mode()
        if recommendation.get("mode"):
            auto_text = f"⚡ Will use: {recommendation['mode']} ({recommendation.get('confidence', 'unknown')} confidence)"
        else:
            auto_text = "❌ No suitable mode available"
        
        if "auto" in self.status_labels:
            self.status_labels["auto"].config(text=auto_text)
        
        # Update detailed status
        self._update_detailed_status(capabilities, costs, recommendation)
        
        # Auto-select if enabled
        if self.auto_decide_enabled.get():
            self._auto_select_mode()
    
    def _update_detailed_status(self, capabilities, costs, recommendation):
        """Update the detailed status text area"""
        if not hasattr(self, 'status_text'):
            return
            
        status_text = []
        
        # Analysis summary
        status_text.append(f"Analysis completed at {datetime.now().strftime('%H:%M:%S')}")
        
        if recommendation.get("mode"):
            status_text.append(f"Recommended: {recommendation['mode']} - {recommendation.get('reason', '')}")
            if recommendation.get("warning"):
                status_text.append(f"⚠️  {recommendation['warning']}")
        
        # Cost comparison
        if costs:
            status_text.append("\nCost Comparison:")
            for mode, cost_info in costs.items():
                cost_str = f"${cost_info['monetary_cost']:.3f}" if cost_info['monetary_cost'] > 0 else "Free"
                status_text.append(f"  {mode}: {cost_str} (Score: {cost_info['value_score']}/10)")
        
        # Capability summary  
        status_text.append(f"\nAvailable modes: {len([c for c in capabilities.values() if c.get('available')])}/3")
        
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(1.0, "\n".join(status_text))
    
    def _auto_select_mode(self):
        """Automatically select the best mode based on analysis"""
        recommendation = self.decision_engine.recommend_mode()
        
        if recommendation.get("mode"):
            best_mode = recommendation["mode"]
            if best_mode != "auto":  # Avoid infinite recursion
                self.selected_mode.set(best_mode)
                self._validate_selected_mode(best_mode)
    
    def _validate_selected_mode(self, mode):
        """Validate and provide feedback for selected mode"""
        capabilities = self.decision_engine.mode_capabilities.get(mode, {})
        
        feedback_text = f"Selected: {mode}\n"
        
        if not capabilities.get("available"):
            feedback_text += f"⚠️  WARNING: {capabilities.get('reason', 'Mode not available')}\n"
        elif not capabilities.get("meets_requirements"):
            feedback_text += "⚠️  WARNING: This mode may not meet high-level reasoning requirements\n"
        else:
            feedback_text += "✅ Mode meets requirements\n"
        
        if capabilities.get("cost_warning"):
            feedback_text += f"💰 {capabilities['cost_warning']}\n"
        
        print(feedback_text)
    
    def _disable_mode(self):
        """Allow user to disable a mode"""
        current_mode = self.selected_mode.get()
        if current_mode == "auto":
            messagebox.showinfo("Info", "Cannot disable auto-select mode")
            return
        
        confirm = messagebox.askyesno(
            "Disable Mode",
            f"Disable {current_mode} mode? This will prevent it from being used or recommended."
        )
        
        if confirm:
            disabled_modes = self.config.setdefault("user_preferences", {}).setdefault("disabled_modes", [])
            if current_mode not in disabled_modes:
                disabled_modes.append(current_mode)
            
            # Re-analyze with new preferences
            self.decision_engine = IntelligentModeDecision(self.config.get("user_preferences", {}))
            self._analyze_modes_async()
            
            # Switch to auto mode
            self.selected_mode.set("auto")
            self._auto_select_mode()
    
    def _open_preferences(self):
        """Open user preferences dialog"""
        messagebox.showinfo("Preferences", "User preferences dialog would open here")
    
    def _show_analysis_error(self, error):
        """Show analysis error in status"""
        if hasattr(self, 'status_text'):
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(1.0, f"Analysis error: {error}")
    
    def _configure_mode(self):
        """Open configuration dialog for the selected mode"""
        selected = self.get_selected_mode()
        messagebox.showinfo("Configuration", f"Configuration for {selected} mode would open here")
    
    def get_selected_mode(self):
        """Get the currently selected or auto-determined mode"""
        if self.selected_mode.get() == "auto":
            recommendation = self.decision_engine.recommend_mode()
            return recommendation.get("mode", "claude_code")  # Default fallback
        return self.selected_mode.get()
    
    def get_mode_analysis(self):
        """Get detailed analysis of current mode selection"""
        return {
            "selected_mode": self.get_selected_mode(),
            "capabilities": self.decision_engine.mode_capabilities,
            "costs": self.decision_engine.cost_analysis,
            "recommendation": self.decision_engine.recommend_mode(),
            "auto_decide_enabled": self.auto_decide_enabled.get()
        }
    
    def set_mode(self, mode):
        """Set the agent mode programmatically"""
        if mode in ["api_key", "vscode", "claude_code", "auto"]:
            self.selected_mode.set(mode)
            self._on_mode_change()