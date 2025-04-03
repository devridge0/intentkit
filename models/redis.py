"""Redis client module for IntentKit."""

import logging
from typing import Optional

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[Redis] = None


async def init_redis(
    host: str,
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None,
    ssl: bool = False,
    encoding: str = "utf-8",
    decode_responses: bool = True,
) -> Redis:
    """Initialize the Redis client.

    Args:
        host: Redis host
        port: Redis port (default: 6379)
        db: Redis database number (default: 0)
        password: Redis password (default: None)
        ssl: Whether to use SSL (default: False)
        encoding: Response encoding (default: utf-8)
        decode_responses: Whether to decode responses (default: True)

    Returns:
        Redis: The initialized Redis client
    """
    global _redis_client

    if _redis_client is not None:
        logger.info("Redis client already initialized")
        return _redis_client

    try:
        logger.info(f"Initializing Redis client at {host}:{port}")
        _redis_client = Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            ssl=ssl,
            encoding=encoding,
            decode_responses=decode_responses,
        )
        # Test the connection
        await _redis_client.ping()
        logger.info("Redis client initialized successfully")
        return _redis_client
    except Exception as e:
        logger.error(f"Failed to initialize Redis client: {e}")
        raise


def get_redis() -> Redis:
    """Get the Redis client.

    Returns:
        Redis: The Redis client

    Raises:
        RuntimeError: If the Redis client is not initialized
    """
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis first.")
    return _redis_client
