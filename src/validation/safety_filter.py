"""
Safety Filter Module

Detects PII, profanity, and inappropriate content in generated drafts.
"""

import re
import logging
from typing import Dict, Any, List

try:
    from better_profanity import profanity
    HAS_PROFANITY = True
except ImportError:
    HAS_PROFANITY = False

logger = logging.getLogger(__name__)

class SafetyFilter:
    """Filters unsafe content."""
    
    def __init__(self):
        if HAS_PROFANITY:
            profanity.load_censor_words()
            
        self.pii_patterns = {
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b(?:\d[ -]*?){13,16}\b',
            # Simple phone regex, can be improved
            "phone": r'\b\+?1?\d{3}[-.]?\d{3}[-.]?\d{4}\b', 
        }

    def check(self, text: str) -> Dict[str, Any]:
        """
        Check text for safety issues.
        
        Args:
            text: Text to check
            
        Returns:
            Safety check result
        """
        issues = []
        is_safe = True
        
        # 1. Profanity Check
        if HAS_PROFANITY and profanity.contains_profanity(text):
            issues.append("Profanity detected")
            is_safe = False
            
        # 2. PII Check
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, text):
                issues.append(f"Possible PII detected: {pii_type}")
                # We might not want to block automatically for phone numbers in signatures,
                # but for now let's flag it.
                # In production, whitelist user's own phone number.
                pass
        
        return {
            "safe": is_safe,
            "issues": issues
        }

# Example usage
if __name__ == "__main__":
    safety = SafetyFilter()
    print("Safety Filter initialized.")
