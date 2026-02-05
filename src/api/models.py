from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class EmailRequest(BaseModel):
    subject: str
    body: str
    sender: str
    message_id: Optional[str] = None

class ClassificationResponse(BaseModel):
    intent: str
    urgency: str
    sentiment: str
    confidence: float

class EmailResponse(BaseModel):
    id: int  # Changed from str to int to match database ID
    subject: str
    sender: str
    body: str
    classification: Optional[Dict[str, Any]] = None
    generatedDraft: Optional[str] = None

class GenerationRequest(BaseModel):
    intent: str
    sender_name: Optional[str] = "Sender"
    email_body: str
    context: Optional[Dict[str, Any]] = None

class GenerationResponse(BaseModel):
    draft: str

class ValidationRequest(BaseModel):
    draft: str

class ValidationResponse(BaseModel):
    is_valid: bool
    score: float
    issues: List[str]
