import enum
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum as SQLEnum, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class EstadoArticulo(str, enum.Enum):
    BORRADOR = "BORRADOR"
    EN_REVISION = "EN_REVISION"
    PUBLICADO = "PUBLICADO"
    ARCHIVADO = "ARCHIVADO"


class Articulo(Base):
    __tablename__ = "articulos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    resumen: Mapped[str] = mapped_column(String(300), nullable=False)
    fecha: Mapped[str] = mapped_column(String(10), nullable=False)  # Formato YYYY-MM-DD
    etiqueta: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    tiempo_lectura: Mapped[str] = mapped_column(String(20), nullable=False)
    imagen_cabecera: Mapped[str | None] = mapped_column(String(255), nullable=True)
    estado: Mapped[EstadoArticulo] = mapped_column(
        SQLEnum(EstadoArticulo, name="estado_articulo_enum"),
        nullable=False,
        default=EstadoArticulo.BORRADOR,
        index=True,
    )
    secciones: Mapped[list[dict[str, Any]] | dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_body: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
