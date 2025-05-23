#!/usr/bin/env python
"""
Assessment-Based Cleanup System for /utils/ folder
Implements comprehensive cleanup criteria for AI Workflow automation
"""

import os
import json
import time
import hashlib
import difflib
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AssessmentCleanup")

class AssessmentBasedCleanup:
    """Comprehensive assessment-based cleanup for /utils/ folder"""
    
    def __init__(self, utils_dir: str = None):
        """Initialize the assessment-based cleanup system"""
        if utils_dir is None:
            utils_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.utils_dir = Path(utils_dir)
        self.base_dir = self.utils_dir.parent
        
        # Cleanup criteria thresholds
        self.criteria = {
            "duplicate_similarity_threshold": 0.95,  # Content similarity for duplicates
            "session_inactivity_days": 30,           # Days without activity
            "temp_file_age_days": 7,                 # Age for temp files
            "obsolete_patterns": [
                "temp_", "tmp_", "test_", "_backup", "_old", "_temp",
                ".bak", ".tmp", ".cache", "_cache"
            ]
        }
        
        # File patterns to check
        self.target_extensions = [".py", ".bat", ".sh", ".ps1", ".txt", ".json", ".log"]
        
        # Results storage
        self.assessment_results = {}
        
    def run_full_assessment(self) -> Dict[str, Any]:
        """Run complete assessment on /utils/ folder"""
        logger.info("Starting comprehensive assessment-based cleanup")
        
        # Get all files in utils directory
        files = self._get_target_files()
        
        assessment_results = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(files),
            "assessment_criteria": {},
            "cleanup_recommendations": [],
            "files_to_preserve": [],
            "files_to_archive": [],
            "files_to_delete": []
        }
        
        # Apply each assessment criterion
        for file_path in files:
            file_assessment = self._assess_single_file(file_path)
            
            # Determine action based on assessment
            action = self._determine_cleanup_action(file_assessment)
            
            if action == "delete":
                assessment_results["files_to_delete"].append({
                    "path": str(file_path),
                    "reason": file_assessment["cleanup_reason"],
                    "assessment": file_assessment
                })
            elif action == "archive":
                assessment_results["files_to_archive"].append({
                    "path": str(file_path),
                    "reason": file_assessment["cleanup_reason"],
                    "assessment": file_assessment
                })
            else:
                assessment_results["files_to_preserve"].append({
                    "path": str(file_path),
                    "assessment": file_assessment
                })
        
        # Add duplicate analysis
        assessment_results["assessment_criteria"]["duplicates"] = self._assess_duplicates(files)
        
        # Add workflow completion analysis
        assessment_results["assessment_criteria"]["workflow_completion"] = self._assess_workflow_completion(files)
        
        # Add corruption analysis
        assessment_results["assessment_criteria"]["corruption"] = self._assess_file_corruption(files)
        
        # Add obsolete file analysis
        assessment_results["assessment_criteria"]["obsolete_files"] = self._assess_obsolete_files(files)
        
        # Add session activity analysis
        assessment_results["assessment_criteria"]["session_activity"] = self._assess_session_activity(files)
        
        # Generate cleanup recommendations
        assessment_results["cleanup_recommendations"] = self._generate_recommendations(assessment_results)
        
        self.assessment_results = assessment_results
        return assessment_results
    
    def _get_target_files(self) -> List[Path]:
        """Get all target files in /utils/ directory"""
        files = []
        for ext in self.target_extensions:
            files.extend(self.utils_dir.glob(f"*{ext}"))
        return sorted(files)
    
    def _assess_single_file(self, file_path: Path) -> Dict[str, Any]:
        """Assess a single file against all criteria"""
        try:
            stat = file_path.stat()
            
            assessment = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size": stat.st_size,
                "created_time": datetime.fromtimestamp(stat.st_ctime),
                "modified_time": datetime.fromtimestamp(stat.st_mtime),
                "accessed_time": datetime.fromtimestamp(stat.st_atime),
                "is_duplicate": False,
                "is_completed_workflow": False,
                "is_corrupted": False,
                "is_obsolete": False,
                "has_recent_activity": False,
                "cleanup_reason": None,
                "file_hash": self._calculate_file_hash(file_path)
            }
            
            # Check age-based criteria
            now = datetime.now()
            days_since_modified = (now - assessment["modified_time"]).days
            days_since_accessed = (now - assessment["accessed_time"]).days
            
            assessment["days_since_modified"] = days_since_modified
            assessment["days_since_accessed"] = days_since_accessed
            
            # Check if file has recent activity
            assessment["has_recent_activity"] = (
                days_since_modified <= self.criteria["session_inactivity_days"] or
                days_since_accessed <= self.criteria["session_inactivity_days"]
            )
            
            # Check for obsolete patterns
            assessment["is_obsolete"] = any(
                pattern in file_path.name.lower() 
                for pattern in self.criteria["obsolete_patterns"]
            )
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error assessing file {file_path}: {e}")
            return {"error": str(e), "file_path": str(file_path)}
    
    def _assess_duplicates(self, files: List[Path]) -> Dict[str, Any]:
        """Assess files for duplicates using content comparison"""
        duplicates = []
        file_hashes = {}
        content_similarity = []
        
        # Hash-based duplicate detection
        for file_path in files:
            try:
                file_hash = self._calculate_file_hash(file_path)
                if file_hash in file_hashes:
                    duplicates.append({
                        "original": file_hashes[file_hash],
                        "duplicate": str(file_path),
                        "type": "exact_hash_match"
                    })
                else:
                    file_hashes[file_hash] = str(file_path)
            except Exception as e:
                logger.error(f"Error hashing file {file_path}: {e}")
        
        # Content similarity for text files
        text_files = [f for f in files if f.suffix in ['.py', '.txt', '.ps1', '.sh', '.bat']]
        
        for i, file1 in enumerate(text_files):
            for file2 in text_files[i+1:]:
                try:
                    similarity = self._calculate_content_similarity(file1, file2)
                    if similarity >= self.criteria["duplicate_similarity_threshold"]:
                        content_similarity.append({
                            "file1": str(file1),
                            "file2": str(file2),
                            "similarity": similarity,
                            "type": "content_similarity"
                        })
                except Exception as e:
                    logger.error(f"Error comparing {file1} and {file2}: {e}")
        
        return {
            "exact_duplicates": duplicates,
            "similar_content": content_similarity,
            "total_duplicate_sets": len(duplicates) + len(content_similarity)
        }
    
    def _assess_workflow_completion(self, files: List[Path]) -> Dict[str, Any]:
        """Assess if files are from completed workflows"""
        completed_workflows = []
        active_workflows = []
        
        # Check for workflow indicators
        for file_path in files:
            try:
                # Look for workflow completion indicators
                is_completed = self._check_workflow_completion(file_path)
                
                if is_completed:
                    completed_workflows.append({
                        "file": str(file_path),
                        "completion_indicators": is_completed
                    })
                else:
                    active_workflows.append(str(file_path))
                    
            except Exception as e:
                logger.error(f"Error checking workflow completion for {file_path}: {e}")
        
        return {
            "completed_workflow_files": completed_workflows,
            "active_workflow_files": active_workflows,
            "completion_ratio": len(completed_workflows) / len(files) if files else 0
        }
    
    def _assess_file_corruption(self, files: List[Path]) -> Dict[str, Any]:
        """Assess files for corruption or validity issues"""
        corrupted_files = []
        valid_files = []
        
        for file_path in files:
            try:
                is_valid = self._check_file_validity(file_path)
                
                if is_valid:
                    valid_files.append(str(file_path))
                else:
                    corrupted_files.append({
                        "file": str(file_path),
                        "issue": "Invalid or corrupted"
                    })
                    
            except Exception as e:
                corrupted_files.append({
                    "file": str(file_path),
                    "issue": f"Error during validation: {e}"
                })
        
        return {
            "corrupted_files": corrupted_files,
            "valid_files": valid_files,
            "corruption_rate": len(corrupted_files) / len(files) if files else 0
        }
    
    def _assess_obsolete_files(self, files: List[Path]) -> Dict[str, Any]:
        """Assess files for obsolete patterns and characteristics"""
        obsolete_files = []
        current_files = []
        
        for file_path in files:
            try:
                is_obsolete = self._check_if_obsolete(file_path)
                
                if is_obsolete:
                    obsolete_files.append({
                        "file": str(file_path),
                        "obsolete_reason": is_obsolete
                    })
                else:
                    current_files.append(str(file_path))
                    
            except Exception as e:
                logger.error(f"Error checking obsolete status for {file_path}: {e}")
        
        return {
            "obsolete_files": obsolete_files,
            "current_files": current_files,
            "obsolete_ratio": len(obsolete_files) / len(files) if files else 0
        }
    
    def _assess_session_activity(self, files: List[Path]) -> Dict[str, Any]:
        """Assess files for recent session activity"""
        recent_activity = []
        inactive_files = []
        
        cutoff_date = datetime.now() - timedelta(days=self.criteria["session_inactivity_days"])
        
        for file_path in files:
            try:
                stat = file_path.stat()
                last_modified = datetime.fromtimestamp(stat.st_mtime)
                last_accessed = datetime.fromtimestamp(stat.st_atime)
                
                has_activity = (last_modified > cutoff_date or last_accessed > cutoff_date)
                
                if has_activity:
                    recent_activity.append({
                        "file": str(file_path),
                        "last_modified": last_modified.isoformat(),
                        "last_accessed": last_accessed.isoformat()
                    })
                else:
                    inactive_files.append({
                        "file": str(file_path),
                        "last_modified": last_modified.isoformat(),
                        "last_accessed": last_accessed.isoformat(),
                        "days_inactive": (datetime.now() - max(last_modified, last_accessed)).days
                    })
                    
            except Exception as e:
                logger.error(f"Error checking activity for {file_path}: {e}")
        
        return {
            "recent_activity_files": recent_activity,
            "inactive_files": inactive_files,
            "activity_ratio": len(recent_activity) / len(files) if files else 0
        }
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return "hash_error"
    
    def _calculate_content_similarity(self, file1: Path, file2: Path) -> float:
        """Calculate content similarity between two text files"""
        try:
            with open(file1, 'r', encoding='utf-8', errors='ignore') as f1:
                content1 = f1.read()
            with open(file2, 'r', encoding='utf-8', errors='ignore') as f2:
                content2 = f2.read()
            
            # Use difflib for similarity calculation
            similarity = difflib.SequenceMatcher(None, content1, content2).ratio()
            return similarity
            
        except Exception:
            return 0.0
    
    def _check_workflow_completion(self, file_path: Path) -> Optional[List[str]]:
        """Check if file indicates completed workflow"""
        indicators = []
        
        # Check filename patterns
        name_lower = file_path.name.lower()
        if any(pattern in name_lower for pattern in ["completed", "done", "finished", "final"]):
            indicators.append("filename_indicates_completion")
        
        # Check file age (older files more likely to be completed)
        stat = file_path.stat()
        days_old = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
        if days_old > 30:
            indicators.append("file_age_indicates_completion")
        
        # Check for specific content patterns in text files
        if file_path.suffix in ['.py', '.txt', '.ps1', '.sh', '.bat']:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    if any(word in content for word in ["completed", "finished", "deprecated", "legacy"]):
                        indicators.append("content_indicates_completion")
            except Exception:
                pass
        
        return indicators if indicators else None
    
    def _check_file_validity(self, file_path: Path) -> bool:
        """Check if file is valid and not corrupted"""
        try:
            # Basic existence and readability check
            if not file_path.exists() or file_path.stat().st_size == 0:
                return False
            
            # Syntax check for Python files
            if file_path.suffix == '.py':
                try:
                    result = subprocess.run(
                        ['python', '-m', 'py_compile', str(file_path)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    return result.returncode == 0
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
            
            # Basic readability test for text files
            if file_path.suffix in ['.txt', '.ps1', '.sh', '.bat']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        f.read(1024)  # Try to read first 1KB
                    return True
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='latin-1') as f:
                            f.read(1024)
                        return True
                    except Exception:
                        return False
            
            return True
            
        except Exception:
            return False
    
    def _check_if_obsolete(self, file_path: Path) -> Optional[str]:
        """Check if file is obsolete based on patterns and characteristics"""
        name_lower = file_path.name.lower()
        
        # Check filename patterns
        for pattern in self.criteria["obsolete_patterns"]:
            if pattern in name_lower:
                return f"obsolete_pattern_{pattern}"
        
        # Check for very old temporary files
        stat = file_path.stat()
        days_old = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
        
        if any(temp_pattern in name_lower for temp_pattern in ["temp", "tmp", "test"]):
            if days_old > self.criteria["temp_file_age_days"]:
                return f"old_temporary_file_{days_old}_days"
        
        # Check for zero-byte files
        if stat.st_size == 0:
            return "zero_byte_file"
        
        return None
    
    def _determine_cleanup_action(self, assessment: Dict[str, Any]) -> str:
        """Determine cleanup action based on assessment"""
        if "error" in assessment:
            return "preserve"  # Don't touch files with assessment errors
        
        # High-priority deletion criteria
        if assessment.get("is_corrupted", False):
            assessment["cleanup_reason"] = "File is corrupted or invalid"
            return "delete"
        
        if assessment.get("file_size", 0) == 0:
            assessment["cleanup_reason"] = "Zero-byte file"
            return "delete"
        
        # Obsolete file handling
        if assessment.get("is_obsolete", False):
            if assessment.get("days_since_accessed", 0) > self.criteria["temp_file_age_days"]:
                assessment["cleanup_reason"] = "Obsolete file with no recent access"
                return "delete"
            else:
                assessment["cleanup_reason"] = "Obsolete file but recently accessed"
                return "archive"
        
        # Archive criteria
        if (assessment.get("is_completed_workflow", False) and 
            not assessment.get("has_recent_activity", False)):
            assessment["cleanup_reason"] = "Completed workflow with no recent activity"
            return "archive"
        
        if assessment.get("days_since_accessed", 0) > self.criteria["session_inactivity_days"] * 2:
            assessment["cleanup_reason"] = f"No access for {assessment.get('days_since_accessed')} days"
            return "archive"
        
        # Preserve by default
        return "preserve"
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate cleanup recommendations based on assessment"""
        recommendations = []
        
        # Duplicate recommendations
        duplicate_criteria = results["assessment_criteria"]["duplicates"]
        if duplicate_criteria["total_duplicate_sets"] > 0:
            recommendations.append(f"Found {duplicate_criteria['total_duplicate_sets']} duplicate file sets - consider removing redundant copies")
        
        # Obsolete file recommendations
        obsolete_criteria = results["assessment_criteria"]["obsolete_files"]
        if obsolete_criteria["obsolete_ratio"] > 0.3:
            recommendations.append(f"High obsolete file ratio ({obsolete_criteria['obsolete_ratio']:.1%}) - cleanup recommended")
        
        # Corruption recommendations
        corruption_criteria = results["assessment_criteria"]["corruption"]
        if corruption_criteria["corruption_rate"] > 0:
            recommendations.append(f"Found {len(corruption_criteria['corrupted_files'])} corrupted files - immediate removal recommended")
        
        # Activity recommendations
        activity_criteria = results["assessment_criteria"]["session_activity"]
        if activity_criteria["activity_ratio"] < 0.5:
            recommendations.append(f"Low activity ratio ({activity_criteria['activity_ratio']:.1%}) - consider archiving inactive files")
        
        # Overall recommendations
        total_to_clean = len(results["files_to_delete"]) + len(results["files_to_archive"])
        if total_to_clean > 0:
            recommendations.append(f"Total files recommended for cleanup: {total_to_clean}")
        
        return recommendations
    
    def execute_cleanup(self, dry_run: bool = True) -> Dict[str, Any]:
        """Execute the cleanup based on assessment results"""
        if not self.assessment_results:
            raise ValueError("No assessment results available. Run run_full_assessment() first.")
        
        execution_log = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "actions_taken": [],
            "errors": []
        }
        
        # Create archive directory if needed
        archive_dir = self.utils_dir / "archived_files"
        
        if not dry_run and self.assessment_results["files_to_archive"]:
            archive_dir.mkdir(exist_ok=True)
        
        # Process files to delete
        for file_info in self.assessment_results["files_to_delete"]:
            try:
                file_path = Path(file_info["path"])
                if dry_run:
                    execution_log["actions_taken"].append(f"WOULD DELETE: {file_path} - {file_info['reason']}")
                else:
                    file_path.unlink()
                    execution_log["actions_taken"].append(f"DELETED: {file_path} - {file_info['reason']}")
            except Exception as e:
                execution_log["errors"].append(f"Error deleting {file_info['path']}: {e}")
        
        # Process files to archive
        for file_info in self.assessment_results["files_to_archive"]:
            try:
                file_path = Path(file_info["path"])
                archive_path = archive_dir / file_path.name
                
                if dry_run:
                    execution_log["actions_taken"].append(f"WOULD ARCHIVE: {file_path} -> {archive_path} - {file_info['reason']}")
                else:
                    file_path.rename(archive_path)
                    execution_log["actions_taken"].append(f"ARCHIVED: {file_path} -> {archive_path} - {file_info['reason']}")
            except Exception as e:
                execution_log["errors"].append(f"Error archiving {file_info['path']}: {e}")
        
        return execution_log
    
    def save_assessment_report(self, output_path: str = None) -> str:
        """Save assessment results to a JSON report"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.utils_dir / f"cleanup_assessment_report_{timestamp}.json")
        
        try:
            # Convert datetime objects to strings for JSON serialization
            serializable_results = self._make_json_serializable(self.assessment_results)
            
            with open(output_path, 'w') as f:
                json.dump(serializable_results, f, indent=2)
            
            logger.info(f"Assessment report saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving assessment report: {e}")
            raise
    
    def _make_json_serializable(self, obj):
        """Convert datetime objects to strings for JSON serialization"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        else:
            return obj


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Assessment-based cleanup for /utils/ folder")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without executing")
    parser.add_argument("--execute", action="store_true", help="Execute cleanup actions")
    parser.add_argument("--report-only", action="store_true", help="Generate assessment report only")
    parser.add_argument("--utils-dir", help="Path to utils directory (default: current script directory)")
    
    args = parser.parse_args()
    
    # Initialize cleanup system
    cleanup = AssessmentBasedCleanup(args.utils_dir)
    
    # Run assessment
    print("Running comprehensive assessment...")
    results = cleanup.run_full_assessment()
    
    # Save report
    report_path = cleanup.save_assessment_report()
    print(f"Assessment report saved to: {report_path}")
    
    # Print summary
    print(f"\nAssessment Summary:")
    print(f"Total files assessed: {results['total_files']}")
    print(f"Files to delete: {len(results['files_to_delete'])}")
    print(f"Files to archive: {len(results['files_to_archive'])}")
    print(f"Files to preserve: {len(results['files_to_preserve'])}")
    
    # Print recommendations
    if results['cleanup_recommendations']:
        print(f"\nRecommendations:")
        for rec in results['cleanup_recommendations']:
            print(f"- {rec}")
    
    # Execute cleanup if requested
    if args.execute or args.dry_run:
        print(f"\n{'DRY RUN' if args.dry_run else 'EXECUTING'} cleanup...")
        execution_log = cleanup.execute_cleanup(dry_run=args.dry_run)
        
        if execution_log['actions_taken']:
            print("Actions taken:")
            for action in execution_log['actions_taken']:
                print(f"- {action}")
        
        if execution_log['errors']:
            print("Errors:")
            for error in execution_log['errors']:
                print(f"- {error}")


if __name__ == "__main__":
    main()