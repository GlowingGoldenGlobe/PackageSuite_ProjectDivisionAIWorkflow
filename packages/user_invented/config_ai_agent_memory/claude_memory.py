#!/usr/bin/env python3
"""
Claude Memory Management System

This module provides functions for Claude to maintain persistent memory
across sessions by updating a markdown file and logging changes.

FILES MANAGED:
- /mnt/c/Users/yerbr/glowinggoldenglobe_venv/CLAUDE.md - Primary memory repository
- /mnt/c/Users/yerbr/glowinggoldenglobe_venv/claude_memory.log - Change log (not read by Claude)

This script is referenced in both CLAUDE.md and MEMORY_GUIDELINES.md for user awareness.
"""

import os
import datetime
import re
from pathlib import Path

# Configuration
CLAUDE_MEMORY_FILE = os.path.join(os.path.dirname(__file__), "CLAUDE.md")
MEMORY_LOG_FILE = os.path.join(os.path.dirname(__file__), "claude_memory.log")

def add_to_memory(content, category="Guidelines and Rules"):
    """
    Add new content to Claude's memory repository
    
    Args:
        content: The content to add (string)
        category: The category under which to file this memory
                 (Guidelines and Rules, User Preferences, Project-Specific Notes, Tool Usage)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Make sure the category is valid
        valid_categories = [
            "Guidelines and Rules", 
            "User Preferences", 
            "Project-Specific Notes",
            "Tool Usage"
        ]
        
        if category not in valid_categories:
            log_memory_action(f"Invalid category: {category}", success=False)
            return False
        
        # Read current memory file
        if os.path.exists(CLAUDE_MEMORY_FILE):
            with open(CLAUDE_MEMORY_FILE, 'r') as f:
                memory_content = f.read()
        else:
            # Create a basic structure if file doesn't exist
            memory_content = """# Claude Memory Repository

This file serves as a persistent memory repository for Claude. Important guidelines, rules, and preferences mentioned by users will be automatically recorded here for future reference.

## Guidelines and Rules

## User Preferences

## Project-Specific Notes

## Tool Usage
"""
        
        # Find the appropriate section
        section_pattern = f"## {re.escape(category)}"
        match = re.search(section_pattern, memory_content)
        
        if not match:
            log_memory_action(f"Category section not found: {category}", success=False)
            return False
        
        # Find next section to determine where to insert
        section_start = match.end()
        next_section = re.search(r"## ", memory_content[section_start:])
        
        if next_section:
            insert_position = section_start + next_section.start()
        else:
            insert_position = len(memory_content)
        
        # Count existing items
        existing_items = re.findall(r"\d+\.\s+", memory_content[section_start:insert_position])
        next_item_number = len(existing_items) + 1
        
        # Format the new content
        formatted_content = f"\n{next_item_number}. **{content}**\n"
        
        # Insert the new content
        new_memory_content = (
            memory_content[:insert_position] + 
            formatted_content + 
            memory_content[insert_position:]
        )
        
        # Write back to file
        with open(CLAUDE_MEMORY_FILE, 'w') as f:
            f.write(new_memory_content)
        
        # Log the action
        log_memory_action(f"Added to '{category}': {content}", success=True)
        
        return True
    
    except Exception as e:
        log_memory_action(f"Error adding to memory: {str(e)}", success=False)
        return False

def log_memory_action(message, success=True):
    """
    Log memory-related actions to a log file
    
    Args:
        message: The message to log
        success: Whether the action was successful
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "SUCCESS" if success else "ERROR"
        log_entry = f"[{timestamp}] [{status}] {message}\n"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(MEMORY_LOG_FILE), exist_ok=True)
        
        # Append to log file
        with open(MEMORY_LOG_FILE, 'a') as f:
            f.write(log_entry)
            
    except Exception as e:
        # Can't log to file, print to stdout
        print(f"Error logging memory action: {str(e)}")

def get_memory_categories():
    """Get the list of available memory categories"""
    return [
        "Guidelines and Rules", 
        "User Preferences", 
        "Project-Specific Notes",
        "Tool Usage"
    ]

def list_memory_entries(category=None):
    """
    List memory entries, optionally filtered by category
    
    Args:
        category: Optional category to filter by
        
    Returns:
        list: List of memory entries
    """
    try:
        if not os.path.exists(CLAUDE_MEMORY_FILE):
            return []
            
        with open(CLAUDE_MEMORY_FILE, 'r') as f:
            content = f.read()
            
        entries = []
        
        # Process each category
        categories = get_memory_categories()
        
        for cat in categories:
            if category and cat != category:
                continue
                
            section_pattern = f"## {re.escape(cat)}"
            match = re.search(section_pattern, content)
            
            if not match:
                continue
                
            section_start = match.end()
            next_section = re.search(r"## ", content[section_start:])
            
            if next_section:
                section_end = section_start + next_section.start()
            else:
                section_end = len(content)
                
            section_content = content[section_start:section_end]
            
            # Extract numbered items
            items = re.findall(r"\d+\.\s+\*\*(.*?)\*\*", section_content)
            for item in items:
                entries.append((cat, item))
                
        return entries
        
    except Exception as e:
        log_memory_action(f"Error listing memory entries: {str(e)}", success=False)
        return []

# Example usage - to be used directly by Claude
if __name__ == "__main__":
    # Example: add_to_memory("Always use lazy loading for expensive operations", "Guidelines and Rules")
    pass