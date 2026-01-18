from functools import lru_cache
from src.pipeline import EmailPipeline
from src.database import get_db
from src.cache import get_redis_client
import logging

logger = logging.getLogger(__name__)

# Cache the pipeline instance to avoid reloading models on every request
@lru_cache()
def get_email_pipeline() -> EmailPipeline:
    logger.info("Loading EmailPipeline instance for API...")
    return EmailPipeline()

@lru_cache()
def get_gmail_client():
    from src.integration.gmail_client import GmailClient
    logger.info("Loading GmailClient for API...")
    return GmailClient()

# Database and Cache dependencies are imported from their respective modules
# Usage in routes:
# - db: AsyncSession = Depends(get_db)
# - redis: RedisClient = Depends(get_redis_client)
