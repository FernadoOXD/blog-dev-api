import hashlib
import json
from pathlib import Path
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cms.models import Articulo, EstadoArticulo
from app.modules.generator.models import Build
from app.shared.database import AsyncSessionLocal

CACHE_DIR = Path("cache")
FEED_CACHE_FILE = CACHE_DIR / "feed.json"


def _serialize_article(art: Articulo) -> dict[str, Any]:
    return {
        "id": art.id,
        "slug": art.slug,
        "titulo": art.titulo,
        "resumen": art.resumen,
        "fecha": art.fecha,
        "etiqueta": art.etiqueta,
        "tiempoLectura": art.tiempo_lectura,
        "imagenCabecera": art.imagen_cabecera,
        "secciones": art.secciones,
    }


async def compile_published_feed(db: AsyncSession) -> tuple[list[dict[str, Any]], str]:
    start = time.perf_counter()

    stmt = (
        select(Articulo)
        .where(Articulo.estado == EstadoArticulo.PUBLICADO)
        .order_by(Articulo.fecha.desc(), Articulo.id.desc())
    )
    result = await db.execute(stmt)
    articulos = result.scalars().all()

    items = [_serialize_article(art) for art in articulos]
    serialized_json = json.dumps(items, ensure_ascii=False, sort_keys=True)
    build_hash = hashlib.sha256(serialized_json.encode("utf-8")).hexdigest()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_payload = {
        "build_hash": build_hash,
        "items": items,
    }
    FEED_CACHE_FILE.write_text(
        json.dumps(cache_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    duracion_ms = max(1, int((time.perf_counter() - start) * 1000))

    build_record = Build(
        build_hash=build_hash,
        articulos_procesados=len(items),
        duracion_ms=duracion_ms,
    )
    db.add(build_record)
    await db.commit()

    return (items, build_hash)


async def run_background_build() -> None:
    async with AsyncSessionLocal() as db:
        await compile_published_feed(db)


async def get_cached_or_fresh_feed(db: AsyncSession) -> tuple[list[dict[str, Any]], str]:
    if FEED_CACHE_FILE.exists():
        try:
            data = json.loads(FEED_CACHE_FILE.read_text(encoding="utf-8"))
            if "items" in data and "build_hash" in data:
                return (data["items"], data["build_hash"])
        except Exception:
            pass
    return await compile_published_feed(db)


async def get_published_article_by_slug(
    db: AsyncSession,
    slug: str,
) -> dict[str, Any] | None:
    stmt = (
        select(Articulo)
        .where(Articulo.slug == slug)
        .where(Articulo.estado == EstadoArticulo.PUBLICADO)
    )
    result = await db.execute(stmt)
    art = result.scalar_one_or_none()
    if not art:
        return None
    return _serialize_article(art)


async def list_recent_builds(
    db: AsyncSession,
    limit: int = 10,
) -> list[Build]:
    stmt = select(Build).order_by(Build.id.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
