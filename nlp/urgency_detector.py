"""
Enhanced Urgency Detector

Detects email urgency using temporal analysis and keyword detection.
Uses dateutil for robust date parsing.
"""

import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from src.config_loader import config

try:
    from dateutil import parser as date_parser
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False

logger = logging.getLogger(__name__)

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
            r'\b(urgent|asap|immediately|emergency|critical|right now|within hours)\b'
        ]
        
        self.high_keywords = [
            r'\b(soon|quickly|tomorrow|by tomorrow|this week|deadline|due|time-sensitive|priority)\b'
        ]
        
        self.medium_keywords = [
            r'\b(next week|upcoming|soon|when you can|at your convenience)\b'
        ]
        
        # VIP Senders (mock - real would come from user config)
        self.vip_senders = ["boss@company.com", "ceo@company.com"]

    def detect(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect urgency level.
        
        Args:
            email: Preprocessed email dictionary
            
        Returns:
            Urgency result with level and confidence
        """
        text = email.get("combined_text", "").lower()
        sender = email.get("sender", "").lower()
        
        # 1. Check VIP
        if any(vip in sender for vip in self.vip_senders):
            return {
                "urgency": "high",
                "confidence": 0.9,
                "reasoning": "VIP sender detected"
            }
            
        # 2. Check for Clean Deadline
        deadline_info = self._extract_deadline(text)
        if deadline_info:
            days_until = deadline_info.get("days_until", 999)
            
            if days_until <= 0: # Today/Overdue
                return {
                    "urgency": "critical",
                    "confidence": 0.95,
                    "reasoning": f"Deadline is today/overdue: {deadline_info.get('deadline_text')}",
                    "deadline": deadline_info
                }
            elif days_until <= 2:
                return {
                    "urgency": "high",
                    "confidence": 0.85,
                    "reasoning": f"Deadline in {days_until} days",
                    "deadline": deadline_info
                }
            elif days_until <= 7:
                return {
                    "urgency": "medium",
                    "confidence": 0.75,
                    "reasoning": f"Deadline in {days_until} days",
                    "deadline": deadline_info
                }
        
        # 3. Check Keywords
        # Critical
        if self._check_keywords(text, self.critical_keywords):
            return {"urgency": "critical", "confidence": 0.85, "reasoning": "Critical keywords found"}
            
        # High
        if self._check_keywords(text, self.high_keywords):
            return {"urgency": "high", "confidence": 0.75, "reasoning": "High urgency keywords found"}
            
        # Medium
        if self._check_keywords(text, self.medium_keywords):
            return {"urgency": "medium", "confidence": 0.65, "reasoning": "Medium urgency keywords found"}
        
        # Default
        return {"urgency": "low", "confidence": 0.60, "reasoning": "No urgency indicators"}

    def _check_keywords(self, text: str, patterns: List[str]) -> bool:
        """Check if any compiled regex pattern matches."""
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False

    def _extract_deadline(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract deadline information from text.
        Returns closest future date found near keyword 'deadline'/'due'.
        """
        # Look for context window around "due" or "deadline"
        # Simple extraction logic
        
        matches = re.finditer(r'\b(due|deadline|by|until)\b.{0,30}', text)
        
        today = datetime.now()
        closest_date = None
        min_diff = 999
        matched_text = ""
        
        for match in matches:
            snippet = match.group(0)
            # Try parsing date from snippet
            try:
                # dateutil parser fuzzy=True matches dates in string
                if HAS_DATEUTIL:
                    dt = date_parser.parse(snippet, fuzzy=True, default=today)
                else:
                    # Very simple fallback: only detect known keywords for relative dates
                    dt = today
                    snippet_lower = snippet.lower()
                    if "tomorrow" in snippet_lower:
                        dt = today + timedelta(days=1)
                    elif "next week" in snippet_lower:
                        dt = today + timedelta(days=7)
                    else:
                        continue # Cannot parse strict dates without dateutil
                
                # Filter out past dates if just 'timestamp', but keep if explicitly date
                # Simple check: ignore if it's just 'today's time'
                if dt.date() == today.date() and dt.year == today.year:
                     # Check if it actually parsed a date or just defaulted
                     # If snippet doesn't contain date info, fuzzy might return default
                     pass 
                
                diff = (dt - today).days
                if -1 <= diff < min_diff:  # Allow -1 for "yesterday" context or slight offsets
                    # Only consider it if it looks like a future/near date
                    min_diff = diff
                    closest_date = dt
                    matched_text = snippet
            except:
                continue
                
        if closest_date:
            return {
                "deadline_text": matched_text,
                "date": closest_date,
                "days_until": max(0, min_diff)
            }
            
        return None

# Example usage
if __name__ == "__main__":
    detector = UrgencyDetector()
    print("Urgency Detector initialized.")
