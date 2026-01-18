"""
Redis Caching Client

Provides caching utilities for email classifications, drafts, and metadata.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from redis import Redis
from redis.exceptions import RedisError, ConnectionError

logger = logging.getLogger(__name__)

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class RedisClient:
    """Redis client wrapper for caching email processing results."""
    
    def __init__(self, url: str = REDIS_URL):
        """
        Initialize Redis client.
        
        Args:
            url: Redis connection URL
        """
        self.url = url
        self.client: Optional[Redis] = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Redis."""
        try:
            self.client = Redis.from_url(
                self.url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            self.client.ping()
            logger.info("Redis connection established successfully.")
        except (RedisError, ConnectionError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except (RedisError, ConnectionError):
            return False
    
    def _serialize(self, data: Any) -> str:
        """Serialize data to JSON string."""
        return json.dumps(data)
    
    def _deserialize(self, data: str) -> Any:
        """Deserialize JSON string to data."""
        return json.loads(data)
    
    # Classification Caching (TTL: 1 hour)
    
    def cache_classification(self, email_id: int, classification: Dict[str, Any], ttl: int = 3600):
        """
        Cache email classification results.
        
        Args:
            email_id: Email ID
            classification: Classification data
            ttl: Time to live in seconds (default: 1 hour)
        """
        if not self.is_connected():
            logger.warning("Redis not connected, skipping cache.")
            return
        
        try:
            key = f"classification:email_{email_id}"
            self.client.setex(key, ttl, self._serialize(classification))
            logger.debug(f"Cached classification for email {email_id}")
        except RedisError as e:
            logger.error(f"Failed to cache classification: {e}")
    
    def get_classification(self, email_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached classification.
        
        Args:
            email_id: Email ID
            
        Returns:
            Classification data or None if not found
        """
        if not self.is_connected():
            return None
        
        try:
            key = f"classification:email_{email_id}"
            data = self.client.get(key)
            if data:
                logger.debug(f"Cache hit for classification email {email_id}")
                return self._deserialize(data)
            logger.debug(f"Cache miss for classification email {email_id}")
            return None
        except RedisError as e:
            logger.error(f"Failed to get classification from cache: {e}")
            return None
    
    # Draft Caching (TTL: 24 hours)
    
    def cache_draft(self, email_id: int, draft: Dict[str, Any], ttl: int = 86400):
        """
        Cache generated draft.
        
        Args:
            email_id: Email ID
            draft: Draft data
            ttl: Time to live in seconds (default: 24 hours)
        """
        if not self.is_connected():
            logger.warning("Redis not connected, skipping cache.")
            return
        
        try:
            key = f"draft:email_{email_id}"
            self.client.setex(key, ttl, self._serialize(draft))
            logger.debug(f"Cached draft for email {email_id}")
        except RedisError as e:
            logger.error(f"Failed to cache draft: {e}")
    
    def get_draft(self, email_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached draft.
        
        Args:
            email_id: Email ID
            
        Returns:
            Draft data or None if not found
        """
        if not self.is_connected():
            return None
        
        try:
            key = f"draft:email_{email_id}"
            data = self.client.get(key)
            if data:
                logger.debug(f"Cache hit for draft email {email_id}")
                return self._deserialize(data)
            logger.debug(f"Cache miss for draft email {email_id}")
            return None
        except RedisError as e:
            logger.error(f"Failed to get draft from cache: {e}")
            return None
    
    # Email Metadata Caching (TTL: 30 minutes)
    
    def cache_email_metadata(self, email_id: int, metadata: Dict[str, Any], ttl: int = 1800):
        """
        Cache email metadata.
        
        Args:
            email_id: Email ID
            metadata: Metadata
            ttl: Time to live in seconds (default: 30 minutes)
        """
        if not self.is_connected():
            logger.warning("Redis not connected, skipping cache.")
            return
        
        try:
            key = f"metadata:email_{email_id}"
            self.client.setex(key, ttl, self._serialize(metadata))
            logger.debug(f"Cached metadata for email {email_id}")
        except RedisError as e:
            logger.error(f"Failed to cache metadata: {e}")
    
    def get_email_metadata(self, email_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached email metadata.
        
        Args:
            email_id: Email ID
            
        Returns:
            Metadata or None if not found
        """
        if not self.is_connected():
            return None
        
        try:
            key = f"metadata:email_{email_id}"
            data = self.client.get(key)
            if data:
                logger.debug(f"Cache hit for metadata email {email_id}")
                return self._deserialize(data)
            logger.debug(f"Cache miss for metadata email {email_id}")
            return None
        except RedisError as e:
            logger.error(f"Failed to get metadata from cache: {e}")
            return None
    
    # Cache Invalidation
    
    def invalidate_email_cache(self, email_id: int):
        """
        Invalidate all cache entries for an email.
        
        Args:
            email_id: Email ID
        """
        if not self.is_connected():
            return
        
        try:
            keys = [
                f"classification:email_{email_id}",
                f"draft:email_{email_id}",
                f"metadata:email_{email_id}",
            ]
            self.client.delete(*keys)
            logger.debug(f"Invalidated cache for email {email_id}")
        except RedisError as e:
            logger.error(f"Failed to invalidate cache: {e}")
    
    def clear_all_cache(self):
        """
        Clear all cache entries.
        
        WARNING: This will delete all data in the Redis database!
        """
        if not self.is_connected():
            return
        
        try:
            self.client.flushdb()
            logger.warning("Cleared all Redis cache.")
        except RedisError as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def close(self):
        """Close Redis connection."""
        if self.client:
            self.client.close()
            logger.info("Redis connection closed.")


# Global Redis client instance
redis_client = RedisClient()


def get_redis_client() -> RedisClient:
    """
    Dependency for FastAPI to get Redis client.
    
    Usage:
        @app.get("/items")
        async def read_items(redis: RedisClient = Depends(get_redis_client)):
            ...
    """
    return redis_client
