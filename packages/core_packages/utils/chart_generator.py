# Chart Generator for GlowingGoldenGlobe

This module provides tools for automatically generating system architecture charts
for the GlowingGoldenGlobe project. It analyzes the project structure, identifies
AI Managers and implementation components, and creates visual representations of their
relationships.

import os
import ast
import re
import json
import importlib.util
from pathlib import Path

class ComponentType:
    """Define component types for the system architecture"""
    AI_MANAGER = "ai_manager"
    IMPLEMENTATION = "implementation"
    PYAUTOGEN = "pyautogen"
    EXTERNAL = "external"

class ChartGenerator:
    """Generates system architecture charts for GlowingGoldenGlobe"""

    def __init__(self, project_root):
        """
        Initialize the chart generator
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.components = []
        self.relationships = []
        self.component_map = {}  # Map of component paths to IDs
    
    def collect_data(self):
        """Collect data about project components and their relationships"""
        # Find all Python files in the project
        for py_file in self.project_root.glob("**/*.py"):
            self._process_file(py_file)
        
        # Find relationships between components
        self._analyze_relationships()
        
        return self.components, self.relationships
    
    def _process_file(self, file_path):
        """
        Process a Python file to extract component information
        
        Args:
            file_path: Path to the Python file
        """
        rel_path = file_path.relative_to(self.project_root)
        file_id = f"comp_{len(self.components)}"
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine component type based on file content and name
            component_type = self._determine_component_type(file_path.name, content)
            
            # Create component
            component = {
                "id": file_id,
                "name": file_path.name,
                "path": str(rel_path),
                "type": component_type,
                "classes": self._extract_classes(content),
                "functions": self._extract_functions(content)
            }
            
            self.components.append(component)
            self.component_map[str(rel_path)] = file_id
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    def _determine_component_type(self, filename, content):
        """
        Determine the type of component based on file content
        
        Args:
            filename: Name of the file
            content: Content of the file
        
        Returns:
            ComponentType value
        """
        # AI Manager heuristics
        if "ai_manager" in filename.lower() or "resource_manager" in filename.lower():
            return ComponentType.AI_MANAGER
        
        # Check for AI Manager characteristics
        if "class" in content and (
            ("Manager" in content and "def assess" in content) or
            ("make_decision" in content) or
            ("evaluate" in content and "def decide" in content)
        ):
            return ComponentType.AI_MANAGER
        
        # PyAutoGen components
        if "pyautogen" in content or "autogen" in content:
            return ComponentType.PYAUTOGEN
            
        # Default to implementation
        return ComponentType.IMPLEMENTATION
    
    def _extract_classes(self, content):
        """Extract class names from Python content"""
        try:
            tree = ast.parse(content)
            return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        except:
            # Fallback to regex if parsing fails
            class_matches = re.findall(r'class\s+(\w+)', content)
            return class_matches
    
    def _extract_functions(self, content):
        """Extract function names from Python content"""
        try:
            tree = ast.parse(content)
            return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        except:
            # Fallback to regex if parsing fails
            function_matches = re.findall(r'def\s+(\w+)', content)
            return function_matches
    
    def _analyze_relationships(self):
        """Analyze relationships between components"""
        # Process each component for imports and function calls
        for component in self.components:
            file_path = os.path.join(self.project_root, component["path"])
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find imports
                import_matches = re.findall(r'(?:from|import)\s+([\w\.]+)', content)
                
                for imported in import_matches:
                    # Find the component that corresponds to the import
                    for target_comp in self.components:
                        target_path = os.path.splitext(target_comp["path"])[0].replace('/', '.')
                        
                        if imported == target_path or imported in target_path:
                            relationship = {
                                "source": component["id"],
                                "target": target_comp["id"],
                                "label": "imports",
                                "type": "import"
                            }
                            self.relationships.append(relationship)
                
                # Check for known reporting patterns
                for target_comp in self.components:
                    if target_comp["type"] == ComponentType.AI_MANAGER:
                        for target_class in target_comp["classes"]:
                            # Check if this component reports to an AI Manager
                            pattern = f"{target_class}|{os.path.basename(target_comp['path'])}"
                            if re.search(pattern, content):
                                relationship = {
                                    "source": component["id"],
                                    "target": target_comp["id"],
                                    "label": "reports to",
                                    "type": "reporting"
                                }
                                self.relationships.append(relationship)
            
            except Exception as e:
                print(f"Error analyzing relationships in {file_path}: {str(e)}")
    
    def generate_ai_manager_chart(self):
        """Generate Mermaid chart for AI Managers"""
        mermaid_code = "flowchart TB\n"
        mermaid_code += "    classDef aiManager fill:#f96,stroke:#333,stroke-width:2px\n"
        mermaid_code += "    classDef implementation fill:#9cf,stroke:#333,stroke-width:1px\n\n"
        
        # Add components
        ai_managers = []
        implementations = []
        
        for component in self.components:
            if component["type"] == ComponentType.AI_MANAGER:
                name = os.path.splitext(component["name"])[0]
                mermaid_code += f"    {component['id']}[{name}] :::aiManager\n"
                ai_managers.append(component['id'])
            elif component["type"] == ComponentType.IMPLEMENTATION:
                name = os.path.splitext(component["name"])[0]
                mermaid_code += f"    {component['id']}[{name}] :::implementation\n"
                implementations.append(component['id'])
        
        # Add relationships
        for rel in self.relationships:
            if rel["source"] in implementations and rel["target"] in ai_managers:
                mermaid_code += f"    {rel['source']} -->|{rel['label']}| {rel['target']}\n"
            elif rel["source"] in ai_managers and rel["target"] in ai_managers:
                mermaid_code += f"    {rel['source']} -.->|coordinates with| {rel['target']}\n"
        
        # Add groups
        if ai_managers:
            mermaid_code += "\n    subgraph AI_Managers [\"AI Managers (Decision Makers)\"]\n"
            for comp_id in ai_managers:
                mermaid_code += f"        {comp_id}\n"
            mermaid_code += "    end\n"
        
        if implementations:
            mermaid_code += "\n    subgraph Implementation_Modules [\"Implementation Modules\"]\n"
            for comp_id in implementations:
                mermaid_code += f"        {comp_id}\n"
            mermaid_code += "    end\n"
        
        return mermaid_code
    
    def generate_system_architecture_chart(self):
        """Generate Mermaid chart for complete system architecture"""
        mermaid_code = "flowchart TD\n"
        mermaid_code += "    classDef aiManager fill:#f96,stroke:#333,stroke-width:2px\n"
        mermaid_code += "    classDef implementation fill:#9cf,stroke:#333,stroke-width:1px\n"
        mermaid_code += "    classDef pyautogen fill:#c9f,stroke:#333,stroke-width:2px\n"
        mermaid_code += "    classDef external fill:#cfc,stroke:#333,stroke-width:1px\n\n"
        
        # External systems (hardcoded for now)
        mermaid_code += "    %% External Systems\n"
        mermaid_code += "    BLENDER[Blender\\n3D Engine] :::external\n"
        mermaid_code += "    O3DE[O3DE\\nSimulation Engine] :::external\n"
        mermaid_code += "    ROS[ROS2\\nRobotics] :::external\n\n"
        
        # Add components by type
        ai_managers = []
        implementations = {}  # Group implementations by category
        pyautogen_comps = []
        
        for component in self.components:
            name = os.path.splitext(component["name"])[0]
            
            if component["type"] == ComponentType.AI_MANAGER:
                mermaid_code += f"    {component['id']}[{name}] :::aiManager\n"
                ai_managers.append(component['id'])
            
            elif component["type"] == ComponentType.PYAUTOGEN:
                mermaid_code += f"    {component['id']}[{name}] :::pyautogen\n"
                pyautogen_comps.append(component['id'])
            
            elif component["type"] == ComponentType.IMPLEMENTATION:
                # Categorize implementation component
                category = self._categorize_implementation(component)
                
                if category not in implementations:
                    implementations[category] = []
                
                implementations[category].append((component['id'], name))
        
        # Add relationships
        mermaid_code += "\n    %% Connections\n"
        for rel in self.relationships:
            mermaid_code += f"    {rel['source']} --> {rel['target']}\n"
        
        # Add groups
        mermaid_code += "\n    %% Component Groups\n"
        
        # AI Managers group
        if ai_managers:
            mermaid_code += "    subgraph AI_Managers [AI Manager Subsystem]\n"
            for comp_id in ai_managers:
                mermaid_code += f"        {comp_id}\n"
            mermaid_code += "    end\n\n"
        
        # PyAutoGen group
        if pyautogen_comps:
            mermaid_code += "    subgraph PyAutoGen_System [PyAutoGen Integration]\n"
            for comp_id in pyautogen_comps:
                mermaid_code += f"        {comp_id}\n"
            mermaid_code += "    end\n\n"
        
        # Implementation groups
        for category, comps in implementations.items():
            mermaid_code += f"    subgraph {category.replace(' ', '_')} [{category}]\n"
            for comp_id, name in comps:
                mermaid_code += f"        {comp_id}\n"
            mermaid_code += "    end\n\n"
        
        return mermaid_code
    
    def _categorize_implementation(self, component):
        """Categorize implementation component based on name and content"""
        name = component["name"].lower()
        
        if "gui" in name or "interface" in name:
            return "User Interface"
        elif "hardware" in name or "gpu" in name or "resource" in name:
            return "Hardware & Resources"
        elif "blender" in name or "render" in name or "model" in name:
            return "Rendering & Modeling"
        else:
            return "Core Implementation"

    def save_chart(self, chart_type, output_path):
        """
        Generate and save a chart
        
        Args:
            chart_type: Type of chart to generate ('ai_manager' or 'system')
            output_path: Path to save the chart markdown
        """
        if not self.components:
            self.collect_data()
        
        if chart_type == 'ai_manager':
            mermaid_code = self.generate_ai_manager_chart()
            title = "# GlowingGoldenGlobe AI Managers Chart"
        else:  # system
            mermaid_code = self.generate_system_architecture_chart()
            title = "# GlowingGoldenGlobe Complete System Architecture"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"{title}\n\n```mermaid\n{mermaid_code}\n```\n")
        
        return output_path

# Example usage
if __name__ == "__main__":
    generator = ChartGenerator(".")
    generator.collect_data()
    
    # Generate and save charts
    ai_chart_path = generator.save_chart('ai_manager', 'docs/generated_ai_managers_chart.md')
    sys_chart_path = generator.save_chart('system', 'docs/generated_system_architecture.md')
    
    print(f"AI Managers Chart saved to: {ai_chart_path}")
    print(f"System Architecture Chart saved to: {sys_chart_path}")
