from functools import lru_cache
from src.pipeline import EmailPipeline
import logging

logger = logging.getLogger(__name__)

# Cache the pipeline instance to avoid reloading models on every request
@lru_cache()
def get_email_pipeline() -> EmailPipeline:
    logger.info("Loading EmailPipeline instance for API...")
    return EmailPipeline()
