"""
Sentiment Analyzer

Analyzes email sentiment and tone to detect aggressive or negative emails.
"""

import re
from typing import Dict, List


class SentimentAnalyzer:
    """
    Analyze email sentiment and tone.
    
    Sentiment classes:
    - positive: Friendly, appreciative, enthusiastic
    - neutral: Professional, matter-of-fact
    - negative: Disappointed, frustrated, concerned
    - aggressive: Hostile, demanding, threatening
    """
    
    def __init__(self):
        # Sentiment keywords
        self.positive_keywords = [
            "thank", "thanks", "appreciate", "grateful", "great",
            "excellent", "wonderful", "happy", "pleased", "love",
            "perfect", "amazing", "fantastic", "good"
        ]
        
        self.negative_keywords = [
            "unfortunately", "problem", "issue", "concern", "disappointed",
            "frustrated", "unhappy", "dissatisfied", "bad", "poor",
            "wrong", "mistake", "error", "fail"
        ]
        
        self.aggressive_keywords = [
            "demand", "immediately", "unacceptable", "terrible", "worst",
            "hate", "angry", "furious", "ridiculous", "incompetent",
            "pathetic", "disgrace", "lawsuit", "lawyer", "sue"
        ]
        
        # Tone indicators
        self.formal_indicators = [
            "dear", "sincerely", "regards", "respectfully",
            "kindly", "please", "would you", "could you"
        ]
        
        self.informal_indicators = [
            "hey", "hi", "thanks", "cheers", "cool",
            "yeah", "yep", "nope", "gonna", "wanna"
        ]
    
    def analyze(self, email: Dict[str, str]) -> Dict[str, any]:
        """
        Analyze email sentiment and tone.
        
        Args:
            email: Preprocessed email dictionary
            
        Returns:
            Sentiment analysis result
        """
        text = (email.get("subject", "") + " " + email.get("body", "")).lower()
        
        # Check for aggressive tone (highest priority - safety)
        aggressive_matches = [kw for kw in self.aggressive_keywords if kw in text]
        if aggressive_matches:
            return {
                "sentiment": "negative",
                "tone": "aggressive",
                "confidence": 0.90,
                "reasoning": f"Contains aggressive language: {', '.join(aggressive_matches)}",
                "matched_keywords": aggressive_matches,
                "escalate": True  # Always escalate aggressive emails
            }
        
        # Check for excessive capitalization (shouting)
        caps_ratio = sum(1 for c in email.get("body", "") if c.isupper()) / max(len(email.get("body", "")), 1)
        if caps_ratio > 0.3:
            return {
                "sentiment": "negative",
                "tone": "aggressive",
                "confidence": 0.85,
                "reasoning": "Excessive capitalization detected (shouting)",
                "matched_keywords": [],
                "escalate": True
            }
        
        # Check for excessive exclamation marks
        exclamation_count = text.count('!')
        if exclamation_count > 3:
            return {
                "sentiment": "negative",
                "tone": "aggressive",
                "confidence": 0.75,
                "reasoning": f"Excessive exclamation marks ({exclamation_count})",
                "matched_keywords": [],
                "escalate": True
            }
        
        # Count sentiment keywords
        positive_count = sum(1 for kw in self.positive_keywords if kw in text)
        negative_count = sum(1 for kw in self.negative_keywords if kw in text)
        
        # Determine sentiment
        if positive_count > negative_count and positive_count > 0:
            return {
                "sentiment": "positive",
                "tone": self._detect_tone(text),
                "confidence": min(0.70 + (positive_count * 0.05), 0.95),
                "reasoning": f"Contains {positive_count} positive keywords",
                "matched_keywords": [kw for kw in self.positive_keywords if kw in text],
                "escalate": False
            }
        elif negative_count > positive_count and negative_count > 0:
            return {
                "sentiment": "negative",
                "tone": self._detect_tone(text),
                "confidence": min(0.70 + (negative_count * 0.05), 0.90),
                "reasoning": f"Contains {negative_count} negative keywords",
                "matched_keywords": [kw for kw in self.negative_keywords if kw in text],
                "escalate": False
            }
        else:
            return {
                "sentiment": "neutral",
                "tone": self._detect_tone(text),
                "confidence": 0.75,
                "reasoning": "Balanced or no strong sentiment indicators",
                "matched_keywords": [],
                "escalate": False
            }
    
    def _detect_tone(self, text: str) -> str:
        """
        Detect formality of tone.
        
        Args:
            text: Email text (lowercase)
            
        Returns:
            Tone: "formal", "informal", or "neutral"
        """
        formal_count = sum(1 for indicator in self.formal_indicators if indicator in text)
        informal_count = sum(1 for indicator in self.informal_indicators if indicator in text)
        
        if formal_count > informal_count:
            return "formal"
        elif informal_count > formal_count:
            return "informal"
        else:
            return "neutral"


# Example usage
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    
    test_emails = [
        {
            "subject": "Thank you!",
            "body": "Thank you so much for your help. I really appreciate it!"
        },
        {
            "subject": "Issue with order",
            "body": "Unfortunately, there's a problem with my order. Can you help?"
        },
        {
            "subject": "UNACCEPTABLE SERVICE",
            "body": "This is COMPLETELY UNACCEPTABLE! I demand a refund immediately!"
        },
        {
            "subject": "Meeting tomorrow",
            "body": "Just confirming our meeting tomorrow at 2 PM."
        }
    ]
    
    for email in test_emails:
        result = analyzer.analyze(email)
        print(f"\nEmail: {email['subject']}")
        print(f"Sentiment: {result['sentiment']}, Tone: {result['tone']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Escalate: {result['escalate']}")
        print(f"Reasoning: {result['reasoning']}")
