# AGENTS.md - Blog Engine Suite Architecture & Conventions

Este documento define las directrices arquitectónicas, técnicas y operativas obligatorias para el proyecto **`blog-engine-suite`**. Cualquier agente o desarrollador que colabore en este repositorio debe respetar estas convenciones sin excepción.

---

## 1. Stack Tecnológico Obligatorio

- **Lenguaje**: Python 3.11+ (con tipado estricto mediante anotaciones de tipo / type hints).
- **Framework Web**: FastAPI (versión >= 0.115).
- **Esquemas y Validación**: Pydantic v2 (`pydantic.BaseModel`, `pydantic-settings.BaseSettings`).
- **ORM / Capa de Datos**: SQLAlchemy 2.0 Async (usando `Mapped`, `mapped_column`, `async_sessionmaker`, `AsyncSession`).
- **Motor de Base de Datos**: **PostgreSQL** exclusivamente.
- **Driver de Conexión**: `asyncpg` (`postgresql+asyncpg://...`).
- **Tipos de Datos Nativos PostgreSQL**:
  - `JSONB` (`sqlalchemy.dialects.postgresql.JSONB`) para estructuras de datos flexibles (secciones de artículos, payloads idempotentes, etc.).
  - `ENUM` nativo (`sqlalchemy.Enum(..., name="...")`) para enumeraciones de dominio.
- **Prohibiciones Terminantes**:
  - **Queda estrictamente prohibido** sustituir PostgreSQL por SQLite, MySQL, MariaDB, MongoDB o cualquier otra base de datos no relacional/embebida.
  - **Queda prohibido** reemplazar `JSONB` por `Text` o `JSON` genérico.

---

## 2. Estructura del Proyecto

El proyecto sigue una arquitectura modularizada por dominios (Domain-Driven modular monolith):

```text
blog-engine-suite/
├── .env
├── .env.example
├── .gitignore
├── AGENTS.md
├── docker-compose.yml
├── requirements.txt
└── app/
    ├── __init__.py
    ├── main.py               # Aplicación FastAPI, lifespan, middleware y /health
    ├── config.py             # Configuración centralizada vía pydantic-settings
    ├── shared/               # Recursos transversales compartidos
    │   ├── __init__.py
    │   └── database.py       # Engine asíncrono, Base declarativa y dependencia get_db
    └── modules/              # Módulos desacoplados de dominio
        ├── __init__.py
        ├── cms/              # Dominio 1: Headless CMS
        │   ├── __init__.py
        │   └── models.py     # Tablas: articulos, idempotency_keys
        ├── generator/        # Dominio 2: Static / SSG Generator & Build System
        │   ├── __init__.py
        │   └── models.py     # Tablas: builds
        └── analytics/        # Dominio 3: Telemetría y analítica de lectura
            ├── __init__.py
            └── models.py     # Tablas: metricas_eventos
```

---

## 3. Módulos y Prefijos de Rutas (APIs REST)

La aplicación integra 3 subsistemas desacoplados dentro del mismo núcleo FastAPI:

1. **CMS API**:
   - Prefijo de ruta: `/api/v1/articulos`
   - Responsabilidad: Gestión de contenidos, ciclo de vida del artículo (borrador -> revisión -> publicado -> archivado), idempotencia de publicación y persistencia de secciones enriquecidas en `JSONB`.

2. **Generator API**:
   - Prefijo de ruta: `/api/v1/generator`
   - Responsabilidad: Orquestación y auditoría de builds estáticos, tracking de hashing de artefactos procesados y métricas de generación.

3. **Analytics API**:
   - Prefijo de ruta: `/api/v1/analytics`
   - Responsabilidad: Ingesta de eventos de telemetría y lectura (page views, scroll depth 50%/100%, copia de código, clicks de enlaces), asociados a artículos vía claves foráneas con eliminación en cascada (`CASCADE`).

---

## 4. Política de Respuestas y Códigos HTTP (400 vs 422)

Para garantizar consistencia en clientes frontend y SDKs:

- **HTTP 422 (Unprocessable Entity)**:
  - Reservado **exclusivamente** para fallos de validación sintáctica de esquemas Pydantic (tipos inválidos, campos requeridos faltantes, strings fuera de rango de longitud, formatos de fecha incorrectos).
  - FastAPI y Pydantic gestionan este código de forma nativa a través de los Request Bodies, Path Parameters y Query Parameters.

- **HTTP 400 (Bad Request)**:
  - Reservado para **violaciones de reglas de negocio y lógica de dominio**:
    - Intentar transicionar un artículo a un estado no permitido en la máquina de estados.
    - Conflicto o rechazo por hash en llaves de idempotencia (`idempotency_keys`).
    - Fechas lógicas incoherentes no detectables por schema simple.
    - Acciones de generación o analítica no válidas para el estado actual de los recursos.

---

## 5. Patrones de Código SQLAlchemy 2.0 Async

1. **Definición de Modelos**:
   - Utilizar la sintaxis declarativa moderna `Mapped[T]` y `mapped_column()`.
   - Incluir siempre `__tablename__`.
   - Especificar nombres explícitos para enums PostgreSQL (`SQLEnum(EnumClass, name="nombre_enum")`).

2. **Manejo de Sesiones**:
   - Inyectar la sesión mediante la dependencia de FastAPI `Depends(get_db)`.
   - Las consultas deben usar la API de sentencias 2.0 (`select(...)`, `insert(...)`, `update(...)`, `delete(...)`).
   - Evitar `session.query(...)` (estilo legacy de SQLAlchemy 1.x).
   - Administrar transacciones de manera limpia; `get_db` maneja el ciclo de vida de la sesión asíncrona.
