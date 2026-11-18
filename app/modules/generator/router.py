from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.generator.schemas import (
    ArticuloFeedItem,
    BuildAcceptedResponse,
    BuildRecordResponse,
)
from app.modules.generator.service import (
    get_cached_or_fresh_feed,
    get_published_article_by_slug,
    list_recent_builds,
    run_background_build,
)
from app.shared.database import get_db
from app.shared.security import AuthenticatedUser, require_cms_writer

router = APIRouter()


@router.post(
    "/build",
    response_model=BuildAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Disparar compilación en segundo plano",
)
async def trigger_build(
    background_tasks: BackgroundTasks,
    user: AuthenticatedUser = Depends(require_cms_writer),
) -> BuildAcceptedResponse:
    background_tasks.add_task(run_background_build)
    return BuildAcceptedResponse(
        status="accepted",
        message="Compilación de artículos publicados iniciada en segundo plano",
    )


@router.get(
    "/feed",
    response_model=list[ArticuloFeedItem],
    summary="Feed de artículos publicados",
)
async def get_published_feed(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    items, build_hash = await get_cached_or_fresh_feed(db)
    etag_value = f'"{build_hash}"'

    if_none_match = request.headers.get("if-none-match")
    if if_none_match == etag_value:
        return Response(
            status_code=status.HTTP_304_NOT_MODIFIED,
            headers={
                "ETag": etag_value,
                "Cache-Control": "public, max-age=60",
            },
        )

    return JSONResponse(
        content=items,
        headers={
            "ETag": etag_value,
            "Cache-Control": "public, max-age=60",
        },
    )


@router.get(
    "/render/{slug}",
    response_model=ArticuloFeedItem,
    summary="Renderizar artículo publicado por slug",
)
async def render_article_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    article = await get_published_article_by_slug(db, slug)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artículo publicado no encontrado",
        )

    return JSONResponse(
        content=article,
        headers={"Cache-Control": "public, max-age=60"},
    )


@router.get(
    "/builds",
    response_model=list[BuildRecordResponse],
    summary="Historial de builds recientes",
)
async def get_recent_builds(
    db: AsyncSession = Depends(get_db),
) -> list[BuildRecordResponse]:
    builds = await list_recent_builds(db, limit=10)
    return [BuildRecordResponse.model_validate(b) for b in builds]
