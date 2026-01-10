"""
Enhanced Urgency Detector

Detects email urgency using temporal analysis and keyword detection.
"""

import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class UrgencyDetector:
    """
    Detect email urgency level.
    
    Urgency levels:
    - critical: Immediate action required (within hours)
    - high: Action required within 1-2 days
    - medium: Action required within a week
    - low: No specific deadline or long-term
    """
    
    def __init__(self):
        # Urgency keywords by level
        self.critical_keywords = [
            "urgent", "asap", "immediately", "emergency", "critical",
            "right now", "today", "within hours"
        ]
        
        self.high_keywords = [
            "soon", "quickly", "tomorrow", "by tomorrow", "this week",
            "deadline", "due", "time-sensitive"
        ]
        
        self.medium_keywords = [
            "next week", "upcoming", "soon", "when you can",
            "at your convenience"
        ]
        
        # Temporal patterns
        self.deadline_patterns = [
            r'deadline\s+(?:is\s+)?(?:on\s+)?(\w+\s+\d+)',
            r'due\s+(?:on\s+)?(\w+\s+\d+)',
            r'by\s+(\w+\s+\d+)',
            r'before\s+(\w+\s+\d+)',
            r'(?:today|tomorrow|tonight)',
        ]
    
    def detect(self, email: Dict[str, str]) -> Dict[str, any]:
        """
        Detect urgency level.
        
        Args:
            email: Preprocessed email dictionary
            
        Returns:
            Urgency result with level and confidence
        """
        text = (email.get("subject", "") + " " + email.get("body", "")).lower()
        
        # Check for critical urgency
        critical_matches = [kw for kw in self.critical_keywords if kw in text]
        if critical_matches:
            return {
                "urgency": "critical",
                "confidence": 0.95,
                "reasoning": f"Contains critical keywords: {', '.join(critical_matches)}",
                "matched_keywords": critical_matches
            }
        
        # Check for deadline mentions
        deadline_info = self._extract_deadline(text)
        if deadline_info:
            days_until = deadline_info.get("days_until", 999)
            
            if days_until <= 1:
                return {
                    "urgency": "critical",
                    "confidence": 0.90,
                    "reasoning": f"Deadline within {days_until} day(s)",
                    "deadline": deadline_info.get("deadline_text")
                }
            elif days_until <= 3:
                return {
                    "urgency": "high",
                    "confidence": 0.85,
                    "reasoning": f"Deadline in {days_until} days",
                    "deadline": deadline_info.get("deadline_text")
                }
            elif days_until <= 7:
                return {
                    "urgency": "medium",
                    "confidence": 0.75,
                    "reasoning": f"Deadline in {days_until} days",
                    "deadline": deadline_info.get("deadline_text")
                }
        
        # Check for high urgency keywords
        high_matches = [kw for kw in self.high_keywords if kw in text]
        if high_matches:
            return {
                "urgency": "high",
                "confidence": 0.80,
                "reasoning": f"Contains high-urgency keywords: {', '.join(high_matches)}",
                "matched_keywords": high_matches
            }
        
        # Check for medium urgency keywords
        medium_matches = [kw for kw in self.medium_keywords if kw in text]
        if medium_matches:
            return {
                "urgency": "medium",
                "confidence": 0.70,
                "reasoning": f"Contains medium-urgency keywords: {', '.join(medium_matches)}",
                "matched_keywords": medium_matches
            }
        
        # Default: low urgency
        return {
            "urgency": "low",
            "confidence": 0.65,
            "reasoning": "No urgency indicators found",
            "matched_keywords": []
        }
    
    def _extract_deadline(self, text: str) -> Optional[Dict[str, any]]:
        """
        Extract deadline information from text.
        
        Args:
            text: Email text
            
        Returns:
            Deadline info or None
        """
        for pattern in self.deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                deadline_text = match.group(0)
                
                # Try to parse relative dates
                if "today" in deadline_text.lower():
                    return {
                        "deadline_text": deadline_text,
                        "days_until": 0
                    }
                elif "tomorrow" in deadline_text.lower():
                    return {
                        "deadline_text": deadline_text,
                        "days_until": 1
                    }
                elif "tonight" in deadline_text.lower():
                    return {
                        "deadline_text": deadline_text,
                        "days_until": 0
                    }
                
                # Try to parse specific dates (simplified)
                # In production, use dateutil.parser for robust parsing
                try:
                    if match.groups():
                        date_str = match.group(1)
                        # Simplified: assume dates are within next 30 days
                        # Real implementation would parse actual dates
                        return {
                            "deadline_text": deadline_text,
                            "days_until": 7  # Placeholder
                        }
                except:
                    pass
                
                return {
                    "deadline_text": deadline_text,
                    "days_until": 7  # Default assumption
                }
        
        return None


# Example usage
if __name__ == "__main__":
    detector = UrgencyDetector()
    
    test_emails = [
        {
            "subject": "URGENT: Server Down",
            "body": "The production server is down. Need immediate attention!"
        },
        {
            "subject": "Assignment Due Tomorrow",
            "body": "Just a reminder that the assignment is due by tomorrow."
        },
        {
            "subject": "Meeting Next Week",
            "body": "Let's schedule a meeting for next week when you're available."
        },
        {
            "subject": "Newsletter",
            "body": "Here's our monthly newsletter with updates."
        }
    ]
    
    for email in test_emails:
        result = detector.detect(email)
        print(f"\nEmail: {email['subject']}")
        print(f"Urgency: {result['urgency']} (confidence: {result['confidence']:.2f})")
        print(f"Reasoning: {result['reasoning']}")
