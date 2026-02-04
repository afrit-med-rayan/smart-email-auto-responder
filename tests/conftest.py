"""
Pytest configuration and shared fixtures for testing.
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator, Dict, Any
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_email() -> Dict[str, Any]:
    """Sample email data for testing."""
    return {
        "id": "test123",
        "subject": "Test Email Subject",
        "body": "This is a test email body with some content.",
        "sender": "test@example.com",
        "recipient": "user@example.com",
        "timestamp": "2024-01-01T12:00:00Z"
    }


@pytest.fixture
def sample_academic_email() -> Dict[str, Any]:
    """Sample academic email for testing."""
    return {
        "id": "academic123",
        "subject": "Assignment Question",
        "body": "I have a question about the homework assignment due next week.",
        "sender": "student@university.edu",
        "recipient": "professor@university.edu",
        "timestamp": "2024-01-01T12:00:00Z"
    }


@pytest.fixture
def sample_meeting_email() -> Dict[str, Any]:
    """Sample meeting request email for testing."""
    return {
        "id": "meeting123",
        "subject": "Meeting Request",
        "body": "Can we schedule a meeting for tomorrow to discuss the project?",
        "sender": "colleague@company.com",
        "recipient": "user@company.com",
        "timestamp": "2024-01-01T12:00:00Z"
    }


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Mock database session for testing."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_redis_client() -> Mock:
    """Mock Redis client for testing."""
    client = Mock()
    client.get = Mock(return_value=None)
    client.set = Mock(return_value=True)
    client.delete = Mock(return_value=True)
    client.exists = Mock(return_value=False)
    return client


@pytest.fixture
def mock_email_pipeline() -> Mock:
    """Mock EmailPipeline for testing."""
    pipeline = Mock()
    
    # Mock preprocessor
    pipeline.preprocessor.preprocess.return_value = {
        "combined_text": "test email",
        "cleaned_subject": "test",
        "cleaned_body": "test email body",
        "features": {}
    }
    
    # Mock classifiers
    pipeline.intent_classifier.classify.return_value = {
        "intent": "academic",
        "confidence": 0.85
    }
    pipeline.urgency_detector.detect.return_value = {
        "urgency": "medium",
        "confidence": 0.75
    }
    pipeline.sentiment_analyzer.analyze.return_value = {
        "sentiment": "neutral",
        "confidence": 0.80
    }
    
    # Mock generator
    pipeline.generator.generate_draft.return_value = {
        "draft": "This is a generated response."
    }
    
    # Mock safety filter
    pipeline.safety.check.return_value = {
        "safe": True,
        "issues": []
    }
    
    return pipeline

