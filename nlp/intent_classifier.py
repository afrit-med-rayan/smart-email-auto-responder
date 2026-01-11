"""
Enhanced Intent Classifier

ML-based intent classification using DistilBERT.
Supports both rule-based fallback and model-based classification.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from src.config_loader import config

try:
    import torch
    import numpy as np
    from torch.nn import functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Optional transformers import
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    from torch.nn import functional as F
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

logger = logging.getLogger(__name__)

class IntentClassifier:
    """
    Classify email intent using ML model or rule-based fallback.
    
    Intent classes:
    - academic: Emails from professors, TAs, academic departments
    - internship: Job applications, interviews, HR communications
    - meeting: Scheduling requests, calendar invites
    - support: Help requests, issues, complaints
    - spam: Promotional, unwanted
    - general: Routine correspondence
    """
    
    def __init__(self, model_path: Optional[str] = None, use_rules: bool = True):
        self.use_rules = use_rules
        self.device = None
        if HAS_TORCH:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.model = None
        self.tokenizer = None
        
        # Load model if configured
        if HAS_TRANSFORMERS and HAS_TORCH and config:
            try:
                model_name = model_path or config.models["intent_classifier"].name
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
                self.model.to(self.device)
                self.model.eval()
                
                # Load label mapping (mock for now, would be in config or model config)
                self.id2label = {
                    0: "academic",
                    1: "internship",
                    2: "meeting",
                    3: "support",
                    4: "spam",
                    5: "general"
                }
            except Exception as e:
                logger.warning(f"Failed to load ML model: {e}")
                self.model = None

        # Rule-based keywords (fallback)
        self.rules = {
            "academic": [r'\b(professor|assignment|exam|grade|course|class|homework|lab|thesis|syllabus)\b'],
            "internship": [r'\b(interview|position|application|resume|cv|hiring|job|recruiter|candidacy)\b'],
            "meeting": [r'\b(meeting|schedule|calendar|available|appointment|sync|zoom|teams)\b'],
            "support": [r'\b(help|issue|problem|error|bug|fail|broken|access|account)\b'],
            "spam": [r'\b(unsubscribe|discount|offer|winner|prize|click here|limited time)\b']
        }

    def classify(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify email intent.
        
        Args:
            email: Preprocessed email dictionary
            
        Returns:
            Classification result with intent and confidence
        """
        # 1. Try ML Model
        if self.model and self.tokenizer:
            ml_result = self._classify_with_model(email)
            # If high confidence, return
            if ml_result["confidence"] > 0.6:
                return ml_result
        
        # 2. Fallback to Rules
        if self.use_rules:
            return self._classify_with_rules(email)
            
        # 3. Default
        return {
            "intent": "general",
            "confidence": 0.5,
            "method": "default",
            "scores": {}
        }

    def _classify_with_model(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """Classify using BERT model."""
        text = email.get("combined_text", "")
        if not text:
             return {"intent": "general", "confidence": 0.0, "method": "model_failed"}

        try:
            inputs = self.tokenizer(
                text, 
                padding=True, 
                truncation=True, 
                max_length=512, 
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = F.softmax(outputs.logits, dim=-1)
                
            confidence, predicted_class = torch.max(probs, dim=-1)
            intent = self.id2label.get(predicted_class.item(), "general")
            
            return {
                "intent": intent,
                "confidence": float(confidence),
                "method": "model",
                "id": predicted_class.item(),
                "scores": {self.id2label[i]: float(probs[0][i]) for i in self.id2label}
            }
        except Exception as e:
            logger.error(f"Model ID error: {e}")
            return {"intent": "general", "confidence": 0.0, "method": "model_error"}

    def _classify_with_rules(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based classification fallback."""
        text = email.get("combined_text", "").lower()
        sender = email.get("sender", "").lower()
        
        scores = {intent: 0.0 for intent in self.rules}
        scores["general"] = 0.1  # Base score
        
        # Check sender domain
        if "edu" in sender:
            scores["academic"] += 0.3
        if "linkedin" in sender or "recruiting" in sender:
            scores["internship"] += 0.3
            
        # Check keywords
        for intent, patterns in self.rules.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    scores[intent] += len(matches) * 0.2
                    
        # Normalize scores (simple soft-max like)
        total = sum(scores.values())
        if total > 0:
            for k in scores:
                scores[k] /= total
        
        # Get best intent
        best_intent = max(scores, key=scores.get)
        confidence = scores[best_intent]
        
        return {
            "intent": best_intent,
            "confidence": min(confidence, 1.0),
            "method": "rules",
            "scores": scores
        }
    
    def batch_classify(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify batch of emails."""
        return [self.classify(email) for email in emails]

# Example usage
if __name__ == "__main__":
    classifier = IntentClassifier(use_rules=True)
    
    test_email = {
        "sender": "prof@university.edu",
        "subject": "Assignment",
        "combined_text": "Please submit your assignment by Friday.",
        "body": "Please submit your assignment by Friday."
    }
    
    print(classifier.classify(test_email))
