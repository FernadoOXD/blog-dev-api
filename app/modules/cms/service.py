from fastapi import HTTPException
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cms.models import Articulo, EstadoArticulo
from app.modules.cms.schemas import ArticuloCreateRequest, ArticuloUpdateRequest

TRANSICIONES_VALIDAS: dict[EstadoArticulo, set[EstadoArticulo]] = {
    EstadoArticulo.BORRADOR: {
        EstadoArticulo.BORRADOR,
        EstadoArticulo.EN_REVISION,
        EstadoArticulo.PUBLICADO,
    },
    EstadoArticulo.EN_REVISION: {
        EstadoArticulo.EN_REVISION,
        EstadoArticulo.BORRADOR,
        EstadoArticulo.PUBLICADO,
    },
    EstadoArticulo.PUBLICADO: {
        EstadoArticulo.PUBLICADO,
        EstadoArticulo.ARCHIVADO,
    },
    EstadoArticulo.ARCHIVADO: {
        EstadoArticulo.ARCHIVADO,
    },
}


def validar_transicion_estado(
    estado_actual: EstadoArticulo,
    nuevo_estado: EstadoArticulo,
) -> None:
    destinos_permitidos = TRANSICIONES_VALIDAS.get(estado_actual, set())
    if nuevo_estado not in destinos_permitidos:
        raise HTTPException(
            status_code=400,
            detail="Transición de estado no permitida",
        )


async def generar_slug_unico(
    db: AsyncSession,
    titulo: str,
    articulo_id_actual: int | None = None,
) -> str:
    base_slug = slugify(titulo)
    if not base_slug:
        base_slug = "articulo"

    slug = base_slug
    contador = 2
    while True:
        stmt = select(Articulo.id).where(Articulo.slug == slug)
        if articulo_id_actual is not None:
            stmt = stmt.where(Articulo.id != articulo_id_actual)

        result = await db.execute(stmt)
        if result.scalar_one_or_none() is None:
            return slug

        slug = f"{base_slug}-{contador}"
        contador += 1


async def crear_articulo(
    db: AsyncSession,
    payload: ArticuloCreateRequest,
) -> Articulo:
    slug = await generar_slug_unico(db, payload.titulo)
    secciones_serializadas = [
        s.model_dump(exclude_none=True) for s in payload.secciones
    ]

    articulo = Articulo(
        slug=slug,
        titulo=payload.titulo,
        resumen=payload.resumen,
        fecha=payload.fecha,
        etiqueta=payload.etiqueta,
        tiempo_lectura=payload.tiempoLectura,
        imagen_cabecera=payload.imagenCabecera,
        estado=EstadoArticulo.BORRADOR,
        secciones=secciones_serializadas,
    )

    db.add(articulo)
    await db.commit()
    await db.refresh(articulo)
    return articulo


async def obtener_articulo(
    db: AsyncSession,
    articulo_id: int,
) -> Articulo | None:
    stmt = select(Articulo).where(Articulo.id == articulo_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def listar_articulos(
    db: AsyncSession,
    estado: EstadoArticulo | None = None,
) -> list[Articulo]:
    stmt = select(Articulo).order_by(Articulo.created_at.desc())
    if estado is not None:
        stmt = stmt.where(Articulo.estado == estado)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def actualizar_articulo(
    db: AsyncSession,
    articulo: Articulo,
    payload: ArticuloUpdateRequest,
) -> Articulo:
    if payload.estado is not None:
        validar_transicion_estado(articulo.estado, payload.estado)
        articulo.estado = payload.estado

    if payload.titulo is not None:
        articulo.titulo = payload.titulo

    if payload.resumen is not None:
        articulo.resumen = payload.resumen

    if payload.fecha is not None:
        articulo.fecha = payload.fecha

    if payload.etiqueta is not None:
        articulo.etiqueta = payload.etiqueta

    if payload.tiempoLectura is not None:
        articulo.tiempo_lectura = payload.tiempoLectura

    if payload.imagenCabecera is not None:
        articulo.imagen_cabecera = payload.imagenCabecera

    if payload.secciones is not None:
        articulo.secciones = [
            s.model_dump(exclude_none=True) for s in payload.secciones
        ]

    await db.commit()
    await db.refresh(articulo)
    return articulo


async def archivar_articulo(
    db: AsyncSession,
    articulo: Articulo,
) -> Articulo:
    validar_transicion_estado(articulo.estado, EstadoArticulo.ARCHIVADO)
    articulo.estado = EstadoArticulo.ARCHIVADO
    await db.commit()
    await db.refresh(articulo)
    return articulo
