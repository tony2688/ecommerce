import logging
import httpx

from app.core.settings import settings

logger = logging.getLogger(__name__)


def verify_credentials(timeout: float = 5.0) -> bool:
    token = settings.MP_ACCESS_TOKEN
    if not token or len(token) < 10:
        logger.warning("mp_credentials_missing", extra={"env": settings.MP_ENV})
        return False
    url = "https://api.mercadopago.com/users/me"
    try:
        r = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=timeout)
        ok = r.status_code == 200
        if ok:
            try:
                from app.observability.counters import inc_counter
                inc_counter("mp.credentials.ok")
            except Exception:
                pass
        else:
            logger.warning("mp_credentials_invalid", extra={"status": r.status_code, "env": settings.MP_ENV})
        return ok
    except Exception as e:
        logger.warning("mp_credentials_check_failed", extra={"error": str(e), "env": settings.MP_ENV})
        return False