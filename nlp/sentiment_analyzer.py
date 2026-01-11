"""
Enhanced Sentiment Analyzer

Analyzes email sentiment and tone using DistilBERT model.
Detects aggressive or negative emails for safety filtering.
"""

import re
import logging
from typing import Dict, List, Optional, Any
from src.config_loader import config

try:
    import torch
    from torch.nn import functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Optional transformers import
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Analyze email sentiment and tone.
    
    Classes: positive, negative, neutral
    Safety: Detects aggressive tone
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.device = None
        if HAS_TORCH:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
        self.model = None
        self.tokenizer = None
        
        # Load model if configured
        if HAS_TRANSFORMERS and HAS_TORCH and config:
            try:
                model_name = model_path or config.models["sentiment_analyzer"].name
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
                self.model.to(self.device)
                self.model.eval()
            except Exception as e:
                logger.warning(f"Failed to load Sentiment model: {e}")
                
        # Aggressive keywords (Safety Net)
        self.aggressive_keywords = [
            r'\b(demand|immediately|unacceptable|terrible|worst|hate|sue|lawyer|idiot|stupid)\b',
            r'\b(fuck|shit|damn|hell)\b'
        ]

    def analyze(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze email sentiment.
        
        Args:
            email: Preprocessed email
            
        Returns:
            Sentiment result
        """
        text = email.get("combined_text", "")
        
        # 1. Safety Check: Aggression
        if self._check_aggression(text):
             return {
                "sentiment": "negative",
                "tone": "aggressive",
                "confidence": 0.95,
                "escalate": True,
                "reasoning": "Aggressive language detected"
             }

        # 2. ML Sentiment Analysis
        if self.model and self.tokenizer:
            return self._analyze_with_model(text)
            
        # 3. Fallback Rule-based (simplified)
        return self._analyze_with_rules(text)

    def _check_aggression(self, text: str) -> bool:
        """Check for aggressive keywords or shouting."""
        # Keywords
        for pattern in self.aggressive_keywords:
            if re.search(pattern, text, re.IGNORECASE):
                return True
                
        # Shouting (Caps > 50% and length > 20 chars)
        if len(text) > 20:
            caps_count = sum(1 for c in text if c.isupper())
            if caps_count / len(text) > 0.5:
                return True
                
        return False

    def _analyze_with_model(self, text: str) -> Dict[str, Any]:
        """Analyze using BERT model."""
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
            
            # Assuming binary (negative=0, positive=1) for SST-2
            # Adjust if using different model
            neg_score = probs[0][0].item()
            pos_score = probs[0][1].item()
            
            if pos_score > 0.6:
                sentiment = "positive"
                confidence = pos_score
            elif neg_score > 0.6:
                sentiment = "negative"
                confidence = neg_score
            else:
                sentiment = "neutral"
                confidence = max(pos_score, neg_score)
                
            return {
                "sentiment": sentiment,
                "tone": "neutral", # Default, refine later with rules
                "confidence": float(confidence),
                "escalate": False,
                "scores": {"pos": pos_score, "neg": neg_score}
            }
        except Exception as e:
            logger.error(f"Sentiment model error: {e}")
            return self._analyze_with_rules(text)

    def _analyze_with_rules(self, text: str) -> Dict[str, Any]:
        """Simple rule-fallback."""
        pos_words = ["thank", "great", "good", "happy", "appreciate"]
        neg_words = ["bad", "wrong", "issue", "problem", "missed"]
        
        text_lower = text.lower()
        pos_count = sum(1 for w in pos_words if w in text_lower)
        neg_count = sum(1 for w in neg_words if w in text_lower)
        
        if pos_count > neg_count:
            return {"sentiment": "positive", "confidence": 0.6, "tone": "friendly", "escalate": False}
        elif neg_count > pos_count:
            return {"sentiment": "negative", "confidence": 0.6, "tone": "concerned", "escalate": False}
            
        return {"sentiment": "neutral", "confidence": 0.5, "tone": "neutral", "escalate": False}
