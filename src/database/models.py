"""
Database Models for Email Auto-Responder

SQLAlchemy ORM models for storing emails, classifications, drafts, and metadata.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Email(Base):
    """Core email data model."""
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    gmail_message_id = Column(String(255), unique=True, nullable=True, index=True)
    sender = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    classification = relationship("Classification", back_populates="email", uselist=False, cascade="all, delete-orphan")
    draft = relationship("Draft", back_populates="email", uselist=False, cascade="all, delete-orphan")
    metadata = relationship("ProcessingMetadata", back_populates="email", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Email(id={self.id}, sender='{self.sender}', subject='{self.subject[:30]}...')>"


class Classification(Base):
    """Email classification results (intent, urgency, sentiment)."""
    __tablename__ = "classifications"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Intent classification
    intent = Column(String(50), nullable=False, index=True)
    intent_confidence = Column(Float, nullable=False)
    intent_method = Column(String(50), nullable=True)
    intent_scores = Column(JSON, nullable=True)  # Store all intent scores
    
    # Urgency detection
    urgency = Column(String(50), nullable=False, index=True)
    urgency_confidence = Column(Float, nullable=False)
    urgency_reasoning = Column(Text, nullable=True)
    
    # Sentiment analysis
    sentiment = Column(String(50), nullable=False)
    sentiment_confidence = Column(Float, nullable=False)
    sentiment_tone = Column(String(50), nullable=True)
    sentiment_escalate = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationship
    email = relationship("Email", back_populates="classification")
    
    def __repr__(self):
        return f"<Classification(email_id={self.email_id}, intent='{self.intent}', urgency='{self.urgency}')>"


class Draft(Base):
    """Generated draft responses."""
    __tablename__ = "drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    draft_text = Column(Text, nullable=False)
    method = Column(String(50), nullable=True)  # e.g., "template", "llm", "hybrid"
    confidence = Column(Float, nullable=True)
    template_used = Column(String(100), nullable=True)
    word_count = Column(Integer, nullable=True)
    
    # Draft status
    status = Column(String(50), default="pending", index=True)  # pending, approved, sent, ignored
    approved_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship
    email = relationship("Email", back_populates="draft")
    
    def __repr__(self):
        return f"<Draft(email_id={self.email_id}, status='{self.status}', word_count={self.word_count})>"


class ProcessingMetadata(Base):
    """Processing metadata and pipeline status."""
    __tablename__ = "processing_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    action = Column(String(100), nullable=True)  # e.g., "DRAFT_REVIEW", "AUTO_SEND", "IGNORE"
    status = Column(String(50), nullable=False, index=True)  # success, error, pending
    reason = Column(Text, nullable=True)
    
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship
    email = relationship("Email", back_populates="metadata")
    
    def __repr__(self):
        return f"<ProcessingMetadata(email_id={self.email_id}, status='{self.status}', action='{self.action}')>"
