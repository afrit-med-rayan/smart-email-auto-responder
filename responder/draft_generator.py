"""
Draft Generator - Generation Orchestrator

Coordinates multiple generation strategies (Template, LLM, RAG) with fallback logic.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Optional
from src.generation.template_engine import TemplateEngine
from src.generation.llm_generator import LLMGenerator
from src.generation.rag_system import RAGSystem
from src.validation.validator import ResponseValidator


class DraftGenerator:
    """
    Orchestrate email draft generation.
    
    Strategy:
    1. Try RAG + LLM for specialized domains
    2. Fallback to LLM only
    3. Fallback to template-based
    """
    
    def __init__(
        self,
        llm_model_path: Optional[str] = None,
        knowledge_base_path: Optional[str] = None,
        user_name: str = "Rayan",
        use_rag: bool = True,
        use_llm: bool = True,
        use_templates: bool = True
    ):
        """
        Initialize draft generator.
        
        Args:
            llm_model_path: Path to fine-tuned LLM
            knowledge_base_path: Path to knowledge base for RAG
            user_name: User's name for signatures
            use_rag: Enable RAG
            use_llm: Enable LLM generation
            use_templates: Enable template generation
        """
        self.user_name = user_name
        self.use_rag = use_rag
        self.use_llm = use_llm
        self.use_templates = use_templates
        
        # Initialize components
        self.template_engine = TemplateEngine() if use_templates else None
        self.llm_generator = LLMGenerator(model_path=llm_model_path) if use_llm else None
        self.rag_system = RAGSystem(knowledge_base_path=knowledge_base_path) if use_rag else None
        self.validator = ResponseValidator()
    
    def generate(
        self,
        email: Dict[str, str],
        intent: Dict[str, any],
        urgency: Dict[str, any],
        sentiment: Dict[str, any],
        **kwargs
    ) -> Dict[str, any]:
        """
        Generate email draft using best available strategy.
        
        Args:
            email: Preprocessed email dictionary
            intent: Intent classification result
            urgency: Urgency detection result
            sentiment: Sentiment analysis result
            **kwargs: Additional parameters
            
        Returns:
            Generation result with draft and metadata
        """
        intent_label = intent.get("intent", "general")
        urgency_level = urgency.get("urgency", "medium")
        sentiment_label = sentiment.get("sentiment", "neutral")
        
        # Safety check: escalate aggressive emails
        if sentiment.get("escalate", False):
            return {
                "draft": None,
                "method": "escalated",
                "confidence": 0.0,
                "reason": "Aggressive tone detected - requires human review",
                "escalate": True
            }
        
        # Strategy 1: RAG + LLM for specialized domains
        if self.use_rag and self.rag_system and intent_label in ["academic", "internship", "support"]:
            result = self._generate_with_rag_llm(
                email, intent_label, urgency_level, sentiment_label
            )
            if result and result.get("confidence", 0) > 0.75:
                return result
        
        # Strategy 2: LLM only
        if self.use_llm and self.llm_generator:
            result = self._generate_with_llm(
                email, intent_label, urgency_level, sentiment_label
            )
            if result and result.get("confidence", 0) > 0.70:
                return result
        
        # Strategy 3: Template-based (fallback)
        if self.use_templates and self.template_engine:
            result = self._generate_with_template(
                email, intent_label, urgency_level
            )
            return result
        
        # Final fallback: simple response
        return {
            "draft": f"Hello,\n\nThank you for your email. I will respond shortly.\n\nBest regards,\n{self.user_name}",
            "method": "fallback",
            "confidence": 0.60,
            "reason": "All generation strategies failed"
        }
    
    def _generate_with_rag_llm(
        self,
        email: Dict[str, str],
        intent: str,
        urgency: str,
        sentiment: str
    ) -> Optional[Dict[str, any]]:
        """Generate using RAG + LLM."""
        try:
            # Retrieve context
            context = self.rag_system.augment_prompt(email, intent)
            
            if not context:
                return None
            
            # Generate with LLM using context
            result = self.llm_generator.generate(
                email=email,
                intent=intent,
                urgency=urgency,
                sentiment=sentiment,
                context=context,
                user_name=self.user_name
            )
            
            # Update method
            result["method"] = "rag_llm"
            result["rag_context_used"] = True
            
            return result
        
        except Exception as e:
            print(f"RAG+LLM generation failed: {e}")
            return None
    
    def _generate_with_llm(
        self,
        email: Dict[str, str],
        intent: str,
        urgency: str,
        sentiment: str
    ) -> Optional[Dict[str, any]]:
        """Generate using LLM only."""
        try:
            result = self.llm_generator.generate(
                email=email,
                intent=intent,
                urgency=urgency,
                sentiment=sentiment,
                user_name=self.user_name
            )
            
            return result
        
        except Exception as e:
            print(f"LLM generation failed: {e}")
            return None
    
    def _generate_with_template(
        self,
        email: Dict[str, str],
        intent: str,
        urgency: str
    ) -> Dict[str, any]:
        """Generate using template."""
        try:
            result = self.template_engine.generate(
                email=email,
                intent=intent,
                urgency=urgency,
                user_name=self.user_name
            )
            
            return result
        
        except Exception as e:
            print(f"Template generation failed: {e}")
            return {
                "draft": f"Hello,\n\nThank you for your email. I will respond shortly.\n\nBest regards,\n{self.user_name}",
                "method": "template_fallback",
                "confidence": 0.65,
                "error": str(e)
            }
    
    def validate_draft(
        self,
        draft: str,
        email: Dict[str, str],
        intent: Dict[str, any],
        urgency: Dict[str, any],
        sentiment: Dict[str, any],
        generation_confidence: float
    ) -> Dict[str, any]:
        """
        Validate generated draft.
        
        Args:
            draft: Generated draft text
            email: Original email
            intent: Intent classification
            urgency: Urgency detection
            sentiment: Sentiment analysis
            generation_confidence: Confidence from generator
            
        Returns:
            Validation result
        """
        # Get minimum classification confidence
        classification_confidence = min(
            intent.get("confidence", 0),
            urgency.get("confidence", 0),
            sentiment.get("confidence", 0)
        )
        
        return self.validator.validate(
            draft=draft,
            email=email,
            intent=intent.get("intent", "general"),
            urgency=urgency.get("urgency", "medium"),
            sentiment=sentiment.get("sentiment", "neutral"),
            generation_confidence=generation_confidence,
            classification_confidence=classification_confidence
        )


# Backward compatibility function
def generate_draft(email: Dict[str, str], intent: Dict[str, any]) -> str:
    """
    Legacy function for backward compatibility.
    
    Args:
        email: Email dictionary
        intent: Intent classification result
        
    Returns:
        Generated draft text
    """
    generator = DraftGenerator()
    
    # Create dummy urgency and sentiment
    urgency = {"urgency": "medium", "confidence": 0.75}
    sentiment = {"sentiment": "neutral", "confidence": 0.75, "escalate": False}
    
    result = generator.generate(email, intent, urgency, sentiment)
    
    return result.get("draft", "")


# Example usage
if __name__ == "__main__":
    generator = DraftGenerator(user_name="Rayan")
    
    test_email = {
        "sender": "professor.smith@university.edu",
        "subject": "Assignment Extension Request",
        "body": "Hi, I was wondering if I could get an extension on the final project due to personal issues."
    }
    
    intent = {"intent": "academic", "confidence": 0.85}
    urgency = {"urgency": "medium", "confidence": 0.80}
    sentiment = {"sentiment": "neutral", "confidence": 0.75, "escalate": False}
    
    result = generator.generate(test_email, intent, urgency, sentiment)
    
    print("Generated Draft:")
    print(result["draft"])
    print(f"\nMethod: {result['method']}")
    print(f"Confidence: {result['confidence']}")
    
    # Validate
    if result["draft"]:
        validation = generator.validate_draft(
            draft=result["draft"],
            email=test_email,
            intent=intent,
            urgency=urgency,
            sentiment=sentiment,
            generation_confidence=result["confidence"]
        )
        
        print(f"\nValidation Passed: {validation['passed']}")
        print(f"Recommendation: {validation['recommendation']}")
