from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.models import (
    EmailRequest, EmailResponse, ClassificationResponse, GenerationRequest, 
    GenerationResponse, ValidationRequest, ValidationResponse
)
from src.api.auth import get_api_key
from src.api.dependencies import get_email_pipeline, get_gmail_client
from src.api import crud
from src.database import get_db
from src.cache import get_redis_client, RedisClient
from src.pipeline import EmailPipeline
from src.integration.gmail_client import GmailClient
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter(dependencies=[Depends(get_api_key)])

@router.get("/emails", response_model=List[EmailResponse])
async def list_emails(
    skip: int = 0,
    limit: int = 100,
    intent: Optional[str] = None,
    urgency: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> List[EmailResponse]:
    """
    List emails with optional filtering and pagination.
    
    Query params:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (default: 100)
    - intent: Filter by classification intent
    - urgency: Filter by classification urgency
    - status: Filter by draft status
    """
    # Fetch emails from database
    emails = await crud.list_emails(
        db,
        skip=skip,
        limit=limit,
        intent_filter=intent,
        urgency_filter=urgency,
        status_filter=status,
    )
    
    # Transform to response format
    response_list: List[EmailResponse] = []
    for email in emails:
        classification_data: Optional[Dict[str, Any]] = None
        if email.classification:
            classification_data = {
                "intent": email.classification.intent,
                "urgency": email.classification.urgency,
                "sentiment": email.classification.sentiment,
                "confidence": (
                    email.classification.intent_confidence +
                    email.classification.urgency_confidence +
                    email.classification.sentiment_confidence
                ) / 3.0
            }
        
        draft_text = email.draft.draft_text if email.draft else None
        
        response_list.append(EmailResponse(
            id=email.id,
            subject=email.subject,
            sender=email.sender,
            body=email.body,
            classification=classification_data,
            generatedDraft=draft_text,
        ))
    
    return response_list

@router.post("/classify", response_model=ClassificationResponse)
async def classify_email(
    request: EmailRequest,
    pipeline: EmailPipeline = Depends(get_email_pipeline),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> ClassificationResponse:
    """
    Classify an email and optionally cache the result.
    """
    # Construct dict format expected by internal tools
    email_data: Dict[str, Any] = {
        "subject": request.subject,
        "body": request.body,
        "sender": request.sender,
        "id": request.message_id or "api-req"
    }
    
    # Use pipeline's preprocessor and classifiers directly
    processed_email = pipeline.preprocessor.preprocess(email_data)
    
    intent_res = pipeline.intent_classifier.classify(processed_email)
    urgency_res = pipeline.urgency_detector.detect(processed_email)
    sentiment_res = pipeline.sentiment_analyzer.analyze(processed_email)
    
    # Calculate an aggregate confidence
    avg_confidence: float = (
        intent_res.get("confidence", 0) + 
        urgency_res.get("confidence", 0) + 
        sentiment_res.get("confidence", 0)
    ) / 3.0
    
    return ClassificationResponse(
        intent=intent_res.get("intent", "unknown"),
        urgency=urgency_res.get("urgency", "medium"),
        sentiment=sentiment_res.get("sentiment", "neutral"),
        confidence=avg_confidence
    )

@router.post("/generate", response_model=GenerationResponse)
async def generate_draft(
    request: GenerationRequest,
    pipeline: EmailPipeline = Depends(get_email_pipeline)
) -> GenerationResponse:
    """Generate a draft response for an email."""
    # Mock processed email structure for generator
    processed_email: Dict[str, Any] = {
        "combined_text": request.email_body, 
        "sender": request.sender_name,
        "subject": "Re: " + request.context.get("subject", "") if request.context else ""
    }
    
    draft_res = pipeline.generator.generate_draft(
        processed_email,
        intent=request.intent,
        urgency="medium"  # Default or passed in context
    )
    
    return GenerationResponse(draft=draft_res.get("draft", ""))

@router.post("/validate", response_model=ValidationResponse)
async def validate_draft(
    request: ValidationRequest,
    pipeline: EmailPipeline = Depends(get_email_pipeline)
) -> ValidationResponse:
    """Validate a draft response."""
    # Use Validator - SafetyFilter and basic Validator logic
    safety_res = pipeline.safety.check(request.draft)
    
    if not safety_res["safe"]:
         return ValidationResponse(
             is_valid=False,
             score=0.0,
             issues=safety_res["issues"]
         )
         
    # We'd invoke full validator here, but it requires full context (intent etc.)
    # For this endpoint, we'll assume basic grammar/safety check if context missing
    
    return ValidationResponse(
        is_valid=True,
        score=1.0, 
        issues=[]
    )
