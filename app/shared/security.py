import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import settings

security = HTTPBearer(auto_error=True)


class AuthenticatedUser(BaseModel):
    user_id: str
    role: str
    scopes: list[str]


async def require_cms_writer(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthenticatedUser:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado",
        )

    user_id = payload.get("sub")
    role = payload.get("role")
    scopes = payload.get("scopes", [])

    if not user_id or not role or not isinstance(scopes, list):
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado",
        )

    if role not in {"EDITOR", "ADMIN"} or "blog:write" not in scopes:
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes: se requiere rol EDITOR o ADMIN con alcance blog:write",
        )

    return AuthenticatedUser(user_id=str(user_id), role=str(role), scopes=scopes)
