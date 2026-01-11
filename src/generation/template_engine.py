"""
Template Engine

Rule-based response generation using Jinja2 templates.
Provides fast, consistent responses for common scenarios.
"""

import re
import logging
from typing import Dict, List, Optional, Any
from src.config_loader import config

try:
    from jinja2 import Template
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

class SimpleTemplate:
    """Fallback template engine using simple string replacement."""
    def __init__(self, text):
        self.text = text
    
    def render(self, **kwargs):
        """Very basic render - only replaces {{ var }}"""
        result = self.text
        for k, v in kwargs.items():
            if isinstance(v, str): # Simple only
                result = result.replace(f"{{{{ {k} }}}}", v)
        
        # Remove Logic blocks (naive removal)
        result = re.sub(r'\{% .*? %\}', '', result, flags=re.DOTALL)
        
        # Remove empty lines left by blocks (simplistic)
        return "\n".join([line for line in result.split("\n") if line.strip()])

logger = logging.getLogger(__name__)

class TemplateEngine:
    """Generate email responses using templates."""
    
    def __init__(self):
        # Define templates for each intent
        if HAS_JINJA2:
             TemplateClass = Template
        else:
             TemplateClass = SimpleTemplate

        self.templates = {
            "academic": TemplateClass("""Dear {{ sender_name }},

Thank you for your email regarding {{ subject }}.

{% if urgency == "critical" or urgency == "high" %}
I have received your message and will respond with the requested information as soon as possible.
{% else %}
I have received your message and will get back to you shortly with the requested information.
{% endif %}

{% if has_deadline and deadline %}
I understand the deadline is {{ deadline }}, and I will ensure to respond in time.
{% endif %}

Best regards,
{{ user_name }}"""),
            
            "internship": TemplateClass("""Hello {{ sender_name }},

Thank you for reaching out regarding {{ subject }}.

{% if "interview" in subject.lower() %}
I appreciate the opportunity and am very interested in this position. I am available for an interview and will confirm my availability shortly.
{% elif "application" in subject.lower() %}
Thank you for considering my application. I am very interested in this opportunity and look forward to hearing from you.
{% else %}
I appreciate the opportunity and will respond with the requested information shortly.
{% endif %}

Kind regards,
{{ user_name }}"""),
            
            "meeting": TemplateClass("""Hello {{ sender_name }},

Thank you for your message about {{ subject }}.

{% if urgency == "critical" or urgency == "high" %}
I am available at the proposed time and look forward to our meeting.
{% else %}
I would be happy to meet. Please let me know what times work best for you, and I will confirm my availability.
{% endif %}

Best,
{{ user_name }}"""),
            
            "support": TemplateClass("""Hello,

Thank you for reaching out regarding {{ subject }}.

I have received your request and will look into this matter. I will get back to you {% if urgency == "critical" %}as soon as possible{% elif urgency == "high" %}within 24 hours{% else %}within 2-3 business days{% endif %} with a solution.

Best regards,
{{ user_name }}"""),
            
            "general": TemplateClass("""Hello {{ sender_name }},

Thank you for your email regarding {{ subject }}.

I have received your message and will respond shortly.

Best regards,
{{ user_name }}"""),

            # Fallback simple template
            "fallback": TemplateClass("""Hello,

Thank you for your email. I will respond shortly.

Best regards,
{{ user_name }}""")
        }
    
    def generate(
        self,
        email: Dict[str, Any],
        intent: str,
        urgency: str = "medium",
        user_name: str = "Rayan",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response using template.
        
        Args:
            email: Email dictionary
            intent: Classified intent
            urgency: Urgency level
            user_name: User's name for signature
            **kwargs: Additional template variables
            
        Returns:
            Generation result with draft text
        """
        # Get template for intent
        template = self.templates.get(intent, self.templates["general"])
        
        # Extract sender name
        sender = email.get("sender", "")
        sender_name = self._extract_name(sender)
        
        # Prepare template variables
        context = {
            "sender_name": sender_name,
            "subject": email.get("subject", "your message"),
            "urgency": urgency,
            "user_name": user_name,
            "has_deadline": "deadline" in email.get("body", "").lower(),
            "deadline": self._extract_deadline(email.get("body", "")),
            **kwargs
        }
        
        # Render template
        try:
            draft = template.render(**context)
            
            return {
                "draft": draft.strip(),
                "method": "template",
                "confidence": 0.90,  # Templates are reliable if intent is correct
                "template_used": intent,
                "word_count": len(draft.split()),
            }
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            # Fallback
            draft = self.templates["fallback"].render(user_name=user_name)
            return {
                "draft": draft,
                "method": "template_fallback",
                "confidence": 0.70,
                "error": str(e),
                "word_count": len(draft.split()),
            }
    
    def _extract_name(self, email_address: str) -> str:
        """Name extraction logic."""
        if not email_address:
            return "there"
            
        # If format is "Name <email>", extract Name
        if "<" in email_address:
            name_part = email_address.split("<")[0].strip()
            if name_part:
                return name_part.replace('"', '').strip()
        
        # Fallback: Try to extract name from email local part
        local_part = email_address.split('@')[0]
        name = local_part.replace('.', ' ').replace('_', ' ')
        name = ' '.join(word.capitalize() for word in name.split())
        
        return name if name else "there"
    
    def _extract_deadline(self, text: str) -> str:
        """Simple regex extraction for template context."""
        patterns = [
            r'\bdeadline\s+(?:is\s+)?(?:on\s+)?((?:\w+\s+\d+)|today|tomorrow|friday|monday)\b',
            r'\bdue\s+(?:on\s+)?((?:\w+\s+\d+)|today|tomorrow|friday|monday)\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""

# Example usage
if __name__ == "__main__":
    engine = TemplateEngine()
    print("Template Engine initialized.")
