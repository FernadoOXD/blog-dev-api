import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class TipoEventoMetrica(str, enum.Enum):
    PAGE_VIEW = "PAGE_VIEW"
    READ_50 = "READ_50"
    READ_100 = "READ_100"
    CODE_COPY = "CODE_COPY"
    LINK_CLICK = "LINK_CLICK"


class MetricaEvento(Base):
    __tablename__ = "metricas_eventos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    articulo_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("articulos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo_evento: Mapped[TipoEventoMetrica] = mapped_column(
        SQLEnum(TipoEventoMetrica, name="tipo_evento_enum"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    duracion_segundos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
