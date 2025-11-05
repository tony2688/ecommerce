import redis
from app.core.settings import settings

r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
)
def too_many_attempts(client_id: str, limit: int = 5, window_sec: int = 900) -> bool:
    # Disable rate limiting outside production to avoid flakiness in dev/tests
    if settings.APP_ENV != "production":
        return False
    # Generic namespacing; caller provides a meaningful key (e.g., "login:<ip>" or "cart_items:<ip>")
    key = f"rl:{client_id}"
    hits = r.incr(key)
    if hits == 1:
        r.expire(key, window_sec)
    return hits > limit