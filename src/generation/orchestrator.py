"""
Generation Orchestrator Module

Coordinates generation strategies (Template, LLM, RAG) based on confidence
and availability. Implements fallback logic.
"""

import logging
from typing import Dict, Any, Optional

from src.generation.template_engine import TemplateEngine
from src.generation.llm_generator import LLMGenerator
from src.generation.rag_system import RAGSystem
from src.config_loader import config

logger = logging.getLogger(__name__)

class GenerationOrchestrator:
    """Coordinates content generation."""
    
    def __init__(self):
        self.template_engine = TemplateEngine()
        self.llm_generator = LLMGenerator()
        self.rag_system = RAGSystem()

    def generate_draft(
        self,
        email: Dict[str, Any],
        intent: str,
        urgency: str = "medium",
        user_name: str = "Rayan"
    ) -> Dict[str, Any]:
        """
        Generate draft using best available strategy.
        
        Logic:
        1. If strict template required or simple intent -> Template
        2. If RAG enabled -> RAG + LLM
        3. Fallback -> LLM
        4. Final Fallback -> Template
        """
        
        # Strategy selection logic
        strategy = config.generation.strategy
        if strategy == "auto":
            # Prefer templates for known reliable intents
            if intent in ["meeting", "spam"]:
                 strategy = "template"
            else:
                 strategy = "rag_llm"
        
        draft_result = None
        
        # 1. RAG + LLM Strategy
        if strategy in ["rag_llm", "llm"]:
            context = []
            if strategy == "rag_llm":
                context = self.rag_system.retrieve(email.get("combined_text", ""))
                
            draft_result = self.llm_generator.generate(
                email, intent, urgency, context_docs=context
            )
            
            # If LLM failed, fallback to template
            if not draft_result or draft_result.get("confidence", 0) < 0.5:
                logger.info("LLM generation failed or low confidence. Fallback to template.")
                strategy = "template"
        
        # 2. Template Strategy (Primary or Fallback)
        if strategy == "template" or not draft_result:
            draft_result = self.template_engine.generate(
                email, intent, urgency, user_name=user_name
            )
            
        return draft_result

# Example usage
if __name__ == "__main__":
    orch = GenerationOrchestrator()
    print("Orchestrator initialized.")
