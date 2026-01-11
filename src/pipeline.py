"""
Email Automation Pipeline

Main orchestrator for the email processing workflow.
Integrates Ingestion, ML Pipeline, Generation, and Validation.
"""

import logging
from typing import Dict, Any, Optional

from src.config_loader import config
from src.ingestion.email_parser import EmailParser
from src.ingestion.preprocessor import TextPreprocessor

from nlp.intent_classifier import IntentClassifier
from nlp.urgency_detector import UrgencyDetector
from nlp.sentiment_analyzer import SentimentAnalyzer

from src.generation.orchestrator import GenerationOrchestrator
from src.validation.validator import Validator
from src.validation.safety_filter import SafetyFilter

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EmailPipeline")

class EmailPipeline:
    """End-to-end email processing pipeline."""
    
    def __init__(self):
        logger.info("Initializing Pipeline Components...")
        
        # Ingestion
        self.parser = EmailParser()
        self.preprocessor = TextPreprocessor()
        
        # ML
        self.intent_classifier = IntentClassifier()
        self.urgency_detector = UrgencyDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Generation
        self.generator = GenerationOrchestrator()
        
        # Validation
        self.validator = Validator()
        self.safety = SafetyFilter()
        
        logger.info("Pipeline Initialized.")

    def process_email(self, raw_email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single email through the pipeline.
        
        Args:
            raw_email: Raw email object (from Gmail API or mock)
            
        Returns:
            Processing result with decision and draft
        """
        try:
            # 1. Ingestion: Parse & Preprocess
            parsed_email = self.parser.parse_gmail_message(raw_email) if 'payload' in raw_email else raw_email
            # Handle case where raw_email is already somewhat structured (e.g. from tests)
            # if 'payload' not in raw_email, assume it's a test dict and needs limited parsing
            
            processed_email = self.preprocessor.preprocess(parsed_email)
            logger.info(f"Processing email: {processed_email.get('subject', 'No Subject')}")
            
            # 2. Classification
            intent_res = self.intent_classifier.classify(processed_email)
            urgency_res = self.urgency_detector.detect(processed_email)
            sentiment_res = self.sentiment_analyzer.analyze(processed_email)
            
            classification = {
                "intent": intent_res,
                "urgency": urgency_res,
                "sentiment": sentiment_res
            }
            
            # 3. Decision Logic (Pre-generation)
            # If aggressive or spam, stop here
            if sentiment_res.get("escalate", False) or sentiment_res.get("tone") == "aggressive":
                logger.info("Aggressive email detected. Escalating.")
                return self._build_result(processed_email, classification, action="ESCALATE", reason="Aggressive tone")
                
            if intent_res.get("intent") == "spam":
                logger.info("Spam detected. Ignoring.")
                return self._build_result(processed_email, classification, action="IGNORE", reason="Spam")
            
            # 4. Generation
            draft_res = self.generator.generate_draft(
                processed_email,
                intent=intent_res["intent"],
                urgency=urgency_res["urgency"]
            )
            
            # 5. Validation
            # Safety Check
            safety_res = self.safety.check(draft_res.get("draft", ""))
            if not safety_res["safe"]:
                logger.warning(f"Unsafe draft generated: {safety_res['issues']}")
                return self._build_result(
                    processed_email, classification, draft_res, 
                    action="ESCALATE", reason="Unsafe draft generated"
                )
            
            # Quality/Confidence Check
            validation_res = self.validator.validate(
                draft_res, 
                intent=intent_res["intent"],
                urgency=urgency_res["urgency"],
                sentiment=sentiment_res["sentiment"]
            )
            
            if not validation_res["valid"]:
                logger.info(f"Validation failed: {validation_res['issues']}")
                return self._build_result(
                    processed_email, classification, draft_res, 
                    action="DRAFT_REVIEW", reason="Validation failed (Low confidence/Quality)"
                )
                
            # If all good
            return self._build_result(
                processed_email, classification, draft_res,
                action="DRAFT_REVIEW", # Always review for now, or AUTO_SEND if confident
                reason="Success"
            )
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            return {"error": str(e), "action": "ERROR"}

    def _build_result(
        self, 
        email: Dict[str, Any], 
        classification: Dict[str, Any], 
        draft: Optional[Dict[str, Any]] = None,
        action: str = "DRAFT_REVIEW",
        reason: str = ""
    ) -> Dict[str, Any]:
        """Construct standard result object."""
        return {
            "email_id": email.get("id"),
            "subject": email.get("subject"),
            "classification": classification,
            "draft": draft,
            "action": action,
            "reason": reason,
            "status": "success"
        }

# Example usage
if __name__ == "__main__":
    pipeline = EmailPipeline()
    print("Pipeline Ready.")
