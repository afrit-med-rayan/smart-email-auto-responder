"""
Migrate JSON Data to PostgreSQL

This script migrates existing email data from JSON files to the PostgreSQL database.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import init_db, AsyncSessionLocal
from src.api.crud import create_email_with_full_data


async def migrate_pending_drafts():
    """Migrate data from data/pending_drafts.json to database."""
    
    json_path = project_root / "data" / "pending_drafts.json"
    
    if not json_path.exists():
        print(f"❌ File not found: {json_path}")
        return 0
    
    print(f"📂 Reading {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"📊 Found {len(data)} email records to migrate")
    
    migrated_count = 0
    async with AsyncSessionLocal() as db:
        for email_id_str, record in data.items():
            try:
                email_info = record.get("email", {})
                metadata_info = record.get("metadata", {})
                classification_info = metadata_info.get("classification", {})
                draft_info = metadata_info.get("draft", {})
                
                # Parse timestamp
                timestamp_str = email_info.get("timestamp", "")
                try:
                    # Try ISO format first
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except:
                    # Fallback to simple format
                    try:
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
                    except:
                        timestamp = datetime.now()
                
                # Prepare email data
                email_data = {
                    "sender": email_info.get("sender", "unknown@example.com"),
                    "subject": email_info.get("subject", "No Subject"),
                    "body": email_info.get("body", ""),
                    "timestamp": timestamp,
                    "gmail_message_id": None,  # JSON doesn't have Gmail IDs
                }
                
                # Prepare classification data
                intent_data = classification_info.get("intent", {})
                urgency_data = classification_info.get("urgency", {})
                sentiment_data = classification_info.get("sentiment", {})
                
                classification_data = {
                    "intent": intent_data.get("intent", "general"),
                    "intent_confidence": intent_data.get("confidence", 0.5),
                    "intent_method": intent_data.get("method", "unknown"),
                    "intent_scores": intent_data.get("scores", {}),
                    "urgency": urgency_data.get("urgency", "medium"),
                    "urgency_confidence": urgency_data.get("confidence", 0.5),
                    "urgency_reasoning": urgency_data.get("reasoning", ""),
                    "sentiment": sentiment_data.get("sentiment", "neutral"),
                    "sentiment_confidence": sentiment_data.get("confidence", 0.5),
                    "sentiment_tone": sentiment_data.get("tone", "neutral"),
                    "sentiment_escalate": sentiment_data.get("escalate", False),
                }
                
                # Prepare draft data
                draft_data = {
                    "draft_text": record.get("draft", "") or draft_info.get("draft", ""),
                    "method": draft_info.get("method", "template"),
                    "confidence": draft_info.get("confidence", 0.9),
                    "template_used": draft_info.get("template_used", ""),
                    "word_count": draft_info.get("word_count", 0),
                    "status": "pending",
                }
                
                # Prepare metadata
                metadata_data = {
                    "action": metadata_info.get("action", "DRAFT_REVIEW"),
                    "status": metadata_info.get("status", "success"),
                    "reason": metadata_info.get("reason", ""),
                }
                
                # Create email with all related data
                await create_email_with_full_data(
                    db,
                    email_data=email_data,
                    classification_data=classification_data,
                    draft_data=draft_data,
                    metadata_data=metadata_data,
                )
                
                migrated_count += 1
                print(f"✅ Migrated email {migrated_count}/{len(data)}: {email_data['subject'][:50]}")
                
            except Exception as e:
                print(f"❌ Failed to migrate record {email_id_str}: {e}")
                continue
        
        # Commit all changes
        await db.commit()
    
    print(f"\n✨ Migration complete! Migrated {migrated_count}/{len(data)} emails")
    return migrated_count


async def migrate_sample_emails():
    """Migrate data from data/sample_emails.json to database."""
    
    json_path = project_root / "data" / "sample_emails.json"
    
    if not json_path.exists():
        print(f"❌ File not found: {json_path}")
        return 0
    
    print(f"📂 Reading {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"📊 Found {len(data)} sample email records")
    
    migrated_count = 0
    async with AsyncSessionLocal() as db:
        for record in data:
            try:
                # Parse timestamp
                timestamp_str = record.get("timestamp", "")
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except:
                    try:
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
                    except:
                        timestamp = datetime.now()
                
                # Prepare email data
                email_data = {
                    "sender": record.get("sender", "unknown@example.com"),
                    "subject": record.get("subject", "No Subject"),
                    "body": record.get("body", ""),
                    "timestamp": timestamp,
                    "gmail_message_id": None,
                }
                
                # Create minimal classification (will be processed later)
                classification_data = {
                    "intent": "general",
                    "intent_confidence": 0.5,
                    "urgency": "medium",
                    "urgency_confidence": 0.5,
                    "sentiment": "neutral",
                    "sentiment_confidence": 0.5,
                }
                
                # Create empty draft
                draft_data = {
                    "draft_text": "",
                    "status": "pending",
                }
                
                # Create metadata
                metadata_data = {
                    "action": "PENDING_CLASSIFICATION",
                    "status": "pending",
                    "reason": "Migrated from sample_emails.json",
                }
                
                # Create email with all related data
                await create_email_with_full_data(
                    db,
                    email_data=email_data,
                    classification_data=classification_data,
                    draft_data=draft_data,
                    metadata_data=metadata_data,
                )
                
                migrated_count += 1
                print(f"✅ Migrated sample email {migrated_count}/{len(data)}: {email_data['subject'][:50]}")
                
            except Exception as e:
                print(f"❌ Failed to migrate sample email: {e}")
                continue
        
        # Commit all changes
        await db.commit()
    
    print(f"\n✨ Sample emails migration complete! Migrated {migrated_count}/{len(data)} emails")
    return migrated_count


async def main():
    """Main migration function."""
    print("=" * 60)
    print("📦 Email Auto-Responder: JSON to PostgreSQL Migration")
    print("=" * 60)
    
    # Initialize database (create tables if they don't exist)
    print("\n🔧 Initializing database...")
    await init_db()
    print("✅ Database initialized")
    
    # Migrate pending drafts
    print("\n" + "=" * 60)
    print("📧 Migrating pending_drafts.json...")
    print("=" * 60)
    drafts_count = await migrate_pending_drafts()
    
    # Migrate sample emails
    print("\n" + "=" * 60)
    print("📧 Migrating sample_emails.json...")
    print("=" * 60)
    samples_count = await migrate_sample_emails()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 MIGRATION SUMMARY")
    print("=" * 60)
    print(f"✅ Pending drafts migrated: {drafts_count}")
    print(f"✅ Sample emails migrated: {samples_count}")
    print(f"✅ Total emails migrated: {drafts_count + samples_count}")
    print("\n🎉 Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
