"""
CRUD Operations for Email Auto-Responder

Database operations for creating, reading, updating, and deleting emails and related data.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import Email, Classification, Draft, ProcessingMetadata


# ============================================================================
# Email CRUD Operations
# ============================================================================

async def create_email(
    db: AsyncSession,
    sender: str,
    subject: str,
    body: str,
    timestamp: datetime,
    gmail_message_id: Optional[str] = None,
) -> Email:
    """Create a new email record."""
    email = Email(
        sender=sender,
        subject=subject,
        body=body,
        timestamp=timestamp,
        gmail_message_id=gmail_message_id,
    )
    db.add(email)
    await db.flush()
    await db.refresh(email)
    return email


async def get_email_by_id(db: AsyncSession, email_id: int) -> Optional[Email]:
    """Get email by ID with all relationships loaded."""
    stmt = (
        select(Email)
        .options(
            selectinload(Email.classification),
            selectinload(Email.draft),
            selectinload(Email.metadata),
        )
        .where(Email.id == email_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_email_by_gmail_id(db: AsyncSession, gmail_message_id: str) -> Optional[Email]:
    """Get email by Gmail message ID."""
    stmt = select(Email).where(Email.gmail_message_id == gmail_message_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_emails(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    intent_filter: Optional[str] = None,
    urgency_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> List[Email]:
    """
    List emails with optional filtering and pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        intent_filter: Filter by classification intent
        urgency_filter: Filter by classification urgency
        status_filter: Filter by draft status
    """
    stmt = (
        select(Email)
        .options(
            selectinload(Email.classification),
            selectinload(Email.draft),
            selectinload(Email.metadata),
        )
        .order_by(desc(Email.timestamp))
    )
    
    # Apply filters
    if intent_filter:
        stmt = stmt.join(Email.classification).where(Classification.intent == intent_filter)
    if urgency_filter:
        stmt = stmt.join(Email.classification).where(Classification.urgency == urgency_filter)
    if status_filter:
        stmt = stmt.join(Email.draft).where(Draft.status == status_filter)
    
    stmt = stmt.offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ============================================================================
# Classification CRUD Operations
# ============================================================================

async def create_classification(
    db: AsyncSession,
    email_id: int,
    intent: str,
    intent_confidence: float,
    urgency: str,
    urgency_confidence: float,
    sentiment: str,
    sentiment_confidence: float,
    intent_method: Optional[str] = None,
    intent_scores: Optional[Dict[str, float]] = None,
    urgency_reasoning: Optional[str] = None,
    sentiment_tone: Optional[str] = None,
    sentiment_escalate: bool = False,
) -> Classification:
    """Create a new classification record."""
    classification = Classification(
        email_id=email_id,
        intent=intent,
        intent_confidence=intent_confidence,
        intent_method=intent_method,
        intent_scores=intent_scores,
        urgency=urgency,
        urgency_confidence=urgency_confidence,
        urgency_reasoning=urgency_reasoning,
        sentiment=sentiment,
        sentiment_confidence=sentiment_confidence,
        sentiment_tone=sentiment_tone,
        sentiment_escalate=sentiment_escalate,
    )
    db.add(classification)
    await db.flush()
    await db.refresh(classification)
    return classification


async def get_classification_by_email_id(db: AsyncSession, email_id: int) -> Optional[Classification]:
    """Get classification by email ID."""
    stmt = select(Classification).where(Classification.email_id == email_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ============================================================================
# Draft CRUD Operations
# ============================================================================

async def create_draft(
    db: AsyncSession,
    email_id: int,
    draft_text: str,
    method: Optional[str] = None,
    confidence: Optional[float] = None,
    template_used: Optional[str] = None,
    word_count: Optional[int] = None,
    status: str = "pending",
) -> Draft:
    """Create a new draft record."""
    draft = Draft(
        email_id=email_id,
        draft_text=draft_text,
        method=method,
        confidence=confidence,
        template_used=template_used,
        word_count=word_count,
        status=status,
    )
    db.add(draft)
    await db.flush()
    await db.refresh(draft)
    return draft


async def get_draft_by_email_id(db: AsyncSession, email_id: int) -> Optional[Draft]:
    """Get draft by email ID."""
    stmt = select(Draft).where(Draft.email_id == email_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_draft_status(
    db: AsyncSession,
    email_id: int,
    status: str,
    approved_at: Optional[datetime] = None,
    sent_at: Optional[datetime] = None,
) -> Optional[Draft]:
    """Update draft status."""
    draft = await get_draft_by_email_id(db, email_id)
    if draft:
        draft.status = status
        if approved_at:
            draft.approved_at = approved_at
        if sent_at:
            draft.sent_at = sent_at
        await db.flush()
        await db.refresh(draft)
    return draft


async def list_drafts_by_status(db: AsyncSession, status: str, limit: int = 100) -> List[Draft]:
    """List drafts by status."""
    stmt = (
        select(Draft)
        .where(Draft.status == status)
        .order_by(desc(Draft.created_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ============================================================================
# Processing Metadata CRUD Operations
# ============================================================================

async def create_processing_metadata(
    db: AsyncSession,
    email_id: int,
    action: Optional[str] = None,
    status: str = "pending",
    reason: Optional[str] = None,
    processing_started_at: Optional[datetime] = None,
    processing_completed_at: Optional[datetime] = None,
) -> ProcessingMetadata:
    """Create a new processing metadata record."""
    metadata = ProcessingMetadata(
        email_id=email_id,
        action=action,
        status=status,
        reason=reason,
        processing_started_at=processing_started_at,
        processing_completed_at=processing_completed_at,
    )
    db.add(metadata)
    await db.flush()
    await db.refresh(metadata)
    return metadata


async def get_metadata_by_email_id(db: AsyncSession, email_id: int) -> Optional[ProcessingMetadata]:
    """Get processing metadata by email ID."""
    stmt = select(ProcessingMetadata).where(ProcessingMetadata.email_id == email_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_processing_metadata(
    db: AsyncSession,
    email_id: int,
    action: Optional[str] = None,
    status: Optional[str] = None,
    reason: Optional[str] = None,
    processing_completed_at: Optional[datetime] = None,
) -> Optional[ProcessingMetadata]:
    """Update processing metadata."""
    metadata = await get_metadata_by_email_id(db, email_id)
    if metadata:
        if action is not None:
            metadata.action = action
        if status is not None:
            metadata.status = status
        if reason is not None:
            metadata.reason = reason
        if processing_completed_at is not None:
            metadata.processing_completed_at = processing_completed_at
        await db.flush()
        await db.refresh(metadata)
    return metadata


# ============================================================================
# Composite Operations
# ============================================================================

async def create_email_with_full_data(
    db: AsyncSession,
    email_data: Dict[str, Any],
    classification_data: Dict[str, Any],
    draft_data: Dict[str, Any],
    metadata_data: Dict[str, Any],
) -> Email:
    """
    Create email with all related data in a single transaction.
    
    This is useful for migrating data from JSON or processing new emails.
    """
    # Create email
    email = await create_email(
        db,
        sender=email_data["sender"],
        subject=email_data["subject"],
        body=email_data["body"],
        timestamp=email_data["timestamp"],
        gmail_message_id=email_data.get("gmail_message_id"),
    )
    
    # Create classification
    await create_classification(
        db,
        email_id=email.id,
        **classification_data,
    )
    
    # Create draft
    await create_draft(
        db,
        email_id=email.id,
        **draft_data,
    )
    
    # Create metadata
    await create_processing_metadata(
        db,
        email_id=email.id,
        **metadata_data,
    )
    
    await db.flush()
    
    # Reload with all relationships
    return await get_email_by_id(db, email.id)
