import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Permitir ejecución directa del script agregando el root al PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import jwt
from app.config import settings


def generate_token(
    user_id: str = "fernando-253428",
    role: str = "ADMIN",
    scopes: list[str] | None = None,
    expires_in_hours: int = 24,
) -> str:
    if scopes is None:
        scopes = ["blog:write"]

    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "scopes": scopes,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=expires_in_hours)).timestamp()),
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


def main() -> None:
    parser = argparse.ArgumentParser(description="Generador de tokens JWT para Blog Engine Suite")
    parser.add_argument("--user-id", default="fernando-253428", help="ID del usuario (sub)")
    parser.add_argument("--role", default="ADMIN", choices=["ADMIN", "EDITOR"], help="Rol del usuario")
    parser.add_argument("--scopes", nargs="+", default=["blog:write"], help="Scopes/alcances del token")
    parser.add_argument("--hours", type=int, default=24, help="Horas de validez del token")

    args = parser.parse_args()

    token = generate_token(
        user_id=args.user_id,
        role=args.role,
        scopes=args.scopes,
        expires_in_hours=args.hours,
    )

    print("\n" + "=" * 60)
    print("  BLOG ENGINE SUITE - TOKEN JWT DE PRUEBA")
    print("=" * 60)
    print(f"User ID:  {args.user_id}")
    print(f"Role:     {args.role}")
    print(f"Scopes:   {args.scopes}")
    print(f"Validez:  {args.hours} horas")
    print("-" * 60)
    print(f"Bearer Token:\n{token}")
    print("-" * 60)
    print(f"Header de autorización para Postman / cURL:\nAuthorization: Bearer {token}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
