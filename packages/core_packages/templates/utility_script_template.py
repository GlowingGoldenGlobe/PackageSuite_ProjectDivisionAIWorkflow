#!/usr/bin/env python
"""
Utility Script Template
Template for creating new utility scripts in the GlowingGoldenGlobe system
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add parent directory for AI workflow integration
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Required AI workflow integration import
from ai_workflow_integration import check_file_access, can_read_file

# Configure logging - REQUIRED PATTERN
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TemplateUtility")

class TemplateUtility:
    """Template Utility for specific operations"""
    
    def __init__(self, config_path: str = None):
        """Initialize the utility"""
        self.base_dir = Path(__file__).parent.parent
        
        if config_path is None:
            config_path = str(self.base_dir / "utils" / "template_utility_config.json")
        
        self.config_path = config_path
        self.config = self._load_config()
        
        # Utility state
        self.results = []
        self.statistics = {
            "processed_count": 0,
            "error_count": 0,
            "start_time": datetime.now()
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration with AI workflow integration"""
        # Check file access
        access_result = check_file_access(self.config_path, "read", "loading utility configuration")
        if not access_result['allowed']:
            if access_result.get('token_saved'):
                logger.info("Config load skipped - token optimization")
            else:
                logger.warning(f"Config access denied: {access_result['reason']}")
            return self._get_default_config()
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
                return config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "version": "1.0.0",
            "settings": {
                "verbose": False,
                "output_format": "json",
                "max_items": 100,
                "timeout_seconds": 30
            },
            "created": datetime.now().isoformat()
        }
    
    def _save_results(self, output_path: str = None) -> str:
        """Save results to file with AI workflow integration"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.base_dir / "utils" / f"template_results_{timestamp}.json")
        
        # Check file access
        access_result = check_file_access(output_path, "write", "saving utility results")
        if not access_result['allowed']:
            if access_result.get('requires_override'):
                logger.error(f"Cannot save results: {access_result['reason']}")
                return None
        
        try:
            output_data = {
                "timestamp": datetime.now().isoformat(),
                "statistics": self.statistics,
                "config": self.config,
                "results": self.results
            }
            
            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            logger.info(f"Results saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return None
    
    def process_item(self, item: Any) -> Dict[str, Any]:
        """Process a single item - IMPLEMENT THIS"""
        try:
            logger.debug(f"Processing item: {item}")
            
            # Example processing logic - REPLACE WITH ACTUAL IMPLEMENTATION
            result = {
                "item": str(item),
                "processed_at": datetime.now().isoformat(),
                "status": "success",
                "data": {
                    "length": len(str(item)),
                    "type": type(item).__name__
                }
            }
            
            self.statistics["processed_count"] += 1
            return result
            
        except Exception as e:
            logger.error(f"Error processing item {item}: {e}")
            self.statistics["error_count"] += 1
            
            return {
                "item": str(item),
                "processed_at": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    def process_batch(self, items: List[Any]) -> Dict[str, Any]:
        """Process a batch of items"""
        logger.info(f"Processing batch of {len(items)} items")
        
        batch_results = []
        batch_start = datetime.now()
        
        for item in items:
            result = self.process_item(item)
            batch_results.append(result)
            self.results.append(result)
        
        batch_duration = (datetime.now() - batch_start).total_seconds()
        
        batch_summary = {
            "batch_size": len(items),
            "processed_count": len([r for r in batch_results if r["status"] == "success"]),
            "error_count": len([r for r in batch_results if r["status"] == "error"]),
            "duration_seconds": batch_duration,
            "items_per_second": len(items) / batch_duration if batch_duration > 0 else 0
        }
        
        logger.info(f"Batch completed: {batch_summary}")
        return batch_summary
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process items from a file with AI workflow integration"""
        # Check file access
        access_result = check_file_access(file_path, "read", "processing utility input file")
        if not access_result['allowed']:
            if access_result.get('token_saved'):
                logger.info(f"File processing skipped - token optimization: {file_path}")
                return {"status": "skipped", "reason": "token_optimization"}
            else:
                logger.error(f"File access denied: {access_result['reason']}")
                return {"status": "error", "reason": access_result['reason']}
        
        try:
            logger.info(f"Processing file: {file_path}")
            
            # Determine file type and load items
            file_path_obj = Path(file_path)
            
            if file_path_obj.suffix.lower() == '.json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    items = data if isinstance(data, list) else [data]
            elif file_path_obj.suffix.lower() == '.txt':
                with open(file_path, 'r') as f:
                    items = [line.strip() for line in f if line.strip()]
            else:
                # Generic text processing
                with open(file_path, 'r') as f:
                    content = f.read()
                    items = [content]
            
            return self.process_batch(items)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return {"status": "error", "error": str(e)}
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a summary report"""
        total_duration = (datetime.now() - self.statistics["start_time"]).total_seconds()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_processed": self.statistics["processed_count"],
                "total_errors": self.statistics["error_count"],
                "total_duration_seconds": total_duration,
                "success_rate": (
                    self.statistics["processed_count"] / 
                    (self.statistics["processed_count"] + self.statistics["error_count"])
                    if (self.statistics["processed_count"] + self.statistics["error_count"]) > 0 
                    else 0
                ),
                "processing_rate": (
                    self.statistics["processed_count"] / total_duration
                    if total_duration > 0 else 0
                )
            },
            "configuration": self.config,
            "results_count": len(self.results)
        }
        
        return report


def main():
    """Main function for CLI usage - REQUIRED PATTERN"""
    parser = argparse.ArgumentParser(description="Template Utility Script")
    
    # Standard arguments
    parser.add_argument("--input", "-i", help="Input file path")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without executing")
    
    # Task-specific arguments - ADD YOUR OWN HERE
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for processing")
    parser.add_argument("--format", choices=["json", "text", "csv"], default="json", help="Output format")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize utility
        utility = TemplateUtility(config_path=args.config)
        
        logger.info("Template Utility started")
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No actual processing will occur")
        
        # Process input
        if args.input:
            if os.path.exists(args.input):
                if not args.dry_run:
                    result = utility.process_file(args.input)
                    logger.info(f"File processing result: {result}")
                else:
                    logger.info(f"Would process file: {args.input}")
            else:
                logger.error(f"Input file not found: {args.input}")
                return 1
        else:
            # Example processing without input file
            example_items = ["item1", "item2", "item3", "item4", "item5"]
            
            if not args.dry_run:
                result = utility.process_batch(example_items)
                logger.info(f"Batch processing result: {result}")
            else:
                logger.info(f"Would process {len(example_items)} example items")
        
        # Generate and display report
        if not args.dry_run:
            report = utility.generate_report()
            
            if args.format == "json":
                print(json.dumps(report, indent=2))
            else:
                # Simple text format
                print(f"\\nSUMMARY REPORT")
                print(f"Processed: {report['summary']['total_processed']}")
                print(f"Errors: {report['summary']['total_errors']}")
                print(f"Success Rate: {report['summary']['success_rate']:.1%}")
                print(f"Duration: {report['summary']['total_duration_seconds']:.2f}s")
            
            # Save results if requested
            if args.output:
                output_path = utility._save_results(args.output)
                if output_path:
                    logger.info(f"Results saved to: {output_path}")
        
        logger.info("Template Utility completed successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Error in main: {e}")
        return 1


if __name__ == "__main__":
    exit(main())