"""
LLM Generator

Neural text generation for context-aware email replies.
Supports T5, FLAN-T5, and other seq2seq models.
"""

from typing import Dict, Optional, List
import re


class LLMGenerator:
    """
    Generate email responses using LLM (T5/FLAN-T5/Mistral).
    
    This is a placeholder implementation that will be replaced
    with actual model inference once models are trained.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        model_type: str = "t5-base",
        device: str = "cpu"
    ):
        """
        Initialize LLM generator.
        
        Args:
            model_path: Path to fine-tuned model
            model_type: Model architecture (t5-base, flan-t5-base, etc.)
            device: Device for inference (cpu/cuda)
        """
        self.model_path = model_path
        self.model_type = model_type
        self.device = device
        self.model = None
        self.tokenizer = None
        
        # Generation parameters
        self.max_length = 300
        self.temperature = 0.7
        self.top_p = 0.9
        self.num_beams = 4
        
        # Load model if path provided
        if model_path:
            self._load_model(model_path)
    
    def generate(
        self,
        email: Dict[str, str],
        intent: str,
        urgency: str = "medium",
        sentiment: str = "neutral",
        context: Optional[str] = None,
        user_name: str = "Rayan",
        **kwargs
    ) -> Dict[str, any]:
        """
        Generate response using LLM.
        
        Args:
            email: Email dictionary
            intent: Classified intent
            urgency: Urgency level
            sentiment: Sentiment classification
            context: Additional context from RAG (optional)
            user_name: User's name for signature
            **kwargs: Additional parameters
            
        Returns:
            Generation result with draft text
        """
        # Build prompt
        prompt = self._build_prompt(
            email=email,
            intent=intent,
            urgency=urgency,
            sentiment=sentiment,
            context=context,
            user_name=user_name
        )
        
        # Generate with model
        if self.model is not None:
            draft = self._generate_with_model(prompt)
        else:
            # Fallback to rule-based generation
            draft = self._generate_fallback(email, intent, user_name)
        
        # Post-process
        draft = self._post_process(draft, user_name)
        
        return {
            "draft": draft,
            "method": "llm" if self.model else "llm_fallback",
            "confidence": 0.80 if self.model else 0.65,
            "model_type": self.model_type,
            "word_count": len(draft.split()),
            "prompt_used": prompt[:100] + "..." if len(prompt) > 100 else prompt
        }
    
    def _build_prompt(
        self,
        email: Dict[str, str],
        intent: str,
        urgency: str,
        sentiment: str,
        context: Optional[str],
        user_name: str
    ) -> str:
        """
        Build prompt for LLM.
        
        Args:
            email: Email dictionary
            intent: Intent classification
            urgency: Urgency level
            sentiment: Sentiment
            context: RAG context
            user_name: User name
            
        Returns:
            Formatted prompt
        """
        # Instruction-based prompt for FLAN-T5 style models
        prompt = f"""Generate a professional email reply based on the following:

Intent: {intent}
Urgency: {urgency}
Sentiment: {sentiment}

Original Email:
Subject: {email.get('subject', '')}
From: {email.get('sender', '')}
Body: {email.get('body', '')[:500]}

"""
        
        # Add RAG context if available
        if context:
            prompt += f"""Relevant Context:
{context}

"""
        
        prompt += f"""Generate a {intent} reply from {user_name} that is:
- Professional and appropriate for the {urgency} urgency level
- Responsive to the sender's {sentiment} tone
- Clear and concise

Reply:"""
        
        return prompt
    
    def _generate_with_model(self, prompt: str) -> str:
        """
        Generate using loaded model.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated text
        """
        try:
            # Tokenize
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                max_length=512,
                truncation=True
            ).to(self.device)
            
            # Generate
            outputs = self.model.generate(
                **inputs,
                max_length=self.max_length,
                temperature=self.temperature,
                top_p=self.top_p,
                num_beams=self.num_beams,
                do_sample=True,
                early_stopping=True
            )
            
            # Decode
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return generated_text
        
        except Exception as e:
            print(f"Generation error: {e}")
            return self._generate_fallback({}, "general", "User")
    
    def _generate_fallback(self, email: Dict[str, str], intent: str, user_name: str) -> str:
        """
        Fallback generation when model is not available.
        
        Args:
            email: Email dictionary
            intent: Intent
            user_name: User name
            
        Returns:
            Simple generated response
        """
        sender = email.get("sender", "")
        sender_name = sender.split('@')[0].replace('.', ' ').title() if sender else "there"
        subject = email.get("subject", "your message")
        
        templates = {
            "academic": f"Dear {sender_name},\n\nThank you for your email regarding {subject}. I have received your message and will respond with the requested information shortly.\n\nBest regards,\n{user_name}",
            "internship": f"Hello {sender_name},\n\nThank you for reaching out. I appreciate the opportunity and will respond with the requested information shortly.\n\nKind regards,\n{user_name}",
            "meeting": f"Hello {sender_name},\n\nThank you for your message. I would be happy to meet. Please let me know what times work best for you.\n\nBest,\n{user_name}",
            "support": f"Hello,\n\nThank you for reaching out. I have received your request and will get back to you within 24 hours.\n\nBest regards,\n{user_name}",
            "general": f"Hello {sender_name},\n\nThank you for your email. I have received your message and will respond shortly.\n\nBest regards,\n{user_name}"
        }
        
        return templates.get(intent, templates["general"])
    
    def _post_process(self, text: str, user_name: str) -> str:
        """
        Post-process generated text.
        
        Args:
            text: Generated text
            user_name: User name
            
        Returns:
            Cleaned text
        """
        # Remove any prompt artifacts
        text = re.sub(r'^(Reply:|Response:|Email:)\s*', '', text, flags=re.IGNORECASE)
        
        # Ensure proper spacing
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Ensure signature if missing
        if user_name not in text:
            if not text.endswith('\n'):
                text += '\n'
            text += f"\nBest regards,\n{user_name}"
        
        return text.strip()
    
    def _load_model(self, model_path: str):
        """
        Load fine-tuned model.
        
        Args:
            model_path: Path to model checkpoint
        """
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
            self.model.to(self.device)
            self.model.eval()
            
            print(f"Loaded LLM model from {model_path}")
        except Exception as e:
            print(f"Failed to load model: {e}")
            print("Using fallback generation")
            self.model = None
            self.tokenizer = None
    
    def set_generation_params(
        self,
        max_length: int = 300,
        temperature: float = 0.7,
        top_p: float = 0.9,
        num_beams: int = 4
    ):
        """
        Update generation parameters.
        
        Args:
            max_length: Maximum output length
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            num_beams: Number of beams for beam search
        """
        self.max_length = max_length
        self.temperature = temperature
        self.top_p = top_p
        self.num_beams = num_beams


# Example usage
if __name__ == "__main__":
    generator = LLMGenerator(model_type="t5-base")
    
    test_email = {
        "sender": "professor.smith@university.edu",
        "subject": "Assignment Extension Request",
        "body": "Hi, I was wondering if I could get an extension on the final project. I've been dealing with some personal issues."
    }
    
    result = generator.generate(
        email=test_email,
        intent="academic",
        urgency="medium",
        sentiment="neutral",
        user_name="Rayan"
    )
    
    print("Generated Draft:")
    print(result["draft"])
    print(f"\nMethod: {result['method']}")
    print(f"Confidence: {result['confidence']}")
