"""
Simple Error Reporter for Agent3_Part1.py

This module provides a straightforward approach to report errors to the LLM/Agent Mode
without implementing complex error detection and recovery mechanisms.

Usage:
    from simple_error_reporter import error_decorator, report_error

    # Use as a decorator for functions
    @error_decorator
    def my_function():
        # your code here
        
    # Or report errors manually
    try:
        # your code here
    except Exception as e:
        report_error(e)
"""
import traceback
import sys
import os
import json
import functools
import logging
from pathlib import Path
from typing import Callable, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
ERROR_FILE = "agent_error.json"
ERROR_DIR = "agent_errors"
os.makedirs(ERROR_DIR, exist_ok=True)

def report_error(error: Exception, context: str = None) -> None:
    """
    Report an error to be handled by the LLM/Agent Mode.
    
    This function:
    1. Captures the error details
    2. Saves them to a file for the LLM/Agent Mode to read
    3. Logs the error for human inspection if needed
    
    Args:
        error: The exception that was raised
        context: Optional additional context about what was happening
    """
    # Capture error details
    error_type = type(error).__name__
    error_message = str(error)
    tb_string = traceback.format_exc()
    
    # Get the file and line number where the error occurred
    frame_info = None
    tb = traceback.extract_tb(sys.exc_info()[2])
    if tb:
        frame_info = tb[-1]  # Get the last frame (where the error occurred)
    
    # Create error report
    error_report = {
        "error_type": error_type,
        "error_message": error_message,
        "traceback": tb_string,
        "context": context or "No additional context provided"
    }
    
    if frame_info:
        error_report["file"] = frame_info.filename
        error_report["line"] = frame_info.lineno
        error_report["function"] = frame_info.name
        error_report["code_line"] = frame_info.line
    
    # Save to file for LLM/Agent Mode
    error_path = os.path.join(ERROR_DIR, ERROR_FILE)
    try:
        with open(error_path, 'w') as f:
            json.dump(error_report, f, indent=2)
        logging.info(f"Error report saved to {error_path}")
    except Exception as e:
        logging.error(f"Failed to write error report: {e}")
    
    # Log error for human inspection
    logging.error(f"ERROR: {error_type}: {error_message}")
    logging.error(f"File: {error_report.get('file')}, Line: {error_report.get('line')}")
    logging.error(f"Context: {context or 'No additional context'}")
    
    # Print to stderr for immediate visibility
    print(f"ERROR: {error_type}: {error_message}", file=sys.stderr)
    print(f"File: {error_report.get('file')}, Line: {error_report.get('line')}", file=sys.stderr)
    print(f"Full details saved to {error_path}", file=sys.stderr)

def error_decorator(func: Callable) -> Callable:
    """
    Decorator that catches exceptions and reports them to the LLM/Agent Mode.
    
    Args:
        func: The function to wrap with error reporting
        
    Returns:
        Wrapped function that reports errors
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = f"Error in function '{func.__name__}' with args: {args}, kwargs: {kwargs}"
            report_error(e, context)
            raise  # Re-raise the exception for proper flow control
    return wrapper

def check_for_errors() -> Optional[dict]:
    """
    Check if there are any reported errors waiting to be addressed
    
    Returns:
        The error report if one exists, or None if there are no errors
    """
    error_path = os.path.join(ERROR_DIR, ERROR_FILE)
    if os.path.exists(error_path):
        try:
            with open(error_path, 'r') as f:
                error_report = json.load(f)
            return error_report
        except Exception as e:
            logging.error(f"Failed to read error report: {e}")
    return None

def clear_error_report():
    """Remove the error report file after it has been processed"""
    error_path = os.path.join(ERROR_DIR, ERROR_FILE)
    if os.path.exists(error_path):
        try:
            os.remove(error_path)
            logging.info("Error report cleared")
        except Exception as e:
            logging.error(f"Failed to clear error report: {e}")

def get_error_context(error_report: dict, lines_of_context: int = 10) -> str:
    """
    Get the surrounding code context for an error
    
    Args:
        error_report: The error report dictionary
        lines_of_context: How many lines before and after the error to include
        
    Returns:
        A string containing the code context
    """
    if not error_report or "file" not in error_report or "line" not in error_report:
        return "No context available"
        
    file_path = error_report["file"]
    line_number = error_report["line"]
    
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
    
    try:
        with open(file_path, 'r') as f:
            all_lines = f.readlines()
        
        start_line = max(0, line_number - lines_of_context - 1)  # -1 because line numbers are 1-indexed
        end_line = min(len(all_lines), line_number + lines_of_context)
        
        context_lines = all_lines[start_line:end_line]
        
        # Add line numbers to the context
        numbered_context = []
        for i, line in enumerate(context_lines):
            line_num = start_line + i + 1
            prefix = "→ " if line_num == line_number else "  "
            numbered_context.append(f"{prefix}{line_num}: {line.rstrip()}")
        
        return "\n".join(numbered_context)
    except Exception as e:
        return f"Failed to get context: {e}"

# Example usage in a main block
if __name__ == "__main__":
    # Example of using the decorator
    @error_decorator
    def divide(a, b):
        return a / b
    
    # Example of manual error reporting
    try:
        result = divide(10, 0)
    except Exception:
        # The error is already reported by the decorator
        pass
    
    # Check if there are any errors and get the context
    error = check_for_errors()
    if error:
        context = get_error_context(error)
        print("Error detected:")
        print(f"Type: {error['error_type']}")
        print(f"Message: {error['error_message']}")
        print("Context:")
        print(context)
        clear_error_report()
