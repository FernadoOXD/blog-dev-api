from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.cms.schemas import SeccionArticuloSchema


class ArticuloFeedItem(BaseModel):
    id: int
    slug: str
    titulo: str
    resumen: str
    fecha: str
    etiqueta: str
    tiempoLectura: str
    imagenCabecera: str | None = None
    secciones: list[SeccionArticuloSchema]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BuildAcceptedResponse(BaseModel):
    status: str = "accepted"
    message: str


class BuildRecordResponse(BaseModel):
    id: int
    build_hash: str
    articulos_procesados: int
    duracion_ms: int
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)
