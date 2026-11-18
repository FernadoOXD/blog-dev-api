from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class Build(Base):
    __tablename__ = "builds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    build_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    articulos_procesados: Mapped[int] = mapped_column(Integer, nullable=False)
    duracion_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
