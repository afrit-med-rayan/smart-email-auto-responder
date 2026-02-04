"""
Unit tests for text preprocessor module.

Tests email cleaning, signature removal, quoted reply handling, and feature extraction.
"""

import pytest
from typing import Dict, Any
from src.ingestion.preprocessor import TextPreprocessor


class TestTextPreprocessor:
    """Test TextPreprocessor class."""
    
    @pytest.fixture
    def preprocessor(self) -> TextPreprocessor:
        """Create a TextPreprocessor instance for testing."""
        return TextPreprocessor()
    
    def test_preprocess_basic_email(self, preprocessor: TextPreprocessor) -> None:
        """Test preprocessing a basic email."""
        email = {
            "subject": "Test Subject",
            "body": "This is a test email body.",
            "sender": "test@example.com"
        }
        
        result = preprocessor.preprocess(email)
        
        assert "cleaned_subject" in result
        assert "cleaned_body" in result
        assert "combined_text" in result
        assert "language" in result
        assert "features" in result
        assert result["cleaned_subject"] == "Test Subject"
        assert "test email body" in result["cleaned_body"].lower()
    
    def test_preprocess_empty_email(self, preprocessor: TextPreprocessor) -> None:
        """Test preprocessing an empty email."""
        email = {
            "subject": "",
            "body": "",
            "sender": "test@example.com"
        }
        
        result = preprocessor.preprocess(email)
        
        assert result["cleaned_subject"] == ""
        assert result["cleaned_body"] == ""
        assert result["combined_text"] == ""
        assert result["word_count"] == 0
        assert result["char_count"] == 0
    
    def test_clean_body_removes_excessive_newlines(self, preprocessor: TextPreprocessor) -> None:
        """Test that excessive newlines are removed."""
        body = "Line 1\n\n\n\n\nLine 2"
        result = preprocessor._clean_body(body)
        
        assert "\n\n\n" not in result
        assert "Line 1" in result
        assert "Line 2" in result
    
    def test_clean_body_empty_string(self, preprocessor: TextPreprocessor) -> None:
        """Test cleaning empty body."""
        result = preprocessor._clean_body("")
        assert result == ""
    
    def test_remove_signature_standard_delimiter(self, preprocessor: TextPreprocessor) -> None:
        """Test removing signature with standard delimiter."""
        text = "Email content here.\n--\nJohn Doe\nSoftware Engineer"
        result = preprocessor._remove_signature(text)
        
        assert "Email content here" in result
        assert "John Doe" not in result
        assert "Software Engineer" not in result
    
    def test_remove_signature_best_regards(self, preprocessor: TextPreprocessor) -> None:
        """Test removing signature with 'Best regards'."""
        text = "Email content here.\nBest regards,\nJohn Doe"
        result = preprocessor._remove_signature(text)
        
        assert "Email content here" in result
        assert "John Doe" not in result
    
    def test_remove_signature_mobile(self, preprocessor: TextPreprocessor) -> None:
        """Test removing mobile signature."""
        text = "Email content here.\nSent from my iPhone"
        result = preprocessor._remove_signature(text)
        
        assert "Email content here" in result
        assert "Sent from my iPhone" not in result
    
    def test_remove_signature_no_signature(self, preprocessor: TextPreprocessor) -> None:
        """Test text without signature remains unchanged."""
        text = "Just email content, no signature"
        result = preprocessor._remove_signature(text)
        
        assert result == text
    
    def test_remove_quoted_replies_angle_bracket(self, preprocessor: TextPreprocessor) -> None:
        """Test removing quoted replies with angle brackets."""
        text = "My reply here.\n> Previous email\n> More quoted text"
        result = preprocessor._remove_quoted_replies(text)
        
        assert "My reply here" in result
        assert "Previous email" not in result
        assert "More quoted text" not in result
    
    def test_remove_quoted_replies_on_wrote(self, preprocessor: TextPreprocessor) -> None:
        """Test removing quoted replies with 'On ... wrote:' pattern."""
        text = "My reply.\nOn Jan 1, 2024, John wrote:\nOriginal message"
        result = preprocessor._remove_quoted_replies(text)
        
        assert "My reply" in result
        assert "Original message" not in result
    
    def test_remove_quoted_replies_forwarded_headers(self, preprocessor: TextPreprocessor) -> None:
        """Test removing forwarded email headers."""
        text = "My comment.\nFrom: sender@example.com\nSent: Monday\nOriginal content"
        result = preprocessor._remove_quoted_replies(text)
        
        assert "My comment" in result
        assert "sender@example.com" not in result
    
    def test_remove_disclaimers(self, preprocessor: TextPreprocessor) -> None:
        """Test removing legal disclaimers."""
        text = "Email content.\nThis email and any attachments are confidential."
        result = preprocessor._remove_disclaimers(text)
        
        assert "Email content" in result
        assert "confidential" not in result.lower()
    
    def test_normalize_whitespace_multiple_spaces(self, preprocessor: TextPreprocessor) -> None:
        """Test normalizing multiple spaces."""
        text = "Word1    Word2     Word3"
        result = preprocessor._normalize_whitespace(text)
        
        assert "    " not in result
        assert "Word1 Word2 Word3" == result
    
    def test_normalize_whitespace_multiple_newlines(self, preprocessor: TextPreprocessor) -> None:
        """Test normalizing multiple newlines."""
        text = "Line1\n\n\n\nLine2"
        result = preprocessor._normalize_whitespace(text)
        
        assert "\n\n\n" not in result
        assert "Line1\n\nLine2" == result
    
    def test_clean_subject_removes_re(self, preprocessor: TextPreprocessor) -> None:
        """Test removing 'Re:' from subject."""
        subject = "Re: Original Subject"
        result = preprocessor._clean_subject(subject)
        
        assert result == "Original Subject"
    
    def test_clean_subject_removes_fwd(self, preprocessor: TextPreprocessor) -> None:
        """Test removing 'Fwd:' from subject."""
        subject = "Fwd: Original Subject"
        result = preprocessor._clean_subject(subject)
        
        assert result == "Original Subject"
    
    def test_clean_subject_removes_multiple_re(self, preprocessor: TextPreprocessor) -> None:
        """Test removing multiple 'Re:' prefixes."""
        subject = "Re: Re: Re: Original Subject"
        result = preprocessor._clean_subject(subject)
        
        assert result == "Original Subject"
    
    def test_clean_subject_normalizes_whitespace(self, preprocessor: TextPreprocessor) -> None:
        """Test normalizing whitespace in subject."""
        subject = "Subject   with    extra    spaces"
        result = preprocessor._clean_subject(subject)
        
        assert "   " not in result
        assert result == "Subject with extra spaces"
    
    def test_extract_features_basic(self, preprocessor: TextPreprocessor) -> None:
        """Test basic feature extraction."""
        email = {
            "combined_text": "This is a test email with some content.",
            "sender": "test@example.com",
            "subject": "Test Subject"
        }
        
        features = preprocessor.extract_features(email)
        
        assert "word_count" in features
        assert "char_count" in features
        assert "sender_domain" in features
        assert features["sender_domain"] == "example.com"
        assert features["is_com"] is True
    
    def test_extract_features_edu_domain(self, preprocessor: TextPreprocessor) -> None:
        """Test feature extraction for .edu domain."""
        email = {
            "combined_text": "Academic email",
            "sender": "student@university.edu",
            "subject": "Assignment"
        }
        
        features = preprocessor.extract_features(email)
        
        assert features["is_edu"] is True
        assert features["is_com"] is False
    
    def test_extract_features_urgent_keywords(self, preprocessor: TextPreprocessor) -> None:
        """Test detection of urgent keywords."""
        email = {
            "combined_text": "This is urgent and needs immediate attention ASAP!",
            "sender": "test@example.com",
            "subject": "Urgent"
        }
        
        features = preprocessor.extract_features(email)
        
        assert features["has_urgent_keywords"] is True
    
    def test_extract_features_meeting_keywords(self, preprocessor: TextPreprocessor) -> None:
        """Test detection of meeting keywords."""
        email = {
            "combined_text": "Let's schedule a meeting for tomorrow.",
            "sender": "test@example.com",
            "subject": "Meeting Request"
        }
        
        features = preprocessor.extract_features(email)
        
        assert features["has_meeting_keywords"] is True
    
    def test_extract_features_academic_keywords(self, preprocessor: TextPreprocessor) -> None:
        """Test detection of academic keywords."""
        email = {
            "combined_text": "Your assignment is due next week. Please submit to the professor.",
            "sender": "prof@university.edu",
            "subject": "Assignment Deadline"
        }
        
        features = preprocessor.extract_features(email)
        
        assert features["has_academic_keywords"] is True
    
    def test_extract_features_question_mark(self, preprocessor: TextPreprocessor) -> None:
        """Test detection of question mark in subject."""
        email = {
            "combined_text": "Email body",
            "sender": "test@example.com",
            "subject": "Can you help?"
        }
        
        features = preprocessor.extract_features(email)
        
        assert features["has_question_mark"] is True
    
    def test_extract_features_is_reply(self, preprocessor: TextPreprocessor) -> None:
        """Test detection of reply emails."""
        email = {
            "combined_text": "Email body",
            "sender": "test@example.com",
            "subject": "re: Original Subject"
        }
        
        features = preprocessor.extract_features(email)
        
        assert features["is_reply"] is True
    
    def test_tokenize_for_bert_without_tokenizer(self, preprocessor: TextPreprocessor) -> None:
        """Test BERT tokenization fallback when tokenizer is not available."""
        # Force tokenizer to None
        preprocessor.tokenizer = None
        
        result = preprocessor.tokenize_for_bert("Test text")
        
        assert "input_ids" in result
        assert "attention_mask" in result
        assert result["input_ids"] == []
        assert result["attention_mask"] == []
    
    def test_preprocess_with_all_cleaning_steps(self, preprocessor: TextPreprocessor) -> None:
        """Test preprocessing with all cleaning steps combined."""
        email = {
            "subject": "Re: Fwd: Important Meeting",
            "body": """Hi there,
            
Let's meet tomorrow.


> On Jan 1, John wrote:
> Previous message

Best regards,
John Doe
Sent from my iPhone

This email is confidential.""",
            "sender": "john@company.com"
        }
        
        result = preprocessor.preprocess(email)
        
        # Subject should be cleaned
        assert result["cleaned_subject"] == "Important Meeting"
        
        # Body should have signature and quotes removed
        assert "Let's meet tomorrow" in result["cleaned_body"]
        assert "John Doe" not in result["cleaned_body"]
        assert "Previous message" not in result["cleaned_body"]
        assert "Sent from my iPhone" not in result["cleaned_body"]
        
        # Features should be extracted
        assert "features" in result
        assert result["features"]["has_meeting_keywords"] is True
