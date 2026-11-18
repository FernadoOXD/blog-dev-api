import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cms.models import IdempotencyKey


def calculate_request_hash(payload: Any) -> str:
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


async def check_idempotency(
    db: AsyncSession,
    key: str | None,
    user_id: str,
    request_hash: str,
) -> JSONResponse | None:
    if not key or not key.strip():
        raise HTTPException(
            status_code=400,
            detail="La cabecera Idempotency-Key es obligatoria",
        )

    clean_key = key.strip()
    stmt = select(IdempotencyKey).where(IdempotencyKey.key == clean_key)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if record:
        record_created_at = record.created_at
        if record_created_at.tzinfo is None:
            record_created_at = record_created_at.replace(tzinfo=timezone.utc)

        now_utc = datetime.now(timezone.utc)
        if record_created_at >= now_utc - timedelta(hours=24):
            if record.request_hash == request_hash:
                return JSONResponse(
                    status_code=record.response_status,
                    content=record.response_body,
                )
            raise HTTPException(
                status_code=409,
                detail="Idempotency-Key ya utilizada con un payload diferente",
            )
        # Expirado (> 24 horas): eliminar para permitir reuso
        await db.delete(record)
        await db.commit()

    return None


async def save_idempotency(
    db: AsyncSession,
    key: str,
    user_id: str,
    request_hash: str,
    status_code: int,
    body: dict[str, Any],
) -> None:
    record = IdempotencyKey(
        key=key.strip(),
        user_id=user_id,
        request_hash=request_hash,
        response_status=status_code,
        response_body=body,
    )
    db.add(record)
    await db.commit()
