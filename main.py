"""
Main Entry Point

Runs the AI Email Auto-Responder Pipeline on sample data.
"""

import json
import logging
from src.pipeline import EmailPipeline
from store.shared import pending_drafts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Main")

def main():
    logger.info("Starting AI Email Auto-Responder...")
    
    # Initialize Pipeline
    pipeline = EmailPipeline()
    
    # Load sample data
    try:
        with open("data/sample_emails.json", encoding="utf-8") as f:
            emails = json.load(f)
    except FileNotFoundError:
        logger.error("Sample data not found in data/sample_emails.json")
        return

    logger.info(f"Loaded {len(emails)} sample emails.")
    
    # Process emails
    for email in emails:
        logger.info(f"Processing email ID: {email.get('id', 'unknown')}")
        
        result = pipeline.process_email(email)
        
        print("\n==============================")
        print(f"Email: {result.get('subject')}")
        print(f"Action: {result.get('action')}")
        print(f"Reason: {result.get('reason')}")
        
        classification = result.get("classification", {})
        if classification:
            print(f"Intent: {classification.get('intent', {}).get('intent')}")
            print(f"Urgency: {classification.get('urgency', {}).get('urgency')}")
        
        draft = result.get("draft")
        if draft and result.get("action") in ["DRAFT_REVIEW", "AUTO_SEND"]:
            print(f"\nGenerated Draft:\n{draft.get('draft')[:200]}...") # Print preview
            
            # Store in pending drafts
            pending_drafts[str(email["id"])] = {
                "draft": draft.get("draft"),
                "email": email,
                "metadata": result
            }
            
    # Save drafts
    with open("data/pending_drafts.json", "w", encoding="utf-8") as f:
        json.dump(pending_drafts, f, indent=2, ensure_ascii=False)
    logger.info("Drafts saved to data/pending_drafts.json")

if __name__ == "__main__":
    main()
