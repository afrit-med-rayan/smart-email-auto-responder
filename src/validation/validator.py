"""
Response Validator

Validates generated email responses for quality, safety, and appropriateness.
"""

import re
from typing import Dict, List, Optional


class ResponseValidator:
    """
    Validate generated email responses.
    
    Checks:
    - Confidence thresholds
    - Grammar and spelling
    - Safety (no inappropriate content)
    - Length constraints
    - Tone consistency
    """
    
    def __init__(self):
        # Confidence thresholds by intent
        self.confidence_thresholds = {
            "academic": 0.80,
            "internship": 0.75,
            "meeting": 0.70,
            "support": 0.75,
            "complaint": 0.85,  # Higher threshold for sensitive emails
            "spam": 0.90,
            "general": 0.70,
        }
        
        # Inappropriate words/phrases
        self.inappropriate_words = [
            "damn", "hell", "crap", "stupid", "idiot",
            # Add more as needed
        ]
        
        # Required elements
        self.min_word_count = 10
        self.max_word_count = 500
    
    def validate(
        self,
        draft: str,
        email: Dict[str, str],
        intent: str,
        urgency: str,
        sentiment: str,
        generation_confidence: float,
        classification_confidence: float
    ) -> Dict[str, any]:
        """
        Validate generated response.
        
        Args:
            draft: Generated draft text
            email: Original email
            intent: Classified intent
            urgency: Urgency level
            sentiment: Sentiment
            generation_confidence: Confidence from generator
            classification_confidence: Confidence from classifier
            
        Returns:
            Validation result with pass/fail and issues
        """
        issues = []
        warnings = []
        
        # Check confidence threshold
        min_confidence = min(generation_confidence, classification_confidence)
        threshold = self.confidence_thresholds.get(intent, 0.75)
        
        if min_confidence < threshold:
            issues.append({
                "type": "low_confidence",
                "severity": "high",
                "message": f"Confidence {min_confidence:.2f} below threshold {threshold:.2f}",
                "recommendation": "Escalate to human review"
            })
        
        # Check length
        word_count = len(draft.split())
        if word_count < self.min_word_count:
            issues.append({
                "type": "too_short",
                "severity": "medium",
                "message": f"Draft too short ({word_count} words, minimum {self.min_word_count})",
                "recommendation": "Regenerate with more detail"
            })
        elif word_count > self.max_word_count:
            warnings.append({
                "type": "too_long",
                "severity": "low",
                "message": f"Draft may be too long ({word_count} words, maximum {self.max_word_count})",
                "recommendation": "Consider shortening"
            })
        
        # Check for inappropriate content
        inappropriate_found = [word for word in self.inappropriate_words if word in draft.lower()]
        if inappropriate_found:
            issues.append({
                "type": "inappropriate_content",
                "severity": "critical",
                "message": f"Contains inappropriate words: {', '.join(inappropriate_found)}",
                "recommendation": "Regenerate or escalate"
            })
        
        # Check for greeting
        if not self._has_greeting(draft):
            warnings.append({
                "type": "missing_greeting",
                "severity": "low",
                "message": "Draft may be missing a greeting",
                "recommendation": "Add greeting (Hello, Dear, etc.)"
            })
        
        # Check for signature
        if not self._has_signature(draft):
            warnings.append({
                "type": "missing_signature",
                "severity": "low",
                "message": "Draft may be missing a signature",
                "recommendation": "Add signature (Best regards, etc.)"
            })
        
        # Check tone consistency
        if sentiment == "aggressive":
            issues.append({
                "type": "aggressive_sender",
                "severity": "critical",
                "message": "Original email has aggressive tone",
                "recommendation": "Escalate to human - requires careful handling"
            })
        
        # Grammar check (placeholder - would use LanguageTool API)
        grammar_issues = self._check_grammar(draft)
        if grammar_issues:
            warnings.extend(grammar_issues)
        
        # Determine overall validation result
        passed = len([i for i in issues if i["severity"] in ["critical", "high"]]) == 0
        
        return {
            "passed": passed,
            "confidence": min_confidence,
            "issues": issues,
            "warnings": warnings,
            "word_count": word_count,
            "has_greeting": self._has_greeting(draft),
            "has_signature": self._has_signature(draft),
            "recommendation": "approve" if passed else "escalate"
        }
    
    def _has_greeting(self, text: str) -> bool:
        """Check if text has a greeting."""
        greetings = [
            r'^(dear|hello|hi|hey|greetings)',
            r'^\w+,',  # Name followed by comma
        ]
        
        first_line = text.split('\n')[0].lower().strip()
        return any(re.match(pattern, first_line, re.IGNORECASE) for pattern in greetings)
    
    def _has_signature(self, text: str) -> bool:
        """Check if text has a signature."""
        signatures = [
            r'(best regards|sincerely|thanks|cheers|regards|best)',
            r'^\w+\s*$',  # Just a name on last line
        ]
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if len(lines) < 2:
            return False
        
        last_lines = '\n'.join(lines[-3:]).lower()
        return any(re.search(pattern, last_lines, re.IGNORECASE) for pattern in signatures)
    
    def _check_grammar(self, text: str) -> List[Dict[str, str]]:
        """
        Check grammar and spelling (placeholder).
        
        In production, this would call LanguageTool API or similar.
        
        Args:
            text: Text to check
            
        Returns:
            List of grammar issues
        """
        issues = []
        
        # Simple checks (placeholder for real grammar checker)
        
        # Check for double spaces
        if '  ' in text:
            issues.append({
                "type": "double_space",
                "severity": "low",
                "message": "Contains double spaces",
                "recommendation": "Remove extra spaces"
            })
        
        # Check for missing punctuation at end
        if text and text[-1] not in '.!?':
            issues.append({
                "type": "missing_punctuation",
                "severity": "low",
                "message": "Missing punctuation at end",
                "recommendation": "Add period"
            })
        
        return issues
    
    def auto_fix(self, draft: str) -> str:
        """
        Automatically fix common issues.
        
        Args:
            draft: Draft text
            
        Returns:
            Fixed draft
        """
        # Remove double spaces
        draft = re.sub(r' {2,}', ' ', draft)
        
        # Remove excessive newlines
        draft = re.sub(r'\n{3,}', '\n\n', draft)
        
        # Ensure ends with punctuation
        if draft and draft[-1] not in '.!?':
            draft += '.'
        
        # Trim whitespace
        draft = draft.strip()
        
        return draft


# Example usage
if __name__ == "__main__":
    validator = ResponseValidator()
    
    test_draft = """Hello Professor Smith,

Thank you for your email regarding the assignment deadline. I have received your message and will respond with the requested information shortly.

Best regards,
Rayan"""
    
    test_email = {
        "sender": "professor@university.edu",
        "subject": "Assignment Question",
        "body": "Can I get an extension?"
    }
    
    result = validator.validate(
        draft=test_draft,
        email=test_email,
        intent="academic",
        urgency="medium",
        sentiment="neutral",
        generation_confidence=0.85,
        classification_confidence=0.82
    )
    
    print(f"Validation Passed: {result['passed']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Issues: {len(result['issues'])}")
    print(f"Warnings: {len(result['warnings'])}")
    print(f"Recommendation: {result['recommendation']}")
