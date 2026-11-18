from datetime import datetime
from typing import Any

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.modules.cms.models import EstadoArticulo


class InvalidNoteTypeError(Exception):
    """Excepción lanzada cuando una nota tiene un tipo no permitido.

    Hereda de Exception directamente para evitar que Pydantic v2
    lo transforme en un ValidationError (422).
    """

    def __init__(self, invalid_value: Any) -> None:
        self.invalid_value = invalid_value
        super().__init__(f"Tipo de nota inválido: '{invalid_value}'")


class BloqueCodigoSchema(BaseModel):
    lenguaje: str = Field(..., min_length=1)
    codigo: str = Field(..., min_length=1)


class ImagenSeccionSchema(BaseModel):
    src: str | None = None
    alt: str = Field(..., min_length=1)
    pieDeFoto: str | None = None


class NotaSeccionSchema(BaseModel):
    tipo: str
    texto: str = Field(..., min_length=1)

    @field_validator("tipo")
    @classmethod
    def validar_tipo(cls, v: str) -> str:
        if v not in ("tip", "info", "warning"):
            raise InvalidNoteTypeError(v)
        return v


class SeccionArticuloSchema(BaseModel):
    subtitulo: str | None = None
    parrafos: list[str] | None = None
    codigo: BloqueCodigoSchema | None = None
    codigoSecundario: BloqueCodigoSchema | None = None
    imagen: ImagenSeccionSchema | None = None
    puntosClave: list[str] | None = None
    nota: NotaSeccionSchema | None = None


class ArticuloCreateRequest(BaseModel):
    titulo: str = Field(..., min_length=5, max_length=150)
    resumen: str = Field(..., min_length=10, max_length=300)
    fecha: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    etiqueta: str = Field(..., min_length=1, max_length=50, pattern=r"^\S+$")
    tiempoLectura: str = Field(..., pattern=r"^\d+\smin$")
    imagenCabecera: str | None = None
    secciones: list[SeccionArticuloSchema] = Field(..., min_length=1)


class ArticuloUpdateRequest(BaseModel):
    titulo: str | None = Field(None, min_length=5, max_length=150)
    resumen: str | None = Field(None, min_length=10, max_length=300)
    fecha: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    etiqueta: str | None = Field(None, min_length=1, max_length=50, pattern=r"^\S+$")
    tiempoLectura: str | None = Field(None, pattern=r"^\d+\smin$")
    imagenCabecera: str | None = None
    estado: EstadoArticulo | None = None
    secciones: list[SeccionArticuloSchema] | None = Field(None, min_length=1)


class ArticuloCreatedResponse(BaseModel):
    id: int
    titulo: str
    fecha: str
    secciones: list[SeccionArticuloSchema]

    model_config = ConfigDict(from_attributes=True)


class ArticuloDetailResponse(BaseModel):
    id: int
    slug: str
    titulo: str
    resumen: str
    fecha: str
    etiqueta: str
    tiempoLectura: str = Field(
        ...,
        validation_alias=AliasChoices("tiempoLectura", "tiempo_lectura"),
        serialization_alias="tiempoLectura",
    )
    imagenCabecera: str | None = Field(
        None,
        validation_alias=AliasChoices("imagenCabecera", "imagen_cabecera"),
        serialization_alias="imagenCabecera",
    )
    estado: EstadoArticulo
    secciones: list[SeccionArticuloSchema]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
