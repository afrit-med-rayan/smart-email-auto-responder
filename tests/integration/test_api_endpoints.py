"""
Integration tests for FastAPI endpoints.

Tests API endpoints using FastAPI TestClient with mocked dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.api.main import app


@pytest.fixture
def mock_db_health() -> AsyncMock:
    """Mock database health check."""
    return AsyncMock(return_value=True)


@pytest.fixture
def mock_email_pipeline() -> Mock:
    """Mock EmailPipeline for testing."""
    pipeline = Mock()
    
    # Mock preprocessor
    pipeline.preprocessor.preprocess.return_value = {
        "combined_text": "test email",
        "cleaned_subject": "test",
        "cleaned_body": "test email body"
    }
    
    # Mock classifiers
    pipeline.intent_classifier.classify.return_value = {
        "intent": "academic",
        "confidence": 0.85
    }
    pipeline.urgency_detector.detect.return_value = {
        "urgency": "high",
        "confidence": 0.80
    }
    pipeline.sentiment_analyzer.analyze.return_value = {
        "sentiment": "neutral",
        "confidence": 0.75
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


@pytest.fixture
def mock_redis_client() -> Mock:
    """Mock Redis client for testing."""
    return Mock()


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Mock database session for testing."""
    return AsyncMock()


@pytest.fixture
def client() -> TestClient:
    """Create test client for FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test /health endpoint."""
    
    @patch("src.api.main.check_db_health")
    def test_health_check_success(
        self, 
        mock_check_db: AsyncMock,
        client: TestClient
    ) -> None:
        """Test health check with healthy database."""
        mock_check_db.return_value = True
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "email-responder"
        assert data["database"] == "connected"
    
    @patch("src.api.main.check_db_health")
    def test_health_check_degraded(
        self,
        mock_check_db: AsyncMock,
        client: TestClient
    ) -> None:
        """Test health check with unhealthy database."""
        mock_check_db.return_value = False
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "disconnected"


class TestClassifyEndpoint:
    """Test /api/v1/classify endpoint."""
    
    @patch("src.api.routes.get_api_key")
    @patch("src.api.routes.get_email_pipeline")
    @patch("src.api.routes.get_db")
    @patch("src.api.routes.get_redis_client")
    def test_classify_email_success(
        self,
        mock_get_redis: Mock,
        mock_get_db: Mock,
        mock_get_pipeline: Mock,
        mock_get_api_key: Mock,
        mock_email_pipeline: Mock,
        mock_redis_client: Mock,
        mock_db_session: AsyncMock,
        client: TestClient
    ) -> None:
        """Test successful email classification."""
        # Setup mocks
        mock_get_api_key.return_value = "test_key"
        mock_get_pipeline.return_value = mock_email_pipeline
        mock_get_db.return_value = mock_db_session
        mock_get_redis.return_value = mock_redis_client
        
        # Make request
        response = client.post(
            "/api/v1/classify",
            json={
                "subject": "Assignment Question",
                "body": "I have a question about the homework.",
                "sender": "student@university.edu",
                "message_id": "test123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "academic"
        assert data["urgency"] == "high"
        assert data["sentiment"] == "neutral"
        assert "confidence" in data
        assert isinstance(data["confidence"], float)
    
    @patch("src.api.routes.get_api_key")
    @patch("src.api.routes.get_email_pipeline")
    @patch("src.api.routes.get_db")
    @patch("src.api.routes.get_redis_client")
    def test_classify_email_missing_fields(
        self,
        mock_get_redis: Mock,
        mock_get_db: Mock,
        mock_get_pipeline: Mock,
        mock_get_api_key: Mock,
        client: TestClient
    ) -> None:
        """Test classification with missing required fields."""
        mock_get_api_key.return_value = "test_key"
        
        response = client.post(
            "/api/v1/classify",
            json={
                "subject": "Test"
                # Missing body and sender
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestGenerateEndpoint:
    """Test /api/v1/generate endpoint."""
    
    @patch("src.api.routes.get_api_key")
    @patch("src.api.routes.get_email_pipeline")
    def test_generate_draft_success(
        self,
        mock_get_pipeline: Mock,
        mock_get_api_key: Mock,
        mock_email_pipeline: Mock,
        client: TestClient
    ) -> None:
        """Test successful draft generation."""
        mock_get_api_key.return_value = "test_key"
        mock_get_pipeline.return_value = mock_email_pipeline
        
        response = client.post(
            "/api/v1/generate",
            json={
                "email_body": "Can we schedule a meeting?",
                "sender_name": "John Doe",
                "intent": "meeting",
                "context": {"subject": "Meeting Request"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "draft" in data
        assert isinstance(data["draft"], str)
        assert len(data["draft"]) > 0
    
    @patch("src.api.routes.get_api_key")
    @patch("src.api.routes.get_email_pipeline")
    def test_generate_draft_without_context(
        self,
        mock_get_pipeline: Mock,
        mock_get_api_key: Mock,
        mock_email_pipeline: Mock,
        client: TestClient
    ) -> None:
        """Test draft generation without context."""
        mock_get_api_key.return_value = "test_key"
        mock_get_pipeline.return_value = mock_email_pipeline
        
        response = client.post(
            "/api/v1/generate",
            json={
                "email_body": "Thank you for your help.",
                "sender_name": "Jane Smith",
                "intent": "support"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "draft" in data


class TestValidateEndpoint:
    """Test /api/v1/validate endpoint."""
    
    @patch("src.api.routes.get_api_key")
    @patch("src.api.routes.get_email_pipeline")
    def test_validate_draft_safe(
        self,
        mock_get_pipeline: Mock,
        mock_get_api_key: Mock,
        mock_email_pipeline: Mock,
        client: TestClient
    ) -> None:
        """Test validation of safe draft."""
        mock_get_api_key.return_value = "test_key"
        mock_get_pipeline.return_value = mock_email_pipeline
        
        response = client.post(
            "/api/v1/validate",
            json={
                "draft": "Thank you for your email. I will get back to you soon."
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["score"] > 0
        assert isinstance(data["issues"], list)
    
    @patch("src.api.routes.get_api_key")
    @patch("src.api.routes.get_email_pipeline")
    def test_validate_draft_unsafe(
        self,
        mock_get_pipeline: Mock,
        mock_get_api_key: Mock,
        mock_email_pipeline: Mock,
        client: TestClient
    ) -> None:
        """Test validation of unsafe draft."""
        mock_get_api_key.return_value = "test_key"
        
        # Mock unsafe response
        mock_email_pipeline.safety.check.return_value = {
            "safe": False,
            "issues": ["Contains inappropriate content"]
        }
        mock_get_pipeline.return_value = mock_email_pipeline
        
        response = client.post(
            "/api/v1/validate",
            json={
                "draft": "This draft contains problematic content."
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert data["score"] == 0.0
        assert len(data["issues"]) > 0


class TestAuthenticationAndAuthorization:
    """Test API authentication and authorization."""
    
    def test_missing_api_key(self, client: TestClient) -> None:
        """Test request without API key is rejected."""
        # This test depends on how authentication is implemented
        # If API key is required, requests without it should fail
        pass  # Implement based on actual auth mechanism
    
    def test_invalid_api_key(self, client: TestClient) -> None:
        """Test request with invalid API key is rejected."""
        # This test depends on how authentication is implemented
        pass  # Implement based on actual auth mechanism


class TestErrorHandling:
    """Test error handling in API endpoints."""
    
    @patch("src.api.routes.get_api_key")
    @patch("src.api.routes.get_email_pipeline")
    @patch("src.api.routes.get_db")
    @patch("src.api.routes.get_redis_client")
    def test_classify_with_pipeline_error(
        self,
        mock_get_redis: Mock,
        mock_get_db: Mock,
        mock_get_pipeline: Mock,
        mock_get_api_key: Mock,
        mock_email_pipeline: Mock,
        client: TestClient
    ) -> None:
        """Test handling of pipeline errors during classification."""
        mock_get_api_key.return_value = "test_key"
        
        # Make pipeline raise an exception
        mock_email_pipeline.preprocessor.preprocess.side_effect = Exception("Pipeline error")
        mock_get_pipeline.return_value = mock_email_pipeline
        
        response = client.post(
            "/api/v1/classify",
            json={
                "subject": "Test",
                "body": "Test body",
                "sender": "test@example.com"
            }
        )
        
        # Should handle error gracefully
        assert response.status_code in [500, 422]  # Depends on error handling implementation
