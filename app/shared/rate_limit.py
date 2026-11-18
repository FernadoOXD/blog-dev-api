import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException

from app.shared.security import AuthenticatedUser, require_cms_writer

RATE_LIMIT_WINDOW_SECONDS = 60.0
RATE_LIMIT_MAX_REQUESTS = 30

_user_request_timestamps: dict[str, deque[float]] = defaultdict(deque)


async def enforce_rate_limit(
    user: AuthenticatedUser = Depends(require_cms_writer),
) -> AuthenticatedUser:
    now = time.time()
    user_timestamps = _user_request_timestamps[user.user_id]

    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    while user_timestamps and user_timestamps[0] <= cutoff:
        user_timestamps.popleft()

    if len(user_timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Límite de tráfico excedido (máximo 30 peticiones/minuto)",
            headers={"Retry-After": "60"},
        )

    user_timestamps.append(now)
    return user
