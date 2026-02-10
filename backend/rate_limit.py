"""
Rate limiting configuration.
Shared limiter instance used by main.py and routers.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_rate_limit_key(request):
    """Get rate limit key - prefer user ID over IP for authenticated requests."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            from jose import jwt
            from config import settings
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=get_rate_limit_key)
