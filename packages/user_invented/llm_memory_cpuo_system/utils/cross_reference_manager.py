"""
Cross-Reference Manager for Project Utilities
Links and tracks relationships between different utilities
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set

class CrossReferenceManager:
    """Manages cross-references between project utilities"""
    
    def __init__(self):
        self.utils_dir = Path(__file__).parent
        self.project_root = self.utils_dir.parent
        self.reference_map_file = self.utils_dir / "utility_cross_references.json"
        self.load_references()
        
    def load_references(self):
        """Load existing cross-references"""
        if self.reference_map_file.exists():
            with open(self.reference_map_file, 'r') as f:
                self.references = json.load(f)
        else:
            self.references = {
                "utilities": {},
                "categories": {
                    "workflow": [],
                    "testing": [],
                    "gui": [],
                    "integration": [],
                    "monitoring": []
                },
                "relationships": []
            }
            
    def analyze_utility_relationships(self):
        """Analyze all utilities and their relationships"""
        utilities = {}
        
        # Scan all Python files in utils
        for util_file in self.utils_dir.glob("*.py"):
            if util_file.name == "__init__.py":
                continue
                
            util_name = util_file.stem
            utilities[util_name] = {
                "file": util_file.name,
                "imports": [],
                "references": [],
                "category": self.categorize_utility(util_name),
                "created": datetime.fromtimestamp(util_file.stat().st_ctime).isoformat()
            }
            
            # Analyze imports and references
            try:
                with open(util_file, 'r') as f:
                    content = f.read()
                    
                # Find imports from other utils
                import_lines = [line for line in content.split('\n') if 'from utils.' in line or 'import utils.' in line]
                for line in import_lines:
                    if 'from utils.' in line:
                        parts = line.split('from utils.')[1].split(' import')[0]
                        if parts != util_name:
                            utilities[util_name]["imports"].append(parts)
                            
                # Find string references to other utilities
                for other_util in self.utils_dir.glob("*.py"):
                    other_name = other_util.stem
                    if other_name != util_name and other_name in content:
                        utilities[util_name]["references"].append(other_name)
                        
            except Exception as e:
                print(f"Error analyzing {util_name}: {e}")
                
        self.references["utilities"] = utilities
        self.update_categories()
        self.find_relationships()
        
    def categorize_utility(self, util_name: str) -> str:
        """Categorize utility based on name and content"""
        name_lower = util_name.lower()
        
        if any(word in name_lower for word in ["workflow", "manager", "ai"]):
            return "workflow"
        elif any(word in name_lower for word in ["test", "check", "validate"]):
            return "testing"
        elif any(word in name_lower for word in ["gui", "interface", "display"]):
            return "gui"
        elif any(word in name_lower for word in ["integration", "patch", "bridge"]):
            return "integration"
        elif any(word in name_lower for word in ["monitor", "track", "log"]):
            return "monitoring"
        else:
            return "general"
            
    def update_categories(self):
        """Update category listings"""
        for category in self.references["categories"]:
            self.references["categories"][category] = []
            
        for util_name, util_data in self.references["utilities"].items():
            category = util_data["category"]
            if category in self.references["categories"]:
                self.references["categories"][category].append(util_name)
                
    def find_relationships(self):
        """Find relationships between utilities"""
        relationships = []
        
        for util_name, util_data in self.references["utilities"].items():
            # Direct imports create strong relationships
            for imported in util_data["imports"]:
                relationships.append({
                    "from": util_name,
                    "to": imported,
                    "type": "imports",
                    "strength": "strong"
                })
                
            # References create weak relationships
            for referenced in util_data["references"]:
                # Avoid duplicates from imports
                if referenced not in util_data["imports"]:
                    relationships.append({
                        "from": util_name,
                        "to": referenced,
                        "type": "references",
                        "strength": "weak"
                    })
                    
        self.references["relationships"] = relationships
        
    def get_related_utilities(self, utility_name: str) -> Dict[str, List[str]]:
        """Get utilities related to a specific utility"""
        related = {
            "imports": [],
            "imported_by": [],
            "references": [],
            "referenced_by": [],
            "same_category": []
        }
        
        # Find direct relationships
        for rel in self.references["relationships"]:
            if rel["from"] == utility_name:
                if rel["type"] == "imports":
                    related["imports"].append(rel["to"])
                else:
                    related["references"].append(rel["to"])
            elif rel["to"] == utility_name:
                if rel["type"] == "imports":
                    related["imported_by"].append(rel["from"])
                else:
                    related["referenced_by"].append(rel["from"])
                    
        # Find same category utilities
        if utility_name in self.references["utilities"]:
            category = self.references["utilities"][utility_name]["category"]
            related["same_category"] = [
                util for util in self.references["categories"].get(category, [])
                if util != utility_name
            ]
            
        return related
        
    def generate_cross_reference_report(self):
        """Generate a comprehensive cross-reference report"""
        report_path = self.project_root / "docs" / "UTILITY_CROSS_REFERENCE_REPORT.md"
        
        report_content = """# Utility Cross-Reference Report

## Overview

This report shows the relationships between all utilities in the `/utils/` directory.

## Utility Categories

"""
        
        # Add categories
        for category, utils in self.references["categories"].items():
            if utils:
                report_content += f"### {category.title()}\n"
                for util in sorted(utils):
                    util_data = self.references["utilities"][util]
                    report_content += f"- **{util}** - {util_data['file']}\n"
                report_content += "\n"
                
        # Add relationships
        report_content += """## Utility Relationships

### Import Dependencies
"""
        
        # Group by utility
        for util_name, util_data in sorted(self.references["utilities"].items()):
            if util_data["imports"]:
                report_content += f"\n**{util_name}** imports:\n"
                for imp in util_data["imports"]:
                    report_content += f"  - {imp}\n"
                    
        # Add relationship graph
        report_content += """
## Relationship Graph

```
"""
        # Simple ASCII representation
        processed = set()
        for rel in self.references["relationships"]:
            if rel["type"] == "imports" and rel["from"] not in processed:
                report_content += f"{rel['from']} --> {rel['to']}\n"
                processed.add(rel["from"])
                
        report_content += """```

## Integration Points

Key utilities that connect multiple components:
"""
        
        # Find utilities with most connections
        connection_counts = {}
        for util_name in self.references["utilities"]:
            related = self.get_related_utilities(util_name)
            count = len(related["imports"]) + len(related["imported_by"])
            connection_counts[util_name] = count
            
        # Top 5 most connected
        top_connected = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for util, count in top_connected:
            report_content += f"- **{util}** - {count} connections\n"
            
        report_content += f"""

## Recent Additions

Utilities added in the last 7 days:
"""
        
        # Find recent utilities
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)
        
        recent = []
        for util_name, util_data in self.references["utilities"].items():
            try:
                created = datetime.fromisoformat(util_data["created"])
                if created > week_ago:
                    recent.append((util_name, created))
            except:
                pass
                
        for util, created in sorted(recent, key=lambda x: x[1], reverse=True):
            report_content += f"- {util} - {created.strftime('%Y-%m-%d')}\n"
            
        report_content += f"""

Generated by Cross-Reference Manager
Date: {datetime.now().isoformat()}
"""
        
        with open(report_path, 'w') as f:
            f.write(report_content)
            
        return report_path
        
    def save_references(self):
        """Save the reference map"""
        with open(self.reference_map_file, 'w') as f:
            json.dump(self.references, f, indent=2)
            
    def link_with_procedure_system(self):
        """Special integration with Project Improvement Procedure"""
        # Add specific link
        if "project_improvement_procedure" in self.references["utilities"]:
            self.references["utilities"]["project_improvement_procedure"]["special_role"] = (
                "Central coordinator for all improvement requests. "
                "Automatically creates utilities and links them together."
            )
            
            # Mark as hub utility
            self.references["utilities"]["project_improvement_procedure"]["is_hub"] = True
            
        self.save_references()


def main():
    """Run cross-reference analysis"""
    print("=== Cross-Reference Manager ===\n")
    
    manager = CrossReferenceManager()
    
    print("Analyzing utility relationships...")
    manager.analyze_utility_relationships()
    
    print(f"Found {len(manager.references['utilities'])} utilities")
    print(f"Found {len(manager.references['relationships'])} relationships")
    
    # Generate report
    report_path = manager.generate_cross_reference_report()
    print(f"\nGenerated report: {report_path}")
    
    # Link with procedure system
    manager.link_with_procedure_system()
    
    # Save references
    manager.save_references()
    print("\nSaved cross-reference map")
    
    # Example: Get related utilities
    if "project_improvement_procedure" in manager.references["utilities"]:
        related = manager.get_related_utilities("project_improvement_procedure")
        print("\nUtilities related to project_improvement_procedure:")
        for rel_type, utils in related.items():
            if utils:
                print(f"  {rel_type}: {', '.join(utils)}")


if __name__ == "__main__":
    main()