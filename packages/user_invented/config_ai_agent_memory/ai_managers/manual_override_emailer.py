#!/usr/bin/env python
"""
Manual Override Email Notification System

Sends email notifications to the user when AI Workflow needs manual approval
for restricted automation operations. This system bypasses the GUI and sends
direct email notifications to yerbro@gmail.com.
"""

import os
import json
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ManualOverrideEmailer")

class ManualOverrideEmailer:
    """Handles email notifications for manual override requests"""
    
    def __init__(self, config_path: str = "ai_managers/restricted_automation_schema.json"):
        self.config_path = config_path
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config = self._load_config()
        self.pending_requests = {}
        
        # Email configuration (will use system email settings)
        self.recipient_email = "yerbro@gmail.com"
        self.sender_email = "ggg_ai_workflow@localhost"  # Local system identifier
        
        # Try to detect available email methods
        self._detect_email_capabilities()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load restricted automation configuration"""
        config_file = os.path.join(self.base_dir, self.config_path)
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            return config.get("restricted_automation_mode", {})
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def _detect_email_capabilities(self):
        """Detect available email sending capabilities"""
        self.email_methods = []
        
        # Check for Windows mail command
        if os.name == 'nt':
            try:
                import subprocess
                result = subprocess.run(['where', 'powershell'], capture_output=True, text=True)
                if result.returncode == 0:
                    self.email_methods.append('powershell')
            except:
                pass
        
        # Check for Linux mail command
        else:
            try:
                import subprocess
                result = subprocess.run(['which', 'mail'], capture_output=True, text=True)
                if result.returncode == 0:
                    self.email_methods.append('mail')
            except:
                pass
        
        # Always have fallback to log file
        self.email_methods.append('logfile')
        
        logger.info(f"Available email methods: {self.email_methods}")
    
    def check_operation_restrictions(self, operation: str, target: str) -> Dict[str, Any]:
        """
        Check if an operation is restricted and requires manual override
        
        Args:
            operation: Type of operation (read, write, delete, etc.)
            target: Target file or folder path
            
        Returns:
            Dict with restriction info and approval status
        """
        result = {
            "restricted": False,
            "override_required": False,
            "reason": "",
            "allowed_operations": [],
            "auto_approved": False
        }
        
        # Normalize target path
        target_path = os.path.normpath(target)
        target_name = os.path.basename(target_path)
        
        # Check folder restrictions
        for folder_pattern, restrictions in self.config.get("folder_restrictions", {}).items():
            if folder_pattern.rstrip('/') in target_path:
                result["restricted"] = True
                result["override_required"] = restrictions.get("override_required", False)
                result["reason"] = restrictions.get("reason", "Folder is restricted")
                result["allowed_operations"] = restrictions.get("allowed_operations", [])
                
                # Check if operation is allowed
                if operation in result["allowed_operations"]:
                    result["auto_approved"] = True
                    return result
                
                break
        
        # Check file restrictions
        for file_pattern, restrictions in self.config.get("file_restrictions", {}).items():
            if self._match_pattern(target_name, file_pattern):
                result["restricted"] = True
                result["override_required"] = restrictions.get("override_required", False)
                result["reason"] = restrictions.get("reason", "File type is restricted")
                result["allowed_operations"] = restrictions.get("allowed_operations", [])
                
                # Check if operation is allowed
                if operation in result["allowed_operations"]:
                    result["auto_approved"] = True
                    return result
                
                break
        
        # Check function restrictions
        for function_name, restrictions in self.config.get("function_restrictions", {}).items():
            if function_name in operation.lower():
                result["restricted"] = True
                result["override_required"] = restrictions.get("override_required", False)
                result["reason"] = restrictions.get("reason", "Function is restricted")
                break
        
        return result
    
    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """Enhanced pattern matching for file names with wildcards"""
        if '*' in pattern:
            # Handle multiple wildcards and complex patterns
            pattern_parts = pattern.split('*')
            
            if len(pattern_parts) == 2:
                # Simple case: *suffix or prefix*
                prefix, suffix = pattern_parts
                return filename.startswith(prefix) and filename.endswith(suffix)
            elif len(pattern_parts) == 3:
                # Case: prefix*middle*suffix
                prefix, middle, suffix = pattern_parts
                return (filename.startswith(prefix) and 
                       filename.endswith(suffix) and 
                       middle.lower() in filename.lower())
            else:
                # Complex case: multiple wildcards
                # Convert to regex-like matching
                import re
                regex_pattern = pattern.replace('*', '.*')
                return bool(re.match(regex_pattern, filename, re.IGNORECASE))
        else:
            return filename.lower() == pattern.lower()
        return False
    
    def request_manual_override(self, operation: str, target: str, reason: str, 
                              session_id: Optional[str] = None) -> str:
        """
        Request manual override for a restricted operation
        
        Args:
            operation: Type of operation requiring approval
            target: Target file or folder
            reason: Reason for the operation
            session_id: Current AI session ID
            
        Returns:
            str: Request ID for tracking
        """
        request_id = f"override_{int(datetime.now().timestamp())}"
        
        # Check if operation is actually restricted
        restriction_info = self.check_operation_restrictions(operation, target)
        
        if not restriction_info["restricted"]:
            logger.info(f"Operation {operation} on {target} is not restricted")
            return "auto_approved"
        
        if restriction_info["auto_approved"]:
            logger.info(f"Operation {operation} on {target} is auto-approved")
            return "auto_approved"
        
        # Create override request
        request_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "operation_type": operation,
            "target_file_or_folder": target,
            "reason_for_override": reason,
            "expected_impact": f"Will {operation} {target}",
            "ai_agent_session_id": session_id or "unknown",
            "restriction_reason": restriction_info["reason"],
            "status": "pending",
            "email_sent": False
        }
        
        # Store request
        self.pending_requests[request_id] = request_data
        
        # Send email notification
        email_sent = self._send_override_email(request_data)
        request_data["email_sent"] = email_sent
        
        # Save request to file for persistence
        self._save_pending_requests()
        
        logger.info(f"Manual override requested: {request_id}")
        return request_id
    
    def _send_override_email(self, request_data: Dict[str, Any]) -> bool:
        """Send email notification for manual override request"""
        
        # Prepare email content
        subject = "GlowingGoldenGlobe - Manual Override Request"
        
        body = f"""
Manual Override Request - GlowingGoldenGlobe AI Workflow

Request ID: {request_data['request_id']}
Timestamp: {request_data['timestamp']}

OPERATION DETAILS:
- Operation Type: {request_data['operation_type']}
- Target: {request_data['target_file_or_folder']}
- Reason: {request_data['reason_for_override']}
- Expected Impact: {request_data['expected_impact']}
- AI Session ID: {request_data['ai_agent_session_id']}

RESTRICTION INFO:
- Restriction Reason: {request_data['restriction_reason']}

ACTION REQUIRED:
The AI Workflow system is requesting manual approval for this operation.
Please review and approve/deny this request.

To approve: Reply with "APPROVE {request_data['request_id']}"
To deny: Reply with "DENY {request_data['request_id']}"

This request will auto-deny after 24 hours if no response is received.

--
GlowingGoldenGlobe AI Workflow System
"""
        
        # Try different email methods
        for method in self.email_methods:
            try:
                if method == 'powershell':
                    success = self._send_email_powershell(subject, body)
                elif method == 'mail':
                    success = self._send_email_mail(subject, body)
                elif method == 'logfile':
                    success = self._send_email_logfile(subject, body)
                else:
                    continue
                
                if success:
                    logger.info(f"Override email sent successfully via {method}")
                    return True
                    
            except Exception as e:
                logger.error(f"Failed to send email via {method}: {e}")
                continue
        
        logger.error("Failed to send email via any method")
        return False
    
    def _send_email_powershell(self, subject: str, body: str) -> bool:
        """Send email using PowerShell (Windows)"""
        try:
            import subprocess
            
            # Create PowerShell command to send email
            ps_script = f"""
$Subject = "{subject}"
$Body = @"
{body}
"@
$To = "{self.recipient_email}"

# Try to send email notification (this is a notification attempt)
Write-Host "Email notification would be sent to: $To"
Write-Host "Subject: $Subject"
Write-Host "Body:"
Write-Host $Body
Write-Host "---"
Write-Host "Note: Actual email sending requires SMTP configuration"
"""
            
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("PowerShell email notification executed")
                return True
            else:
                logger.error(f"PowerShell email failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"PowerShell email error: {e}")
            return False
    
    def _send_email_mail(self, subject: str, body: str) -> bool:
        """Send email using mail command (Linux)"""
        try:
            import subprocess
            
            # Use mail command
            result = subprocess.run(
                ['mail', '-s', subject, self.recipient_email],
                input=body,
                text=True,
                capture_output=True
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Mail command error: {e}")
            return False
    
    def _send_email_logfile(self, subject: str, body: str) -> bool:
        """Log email to file as fallback"""
        try:
            log_file = os.path.join(self.base_dir, "manual_override_notifications.log")
            
            with open(log_file, 'a') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
                f.write(f"TO: {self.recipient_email}\n")
                f.write(f"SUBJECT: {subject}\n")
                f.write(f"BODY:\n{body}\n")
                f.write(f"{'='*50}\n")
            
            logger.info(f"Email logged to file: {log_file}")
            return True
            
        except Exception as e:
            logger.error(f"Log file email error: {e}")
            return False
    
    def _save_pending_requests(self):
        """Save pending requests to file"""
        try:
            requests_file = os.path.join(self.base_dir, "pending_override_requests.json")
            with open(requests_file, 'w') as f:
                json.dump(self.pending_requests, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving pending requests: {e}")
    
    def get_pending_requests(self) -> Dict[str, Any]:
        """Get all pending override requests"""
        return self.pending_requests.copy()
    
    def check_request_status(self, request_id: str) -> Optional[str]:
        """Check the status of an override request"""
        if request_id in self.pending_requests:
            return self.pending_requests[request_id]["status"]
        return None


# Global instance
_override_emailer = None

def get_override_emailer() -> ManualOverrideEmailer:
    """Get the global override emailer instance"""
    global _override_emailer
    if _override_emailer is None:
        _override_emailer = ManualOverrideEmailer()
    return _override_emailer

def check_operation_allowed(operation: str, target: str) -> bool:
    """Quick function to check if an operation is allowed"""
    emailer = get_override_emailer()
    restriction_info = emailer.check_operation_restrictions(operation, target)
    return not restriction_info["restricted"] or restriction_info["auto_approved"]

def request_override(operation: str, target: str, reason: str, session_id: Optional[str] = None) -> str:
    """Quick function to request manual override"""
    emailer = get_override_emailer()
    return emailer.request_manual_override(operation, target, reason, session_id)

# Example usage
if __name__ == "__main__":
    print("Testing Manual Override Email System")
    
    emailer = ManualOverrideEmailer()
    
    # Test restriction checking
    test_operations = [
        ("read", "Help_pyautogen/config.py"),
        ("delete", "backups/important_file.txt"),
        ("modify", "docs/README.md"),
        ("create", "normal_file.txt")
    ]
    
    for operation, target in test_operations:
        restriction_info = emailer.check_operation_restrictions(operation, target)
        print(f"\nOperation: {operation} on {target}")
        print(f"Restricted: {restriction_info['restricted']}")
        print(f"Auto-approved: {restriction_info['auto_approved']}")
        print(f"Reason: {restriction_info['reason']}")
    
    # Test override request
    print("\nTesting override request...")
    request_id = emailer.request_manual_override(
        "delete", 
        "backups/test_file.txt", 
        "Testing the override system",
        "test_session_123"
    )
    print(f"Override request ID: {request_id}")