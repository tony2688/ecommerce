import logging
from typing import Optional
import redis

from app.core.settings import settings

logger = logging.getLogger(__name__)

_client: Optional[redis.Redis] = None


def _get_client() -> Optional[redis.Redis]:
    global _client
    if _client is None:
        try:
            _client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        except Exception as e:
            logger.warning("counter_client_init_failed", extra={"error": str(e)})
            _client = None
    return _client


def inc_counter(name: str, value: int = 1) -> None:
    c = _get_client()
    if not c:
        return
    try:
        c.incrby(f"metrics:{name}", value)
    except Exception as e:
        logger.warning("counter_incr_failed", extra={"name": name, "error": str(e)})