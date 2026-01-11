"""
LLM Generator Module

Neural text generation for complex, context-aware replies using T5/FLAN-T5.
"""

import logging
from typing import Dict, List, Optional, Any
from src.config_loader import config

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Optional transformers import
try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

logger = logging.getLogger(__name__)

class LLMGenerator:
    """Generate email responses using T5/FLAN-T5."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.device = None
        if HAS_TORCH:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
        self.model = None
        self.tokenizer = None
        
        if HAS_TRANSFORMERS and HAS_TORCH and config:
            try:
                model_name = model_path or config.models["text_generator"].name
                logger.info(f"Loading LLM: {model_name}")
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                self.model.to(self.device)
                self.model.eval()
            except Exception as e:
                logger.warning(f"Failed to load LLM model: {e}")

    def generate(
        self, 
        email: Dict[str, Any],
        intent: str,
        urgency: str,
        context_docs: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate reply using LLM.
        
        Args:
            email: Email dictionary
            intent: Classified intent
            urgency: Urgency level
            context_docs: Optional list of RAG context strings
            
        Returns:
            Generation result
        """
        if not self.model or not self.tokenizer:
            return {"draft": "", "confidence": 0.0, "method": "llm_unavailable"}
            
        # Construct Prompt
        # T5 works best with tasks prefixes
        prompt = self._construct_prompt(email, intent, urgency, context_docs)
        
        try:
            inputs = self.tokenizer(
                prompt, 
                max_length=512, 
                truncation=True, 
                return_tensors="pt"
            ).to(self.device)
            
            # Generation parameters
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=config.models["text_generator"].max_length,
                min_length=20,
                do_sample=True,
                temperature=config.models["text_generator"].temperature,
                top_p=config.models["text_generator"].top_p,
                num_beams=4,
                early_stopping=True
            )
            
            draft = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return {
                "draft": draft,
                "method": "llm",
                "confidence": 0.85, # Heuristic, real confidence needs logits analysis
                "word_count": len(draft.split())
            }
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return {"draft": "", "confidence": 0.0, "method": "llm_error", "error": str(e)}

    def _construct_prompt(
        self, 
        email: Dict[str, Any], 
        intent: str, 
        urgency: str, 
        context_docs: List[str] = None
    ) -> str:
        """Construct prompt for T5."""
        sender_name = email.get("sender", "Sender")
        subject = email.get("subject", "")
        body = email.get("body", "")[:300] # Truncate body for prompt context
        
        context_str = ""
        if context_docs:
            context_str = "Context: " + " ".join(context_docs)[:500] + "\n"
            
        # Template for T5 - instructing it to write an email
        prompt = f"""
Write a {urgency} {intent} email reply.
Sender: {sender_name}
Subject: {subject}
Message: {body}
{context_str}
Reply:
"""
        return prompt.strip()

# Example usage
if __name__ == "__main__":
    generator = LLMGenerator()
    print("LLM Generator initialized.")
