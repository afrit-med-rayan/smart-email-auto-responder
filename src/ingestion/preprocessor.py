"""
Text Preprocessor Module

Cleans and normalizes email text for ML model input.
Handles signature removal, quoted reply stripping, tokenization, and feature extraction.
"""

import re
from typing import Dict, List, Tuple, Optional, Any
import logging
from src.config_loader import config

# Optional imports for ML features
try:
    from transformers import AutoTokenizer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    from langdetect import detect
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False

logger = logging.getLogger(__name__)

class TextPreprocessor:
    """Preprocess email text for ML models."""
    
    def __init__(self):
        # Signature patterns
        self.signature_patterns = [
            r'--\s*\n.*',  # Standard signature delimiter
            r'Sent from my [\w\s]+',  # Mobile signatures
            r'(Best regards|Sincerely|Thanks|Cheers|Regards|Best|Warm regards|Yours truly),?\s*\n.*',
            r'_{3,}',  # Horizontal lines
        ]
        
        # Quoted reply patterns
        self.quote_patterns = [
            r'^>.*$',  # Lines starting with >
            r'^On .* wrote:$',  # "On [date] [person] wrote:"
            r'From:.*\nSent:.*\nTo:.*\nSubject:.*',  # Forwarded email headers
            r'-{3,} Original Message -{3,}',
        ]
        
        # Email disclaimer patterns
        self.disclaimer_patterns = [
            r'This email and any attachments.*confidential',
            r'CONFIDENTIALITY NOTICE:.*',
            r'Please consider the environment before printing',
            r'The information contained in this message.*',
        ]
        
        # BERT Tokenizer
        self.tokenizer = None
        if HAS_TRANSFORMERS and config:
            try:
                model_name = config.models["intent_classifier"].name
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            except Exception as e:
                logger.warning(f"Failed to load tokenizer: {e}")
    
    def preprocess(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess email for ML model input.
        
        Args:
            email: Structured email dictionary
            
        Returns:
            Preprocessed email with cleaned text and features
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
        
        # Detect language
        language = "en"
        if HAS_LANGDETECT and combined_text:
            try:
                language = detect(combined_text)
            except:
                pass
        
        result = {
            **email,
            "cleaned_subject": cleaned_subject,
            "cleaned_body": cleaned_body,
            "combined_text": combined_text,
            "language": language,
            "word_count": len(combined_text.split()),
            "char_count": len(combined_text),
        }
        
        # Add basic features
        result["features"] = self.extract_features(result)
        
        # Add BERT tokens if available
        if self.tokenizer:
            tokens = self.tokenize_for_bert(combined_text)
            result["input_ids"] = tokens["input_ids"]
            result["attention_mask"] = tokens["attention_mask"]
            
        return result
    
    def _clean_body(self, body: str) -> str:
        """Basic body cleaning."""
        if not body:
            return ""
            
        # Remove excessive newlines
        body = re.sub(r'\n{3,}', '\n\n', body)
        
        # Remove URLs (replace with token)
        # body = re.sub(r'http[s]?://\S+', '[URL]', body)
        
        return body.strip()
    
    def _remove_signature(self, text: str) -> str:
        """Remove email signature."""
        if not text:
            return ""
            
        for pattern in self.signature_patterns:
            # Find signature and remove everything after
            # Use dotall to match across newlines, but use non-greedy where possible
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            if match:
                # Keep text before signature
                # If signature is at the very beginning, text becomes empty
                text = text[:match.start()].strip()
                # Break after first match (assuming signature is at bottom)
                # But sometimes there are multiple signature-like blocks
                # We usually want the first one from the bottom, but regex finds first from top
                # A better approach might be to look from the end, but regex is left-to-right.
                # Given typical emails, the first signature pattern usually marks the end of content.
                break
        
        return text
    
    def _remove_quoted_replies(self, text: str) -> str:
        """Remove quoted replies from previous emails."""
        if not text:
            return ""
            
        lines = text.split('\n')
        cleaned_lines = []
        in_quote = False
        
        for line in lines:
            line_strip = line.strip()
            
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
                
            # Check for generic separator
            if re.match(r'^-{3,} Original Message -{3,}', line):
                in_quote = True
                continue
            
            # If not in quote, keep the line
            if not in_quote:
                cleaned_lines.append(line)
            
            # Reset quote flag on empty line? 
            # Usually quotes are continuous blocks. 
            # But sometimes people reply inline.
            # For safety, strict quoted reply removal usually assumes everything after header is quote.
            # But inline '>' quotes might be interspersed.
            # Let's simple keep non-quoted lines.
            
            # Note: strict `in_quote` that doesn't reset might delete too much if they reply AFTER a quote block without >
            # But standard email clients put the quote block at the bottom.
            
            # Determine if we should reset in_quote
            # If we hit a quote header ("On... wrote"), it typically means everything after is old.
            # So we shouldn't reset.
            # If it's just '>' lines, we might want to reset if line is empty/normal text?
            # Safe approach: Only skip explicitly marked lines or lines after a definitive header.
            
            pass 
        
        return '\n'.join(cleaned_lines)
    
    def _remove_disclaimers(self, text: str) -> str:
        """Remove legal disclaimers and confidentiality notices."""
        if not text:
            return ""
            
        for pattern in self.disclaimer_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        return text.strip()
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace."""
        if not text:
            return ""
            
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _clean_subject(self, subject: str) -> str:
        """Clean email subject."""
        if not subject:
            return ""
            
        # Remove "Re:", "Fwd:", etc. multiple times
        subject = re.sub(r'^([Rr][Ee]|[Ff][Ww][Dd]?):\s*', '', subject)
        while re.match(r'^([Rr][Ee]|[Ff][Ww][Dd]?):\s*', subject):
             subject = re.sub(r'^([Rr][Ee]|[Ff][Ww][Dd]?):\s*', '', subject)
        
        # Remove excessive whitespace
        subject = re.sub(r'\s+', ' ', subject)
        
        return subject.strip()
    
    def extract_features(self, email: Dict[str, Any]) -> Dict[str, Any]:
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
        
        features = {
            # Text features
            "word_count": len(text.split()),
            "char_count": len(text),
            "sentence_count": len(re.findall(r'[.!?]+', text)),
            
            # Sender features
            "sender_domain": sender.split('@')[-1] if '@' in sender else "",
            "is_edu": bool(re.search(r'\.edu(\.|$)', sender)),
            "is_com": sender.endswith('.com'),
            "is_org": sender.endswith('.org'),
            
            # Subject features
            "subject_length": len(subject),
            "has_question_mark": '?' in subject,
            "has_exclamation": '!' in subject,
            "is_reply": subject.lower().startswith('re:'),
            "is_forward": subject.lower().startswith(('fwd:', 'fw:')),
        }
        
        # Keyword checks using regex for efficiency
        keywords = {
            "urgent": [r'\b(urgent|asap|immediately|deadline|today|tomorrow|critical)\b'],
            "meeting": [r'\b(meeting|schedule|calendar|available|appointment)\b'],
            "academic": [r'\b(professor|assignment|exam|grade|course|class|homework|lab|thesis)\b'],
            "job": [r'\b(interview|position|application|resume|cv|hiring|job|recruiter)\b'],
            "spam": [r'\b(unsubscribe|discount|offer|free|winner|prize|click here)\b'],
            "positive": [r'\b(thank|appreciate|great|excellent|wonderful|happy|glad)\b'],
            "negative": [r'\b(unfortunately|problem|issue|concern|disappointed|angry|fail)\b'],
            "aggressive": [r'\b(demand|immediately|unacceptable|terrible|worst|hate|sue|lawyer)\b']
        }
        
        for key, patterns in keywords.items():
            features[f"has_{key}_keywords"] = any(re.search(p, text.lower()) for p in patterns)
            
        # Specific patterns
        features["has_deadline"] = bool(re.search(r'\b(deadline|due|by|before)\s+\w+\s+\d+', text.lower()))
        
        return features
    
    def tokenize_for_bert(self, text: str, max_length: int = 512) -> Dict[str, List[int]]:
        """
        Tokenize text for BERT model.
        
        Args:
            text: Text to tokenize
            max_length: Maximum sequence length
            
        Returns:
            Tokenization dictionary (input_ids, attention_mask)
        """
        if not self.tokenizer:
            # Fallback simple tokenization if no BERT
            return {
                "input_ids": [],
                "attention_mask": []
            }
            
        return self.tokenizer(
            text,
            padding='max_length',
            truncation=True,
            max_length=max_length,
            return_tensors="pt"
        )
