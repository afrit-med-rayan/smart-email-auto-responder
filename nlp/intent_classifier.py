"""
Enhanced Intent Classifier

ML-based intent classification using BERT/RoBERTa.
Supports both rule-based fallback and model-based classification.
"""

import re
from typing import Dict, List, Optional
import numpy as np


class IntentClassifier:
    """
    Classify email intent using ML model or rule-based fallback.
    
    Intent classes:
    - academic: Emails from professors, TAs, academic departments
    - internship: Job applications, interviews, HR communications
    - meeting: Meeting scheduling, calendar invitations
    - support: Help requests, customer support
    - complaint: Complaints, negative feedback
    - spam: Marketing, newsletters, unsolicited emails
    - general: Everything else
    """
    
    def __init__(self, model_path: Optional[str] = None, use_rules: bool = True):
        """
        Initialize classifier.
        
        Args:
            model_path: Path to trained BERT model (optional)
            use_rules: Whether to use rule-based fallback
        """
        self.model_path = model_path
        self.use_rules = use_rules
        self.model = None
        self.tokenizer = None
        
        # Intent labels
        self.labels = [
            "academic",
            "internship", 
            "meeting",
            "support",
            "complaint",
            "spam",
            "general"
        ]
        
        # Load model if path provided
        if model_path:
            self._load_model(model_path)
    
    def classify(self, email: Dict[str, str]) -> Dict[str, any]:
        """
        Classify email intent.
        
        Args:
            email: Preprocessed email dictionary
            
        Returns:
            Classification result with intent and confidence
        """
        # Try ML model first
        if self.model is not None:
            return self._classify_with_model(email)
        
        # Fallback to rule-based
        if self.use_rules:
            return self._classify_with_rules(email)
        
        # Default
        return {
            "intent": "general",
            "confidence": 0.5,
            "method": "default"
        }
    
    def _classify_with_model(self, email: Dict[str, str]) -> Dict[str, any]:
        """
        Classify using BERT model.
        
        Args:
            email: Preprocessed email
            
        Returns:
            Classification result
        """
        # TODO: Implement when model is trained
        # For now, use rule-based
        return self._classify_with_rules(email)
    
    def _classify_with_rules(self, email: Dict[str, str]) -> Dict[str, any]:
        """
        Rule-based classification (fallback).
        
        Args:
            email: Preprocessed email
            
        Returns:
            Classification result
        """
        text = (email.get("subject", "") + " " + email.get("body", "")).lower()
        sender = email.get("sender", "").lower()
        
        # Spam detection (highest priority)
        spam_keywords = [
            "unsubscribe", "discount", "limited offer", "click here",
            "winner", "prize", "free", "congratulations", "act now"
        ]
        if any(keyword in text for keyword in spam_keywords):
            return {
                "intent": "spam",
                "confidence": 0.95,
                "method": "rule-based",
                "matched_keywords": [kw for kw in spam_keywords if kw in text]
            }
        
        # Academic detection
        academic_keywords = [
            "professor", "assignment", "exam", "grade", "course",
            "class", "homework", "lecture", "syllabus", "office hours"
        ]
        if sender.endswith(".edu") or any(keyword in text for keyword in academic_keywords):
            confidence = 0.85 if sender.endswith(".edu") else 0.75
            return {
                "intent": "academic",
                "confidence": confidence,
                "method": "rule-based",
                "matched_keywords": [kw for kw in academic_keywords if kw in text]
            }
        
        # Internship/Job detection
        job_keywords = [
            "interview", "position", "application", "resume", "cv",
            "hiring", "job", "opportunity", "candidate", "recruiter"
        ]
        if any(keyword in text for keyword in job_keywords) or "hr" in sender:
            return {
                "intent": "internship",
                "confidence": 0.80,
                "method": "rule-based",
                "matched_keywords": [kw for kw in job_keywords if kw in text]
            }
        
        # Meeting detection
        meeting_keywords = [
            "meeting", "schedule", "calendar", "available", "appointment",
            "call", "zoom", "teams", "conference", "sync"
        ]
        if any(keyword in text for keyword in meeting_keywords):
            return {
                "intent": "meeting",
                "confidence": 0.75,
                "method": "rule-based",
                "matched_keywords": [kw for kw in meeting_keywords if kw in text]
            }
        
        # Support detection
        support_keywords = [
            "help", "issue", "problem", "support", "assistance",
            "question", "how to", "not working", "error"
        ]
        if any(keyword in text for keyword in support_keywords):
            return {
                "intent": "support",
                "confidence": 0.70,
                "method": "rule-based",
                "matched_keywords": [kw for kw in support_keywords if kw in text]
            }
        
        # Complaint detection
        complaint_keywords = [
            "disappointed", "unacceptable", "terrible", "worst",
            "complaint", "unsatisfied", "refund", "cancel"
        ]
        if any(keyword in text for keyword in complaint_keywords):
            return {
                "intent": "complaint",
                "confidence": 0.75,
                "method": "rule-based",
                "matched_keywords": [kw for kw in complaint_keywords if kw in text]
            }
        
        # Default: general
        return {
            "intent": "general",
            "confidence": 0.60,
            "method": "rule-based",
            "matched_keywords": []
        }
    
    def _load_model(self, model_path: str):
        """
        Load trained BERT model.
        
        Args:
            model_path: Path to model checkpoint
        """
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model.eval()
            
            print(f"Loaded model from {model_path}")
        except Exception as e:
            print(f"Failed to load model: {e}")
            print("Falling back to rule-based classification")
            self.model = None
            self.tokenizer = None
    
    def batch_classify(self, emails: List[Dict[str, str]]) -> List[Dict[str, any]]:
        """
        Classify multiple emails in batch.
        
        Args:
            emails: List of preprocessed emails
            
        Returns:
            List of classification results
        """
        return [self.classify(email) for email in emails]


# Example usage
if __name__ == "__main__":
    classifier = IntentClassifier(use_rules=True)
    
    # Test emails
    test_emails = [
        {
            "sender": "professor@university.edu",
            "subject": "Assignment Deadline",
            "body": "The assignment is due next week."
        },
        {
            "sender": "hr@company.com",
            "subject": "Interview Invitation",
            "body": "We would like to invite you for an interview."
        },
        {
            "sender": "marketing@shop.com",
            "subject": "50% Discount - Limited Offer!",
            "body": "Click here to claim your discount. Unsubscribe anytime."
        },
        {
            "sender": "colleague@work.com",
            "subject": "Quick sync",
            "body": "Are you available for a meeting tomorrow?"
        }
    ]
    
    for email in test_emails:
        result = classifier.classify(email)
        print(f"\nEmail: {email['subject']}")
        print(f"Intent: {result['intent']} (confidence: {result['confidence']:.2f})")
        print(f"Method: {result['method']}")
