"""
Template Engine

Rule-based response generation using Jinja2 templates.
Provides fast, consistent responses for common scenarios.
"""

from typing import Dict, Optional
from jinja2 import Template


class TemplateEngine:
    """Generate email responses using templates."""
    
    def __init__(self):
        # Define templates for each intent
        self.templates = {
            "academic": Template("""Dear {{ sender_name }},

Thank you for your email regarding {{ subject }}.

{% if urgency == "critical" or urgency == "high" %}
I have received your message and will respond with the requested information as soon as possible.
{% else %}
I have received your message and will get back to you shortly with the requested information.
{% endif %}

{% if has_deadline %}
I understand the deadline is {{ deadline }}, and I will ensure to respond in time.
{% endif %}

Best regards,
{{ user_name }}"""),
            
            "internship": Template("""Hello {{ sender_name }},

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
            
            "meeting": Template("""Hello {{ sender_name }},

Thank you for your message about {{ subject }}.

{% if urgency == "critical" or urgency == "high" %}
I am available at the proposed time and look forward to our meeting.
{% else %}
I would be happy to meet. Please let me know what times work best for you, and I will confirm my availability.
{% endif %}

Best,
{{ user_name }}"""),
            
            "support": Template("""Hello,

Thank you for reaching out regarding {{ subject }}.

I have received your request and will look into this matter. I will get back to you {% if urgency == "critical" %}as soon as possible{% elif urgency == "high" %}within 24 hours{% else %}within 2-3 business days{% endif %} with a solution.

Best regards,
{{ user_name }}"""),
            
            "general": Template("""Hello {{ sender_name }},

Thank you for your email regarding {{ subject }}.

I have received your message and will respond shortly.

Best regards,
{{ user_name }}"""),
        }
    
    def generate(
        self,
        email: Dict[str, str],
        intent: str,
        urgency: str = "medium",
        user_name: str = "Rayan",
        **kwargs
    ) -> Dict[str, any]:
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
                "confidence": 0.85,  # Templates are reliable
                "template_used": intent,
                "word_count": len(draft.split()),
            }
        except Exception as e:
            # Fallback to simple template
            return {
                "draft": f"Hello,\n\nThank you for your email. I will respond shortly.\n\nBest regards,\n{user_name}",
                "method": "template_fallback",
                "confidence": 0.70,
                "error": str(e),
                "word_count": 15,
            }
    
    def _extract_name(self, email_address: str) -> str:
        """
        Extract name from email address.
        
        Args:
            email_address: Email address
            
        Returns:
            Extracted name or "there"
        """
        if not email_address:
            return "there"
        
        # Try to extract name from email
        # Example: john.doe@example.com -> John Doe
        local_part = email_address.split('@')[0]
        
        # Replace dots and underscores with spaces
        name = local_part.replace('.', ' ').replace('_', ' ')
        
        # Capitalize
        name = ' '.join(word.capitalize() for word in name.split())
        
        return name if name else "there"
    
    def _extract_deadline(self, text: str) -> str:
        """
        Extract deadline mention from text.
        
        Args:
            text: Email body
            
        Returns:
            Deadline text or empty string
        """
        import re
        
        patterns = [
            r'deadline\s+(?:is\s+)?(?:on\s+)?(\w+\s+\d+)',
            r'due\s+(?:on\s+)?(\w+\s+\d+)',
            r'by\s+(\w+\s+\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def add_custom_template(self, intent: str, template_str: str):
        """
        Add or update a custom template.
        
        Args:
            intent: Intent name
            template_str: Jinja2 template string
        """
        self.templates[intent] = Template(template_str)


# Example usage
if __name__ == "__main__":
    engine = TemplateEngine()
    
    test_email = {
        "sender": "professor.smith@university.edu",
        "subject": "Assignment Extension Request",
        "body": "Can I get an extension? The deadline is Friday."
    }
    
    result = engine.generate(
        email=test_email,
        intent="academic",
        urgency="high",
        user_name="Rayan"
    )
    
    print("Generated Draft:")
    print(result["draft"])
    print(f"\nMethod: {result['method']}")
    print(f"Confidence: {result['confidence']}")
