"""
Response Validator Module

Validates generated drafts against confidence thresholds, safety rules, and quality metrics.
"""

import logging
from typing import Dict, Any, List
from src.config_loader import config

logger = logging.getLogger(__name__)

class Validator:
    """Validates generated responses."""
    
    def __init__(self):
        # Load thresholds from config
        self.thresholds = config.thresholds["confidence"]
        
    def validate(
        self,
        draft: Dict[str, Any],
        intent: str,
        urgency: str,
        sentiment: str
    ) -> Dict[str, Any]:
        """
        Validate the generated draft.
        
        Args:
            draft: Generation result dictionary
            intent: Classified intent
            urgency: Urgency level
            sentiment: Sentiment label
            
        Returns:
            Validation result with status and issues list
        """
        issues = []
        is_valid = True
        
        # 1. Check Generation Confidence
        gen_confidence = draft.get("confidence", 0.0)
        required_confidence = self.thresholds.get(intent, self.thresholds["default"])
        
        if gen_confidence < required_confidence:
            issues.append(f"Low generation confidence: {gen_confidence:.2f} < {required_confidence}")
            is_valid = False
            
        # 2. Check Input Confidence (from classification)
        # Note: In a real flow, we'd pass classification confidence too.
        # Assuming draft generation implies we already passed classification checks,
        # but we can re-verify if needed.
        
        # 3. Check Length
        word_count = draft.get("word_count", 0)
        if word_count < 5:
            issues.append("Draft too short (< 5 words)")
            is_valid = False
        elif word_count > 500:
            issues.append("Draft too long (> 500 words)")
            is_valid = False
            
        # 4. Check Safety (if not already filtered)
        # Assuming SafetyFilter runs before or we run it here.
        # Let's assume pipeline runs SafetyFilter separately, but we check specific flags.
        if draft.get("escalate", False):
            issues.append("Draft marked for escalation by generator")
            is_valid = False
            
        return {
            "valid": is_valid,
            "issues": issues,
            "components": {
                "confidence_check": gen_confidence >= required_confidence,
                "length_check": 5 <= word_count <= 500
            }
        }

# Example usage
if __name__ == "__main__":
    validator = Validator()
    print("Validator initialized.")
