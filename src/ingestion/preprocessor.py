"""
Text Preprocessor Module

Cleans and normalizes email text for ML model input.
Handles signature removal, quoted reply stripping, and tokenization.
"""

import re
from typing import Dict, List, Tuple, Optional


class TextPreprocessor:
    """Preprocess email text for ML models."""
    
    def __init__(self):
        # Signature patterns
        self.signature_patterns = [
            r'--\s*\n.*',  # Standard signature delimiter
            r'Sent from my [\w\s]+',  # Mobile signatures
            r'(Best regards|Sincerely|Thanks|Cheers|Regards),?\s*\n.*',
            r'_{3,}',  # Horizontal lines
        ]
        
        # Quoted reply patterns
        self.quote_patterns = [
            r'^>.*$',  # Lines starting with >
            r'^On .* wrote:$',  # "On [date] [person] wrote:"
            r'From:.*\nSent:.*\nTo:.*\nSubject:.*',  # Forwarded email headers
        ]
        
        # Email disclaimer patterns
        self.disclaimer_patterns = [
            r'This email and any attachments.*confidential',
            r'CONFIDENTIALITY NOTICE:.*',
            r'Please consider the environment before printing',
        ]
    
    def preprocess(self, email: Dict[str, str]) -> Dict[str, str]:
        """
        Preprocess email for ML model input.
        
        Args:
            email: Structured email dictionary
            
        Returns:
            Preprocessed email with cleaned text
        """
        subject = email.get("subject", "")
        body = email.get("body", "")
        
        # Clean body
        cleaned_body = self._clean_body(body)
        
        # Remove signature
        cleaned_body = self._remove_signature(cleaned_body)
        
        # Remove quoted replies
        cleaned_body = self._remove_quoted_replies(cleaned_body)
        
        # Remove disclaimers
        cleaned_body = self._remove_disclaimers(cleaned_body)
        
        # Normalize whitespace
        cleaned_body = self._normalize_whitespace(cleaned_body)
        
        # Clean subject
        cleaned_subject = self._clean_subject(subject)
        
        # Combine for model input
        combined_text = f"{cleaned_subject} {cleaned_body}".strip()
        
        return {
            **email,
            "cleaned_subject": cleaned_subject,
            "cleaned_body": cleaned_body,
            "combined_text": combined_text,
            "word_count": len(combined_text.split()),
            "char_count": len(combined_text),
        }
    
    def _clean_body(self, body: str) -> str:
        """Basic body cleaning."""
        # Remove excessive newlines
        body = re.sub(r'\n{3,}', '\n\n', body)
        
        # Remove URLs (optional - keep for now as they might be relevant)
        # body = re.sub(r'http[s]?://\S+', '[URL]', body)
        
        # Remove email addresses in body (keep sender/recipient)
        # body = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', body)
        
        return body.strip()
    
    def _remove_signature(self, text: str) -> str:
        """Remove email signature."""
        for pattern in self.signature_patterns:
            # Find signature and remove everything after
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            if match:
                text = text[:match.start()].strip()
                break
        
        return text
    
    def _remove_quoted_replies(self, text: str) -> str:
        """Remove quoted replies from previous emails."""
        lines = text.split('\n')
        cleaned_lines = []
        in_quote = False
        
        for line in lines:
            # Check if line is a quote
            if re.match(r'^>+\s*', line):
                in_quote = True
                continue
            
            # Check for "On ... wrote:" pattern
            if re.match(r'^On .* wrote:$', line, re.IGNORECASE):
                in_quote = True
                continue
            
            # Check for forwarded email headers
            if re.match(r'^(From|Sent|To|Subject):', line):
                in_quote = True
                continue
            
            # If not in quote, keep the line
            if not in_quote:
                cleaned_lines.append(line)
            
            # Reset quote flag on empty line
            if not line.strip():
                in_quote = False
        
        return '\n'.join(cleaned_lines)
    
    def _remove_disclaimers(self, text: str) -> str:
        """Remove legal disclaimers and confidentiality notices."""
        for pattern in self.disclaimer_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        return text.strip()
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace."""
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def _clean_subject(self, subject: str) -> str:
        """Clean email subject."""
        # Remove "Re:", "Fwd:", etc.
        subject = re.sub(r'^(Re|Fwd|Fw):\s*', '', subject, flags=re.IGNORECASE)
        
        # Remove excessive whitespace
        subject = re.sub(r'\s+', ' ', subject)
        
        return subject.strip()
    
    def extract_features(self, email: Dict[str, str]) -> Dict[str, any]:
        """
        Extract additional features for classification.
        
        Args:
            email: Preprocessed email
            
        Returns:
            Feature dictionary
        """
        text = email.get("combined_text", "")
        sender = email.get("sender", "")
        subject = email.get("subject", "")
        
        return {
            # Text features
            "word_count": len(text.split()),
            "char_count": len(text),
            "sentence_count": len(re.findall(r'[.!?]+', text)),
            "avg_word_length": sum(len(word) for word in text.split()) / max(len(text.split()), 1),
            
            # Sender features
            "sender_domain": sender.split('@')[-1] if '@' in sender else "",
            "is_edu": sender.endswith('.edu'),
            "is_com": sender.endswith('.com'),
            "is_org": sender.endswith('.org'),
            
            # Subject features
            "subject_length": len(subject),
            "has_question_mark": '?' in subject,
            "has_exclamation": '!' in subject,
            "is_reply": subject.lower().startswith('re:'),
            "is_forward": subject.lower().startswith(('fwd:', 'fw:')),
            
            # Urgency indicators
            "has_urgent_keywords": bool(re.search(
                r'\b(urgent|asap|immediately|deadline|today|tomorrow|critical)\b',
                text.lower()
            )),
            "has_deadline": bool(re.search(
                r'\b(deadline|due|by|before)\s+\w+\s+\d+',
                text.lower()
            )),
            
            # Intent indicators
            "has_meeting_keywords": bool(re.search(
                r'\b(meeting|schedule|calendar|available|appointment)\b',
                text.lower()
            )),
            "has_academic_keywords": bool(re.search(
                r'\b(professor|assignment|exam|grade|course|class|homework)\b',
                text.lower()
            )),
            "has_job_keywords": bool(re.search(
                r'\b(interview|position|application|resume|cv|hiring|job)\b',
                text.lower()
            )),
            "has_spam_keywords": bool(re.search(
                r'\b(unsubscribe|discount|offer|free|winner|prize|click here)\b',
                text.lower()
            )),
            
            # Sentiment indicators
            "has_positive_words": bool(re.search(
                r'\b(thank|appreciate|great|excellent|wonderful|happy)\b',
                text.lower()
            )),
            "has_negative_words": bool(re.search(
                r'\b(unfortunately|problem|issue|concern|disappointed|angry)\b',
                text.lower()
            )),
            "has_aggressive_words": bool(re.search(
                r'\b(demand|immediately|unacceptable|terrible|worst|hate)\b',
                text.lower()
            )),
        }
    
    def tokenize_for_bert(self, text: str, max_length: int = 512) -> Dict[str, List[int]]:
        """
        Tokenize text for BERT model (placeholder - will use transformers tokenizer).
        
        Args:
            text: Text to tokenize
            max_length: Maximum sequence length
            
        Returns:
            Tokenization dictionary (placeholder)
        """
        # This is a placeholder - actual implementation will use transformers.AutoTokenizer
        return {
            "text": text[:max_length * 4],  # Rough approximation
            "max_length": max_length,
        }


# Example usage
if __name__ == "__main__":
    preprocessor = TextPreprocessor()
    
    sample_email = {
        "sender": "professor@university.edu",
        "subject": "Re: Assignment Deadline Extension",
        "body": """Hi Student,

I wanted to let you know that the deadline for the final project has been extended to next Friday.

Best regards,
Professor Smith

--
Professor John Smith
Department of Computer Science
University Example
"""
    }
    
    # Preprocess
    cleaned = preprocessor.preprocess(sample_email)
    print("Cleaned Body:")
    print(cleaned["cleaned_body"])
    print("\nCombined Text:")
    print(cleaned["combined_text"])
    
    # Extract features
    features = preprocessor.extract_features(cleaned)
    print("\nFeatures:")
    print(f"Word count: {features['word_count']}")
    print(f"Is .edu: {features['is_edu']}")
    print(f"Has academic keywords: {features['has_academic_keywords']}")
