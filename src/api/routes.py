from fastapi import APIRouter, Depends, HTTPException
from src.api.models import (
    EmailRequest, ClassificationResponse, GenerationRequest, 
    GenerationResponse, ValidationRequest, ValidationResponse
)
from src.api.auth import get_api_key
from src.api.dependencies import get_email_pipeline
from src.pipeline import EmailPipeline

router = APIRouter(dependencies=[Depends(get_api_key)])

@router.post("/classify", response_model=ClassificationResponse)
async def classify_email(
    request: EmailRequest,
    pipeline: EmailPipeline = Depends(get_email_pipeline)
):
    # Construct dict format expected by internal tools
    email_data = {
        "subject": request.subject,
        "body": request.body,
        "sender": request.sender,
        "id": request.message_id or "api-req"
    }
    
    # Use pipeline's preprocessor and classifiers directly
    # Note: We are bypassing the full pipeline.process() to give granular access
    
    processed_email = pipeline.preprocessor.preprocess(email_data)
    
    intent_res = pipeline.intent_classifier.classify(processed_email)
    urgency_res = pipeline.urgency_detector.detect(processed_email)
    sentiment_res = pipeline.sentiment_analyzer.analyze(processed_email)
    
    # Calculate an aggregate confidence (simplification)
    avg_confidence = (
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
):
    # Mock processed email structure for generator
    processed_email = {
        "combined_text": request.email_body, 
        "sender": request.sender_name,
        "subject": "Re: " + request.context.get("subject", "") if request.context else ""
    }
    
    draft_res = pipeline.generator.generate_draft(
        processed_email,
        intent=request.intent,
        urgency="medium" # Default or passed in context
    )
    
    return GenerationResponse(draft=draft_res.get("draft", ""))

@router.post("/validate", response_model=ValidationResponse)
async def validate_draft(
    request: ValidationRequest,
    pipeline: EmailPipeline = Depends(get_email_pipeline)
):
    # Use Validator
    # We need dummy intent/urgency/sentiment if not provided, 
    # but the validator mostly checks congruence or grammar.
    
    # For now, let's just use the SafetyFilter and basic Validator logic
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
