import asyncio
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cms.models import EstadoArticulo
from app.modules.cms.schemas import (
    ArticuloCreatedResponse,
    ArticuloCreateRequest,
    ArticuloDetailResponse,
    ArticuloUpdateRequest,
)
from app.modules.cms.service import (
    actualizar_articulo,
    archivar_articulo,
    crear_articulo,
    listar_articulos,
    obtener_articulo,
)
from app.shared.database import get_db
from app.shared.idempotency import (
    calculate_request_hash,
    check_idempotency,
    save_idempotency,
)
from app.shared.rate_limit import enforce_rate_limit
from app.shared.security import AuthenticatedUser

router = APIRouter()


@router.post(
    "",
    response_model=ArticuloCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo artículo",
)
async def crear_nuevo_articulo(
    payload: ArticuloCreateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: AuthenticatedUser = Depends(enforce_rate_limit),
    db: AsyncSession = Depends(get_db),
) -> Response:
    request_hash = calculate_request_hash(payload.model_dump(mode="json"))

    cached_response = await check_idempotency(
        db=db,
        key=idempotency_key,
        user_id=user.user_id,
        request_hash=request_hash,
    )
    if cached_response is not None:
        return cached_response

    assert idempotency_key is not None

    async def _operacion() -> dict[str, Any]:
        articulo = await crear_articulo(db, payload)
        data = ArticuloCreatedResponse.model_validate(articulo).model_dump(mode="json")
        await save_idempotency(
            db=db,
            key=idempotency_key,
            user_id=user.user_id,
            request_hash=request_hash,
            status_code=status.HTTP_201_CREATED,
            body=data,
        )
        return data

    try:
        resultado = await asyncio.wait_for(_operacion(), timeout=3.0)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Tiempo máximo de ejecución síncrona excedido (3s)",
        )

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=resultado)


@router.get(
    "",
    response_model=list[ArticuloDetailResponse],
    summary="Listar artículos",
)
async def listar_todos_los_articulos(
    estado: EstadoArticulo | None = Query(None, description="Filtrar por estado del artículo"),
    user: AuthenticatedUser = Depends(enforce_rate_limit),
    db: AsyncSession = Depends(get_db),
) -> list[ArticuloDetailResponse]:
    articulos = await listar_articulos(db, estado=estado)
    return [ArticuloDetailResponse.model_validate(art) for art in articulos]


@router.get(
    "/{articulo_id}",
    response_model=ArticuloDetailResponse,
    summary="Obtener detalle de un artículo por ID",
)
async def obtener_detalle_articulo(
    articulo_id: int,
    user: AuthenticatedUser = Depends(enforce_rate_limit),
    db: AsyncSession = Depends(get_db),
) -> ArticuloDetailResponse:
    articulo = await obtener_articulo(db, articulo_id)
    if not articulo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artículo no encontrado",
        )
    return ArticuloDetailResponse.model_validate(articulo)


@router.put(
    "/{articulo_id}",
    response_model=ArticuloDetailResponse,
    summary="Actualizar un artículo existente",
)
async def actualizar_articulo_existente(
    articulo_id: int,
    payload: ArticuloUpdateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: AuthenticatedUser = Depends(enforce_rate_limit),
    db: AsyncSession = Depends(get_db),
) -> Response:
    articulo = await obtener_articulo(db, articulo_id)
    if not articulo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artículo no encontrado",
        )

    request_hash = calculate_request_hash({
        "articulo_id": articulo_id,
        **payload.model_dump(mode="json"),
    })

    cached_response = await check_idempotency(
        db=db,
        key=idempotency_key,
        user_id=user.user_id,
        request_hash=request_hash,
    )
    if cached_response is not None:
        return cached_response

    assert idempotency_key is not None

    async def _operacion() -> dict[str, Any]:
        actualizado = await actualizar_articulo(db, articulo, payload)
        data = ArticuloDetailResponse.model_validate(actualizado).model_dump(mode="json")
        await save_idempotency(
            db=db,
            key=idempotency_key,
            user_id=user.user_id,
            request_hash=request_hash,
            status_code=status.HTTP_200_OK,
            body=data,
        )
        return data

    try:
        resultado = await asyncio.wait_for(_operacion(), timeout=3.0)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Tiempo máximo de ejecución síncrona excedido (3s)",
        )

    return JSONResponse(status_code=status.HTTP_200_OK, content=resultado)


@router.delete(
    "/{articulo_id}",
    response_model=ArticuloDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Archivado lógico de un artículo",
)
async def archivar_articulo_por_id(
    articulo_id: int,
    user: AuthenticatedUser = Depends(enforce_rate_limit),
    db: AsyncSession = Depends(get_db),
) -> ArticuloDetailResponse:
    articulo = await obtener_articulo(db, articulo_id)
    if not articulo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artículo no encontrado",
        )

    archivado = await archivar_articulo(db, articulo)
    return ArticuloDetailResponse.model_validate(archivado)
