from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.cms.router import router as cms_router
from app.modules.cms.schemas import InvalidNoteTypeError
from app.modules.generator.router import router as generator_router
from app.shared.database import Base, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Importar todos los modelos para registrarlos en Base.metadata
    import app.modules.analytics.models  # noqa: F401
    import app.modules.cms.models  # noqa: F401
    import app.modules.generator.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(
    title="Blog Engine Suite API",
    version="1.0.0",
    description="Headless CMS, Generator & Analytics decoupled REST APIs",
    lifespan=lifespan,
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(InvalidNoteTypeError)
async def invalid_note_type_exception_handler(
    request: Request,
    exc: InvalidNoteTypeError,
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "detail": f"Valor inválido para nota.tipo: '{exc.invalid_value}'. Debe ser 'tip', 'info' o 'warning'."
        },
    )


# Registrar routers
app.include_router(cms_router, prefix="/api/v1/articulos", tags=["CMS"])
app.include_router(generator_router, prefix="/api/v1/generator", tags=["Generator API"])


@app.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
