"""Punto de entrada del API (SAD §1 y §8). Prefijo versionado /api/v1 (RNF-COM-02)."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app import health
from app.catalogo.router import router as catalogo_router
from app.config import get_settings
from app.errors import register_error_handlers
from app.middleware import RateLimitMiddleware
from app.pagos.router import router as pagos_router
from app.proveedores.router import router as proveedores_router
from app.recomendador.router import router as recomendador_router
from app.reservas.router import router as reservas_router

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    if settings.seed_on_startup:
        from seed.load import load_seed_if_empty

        load_seed_if_empty()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    # /docs solo fuera de producción (SAD §3, Propuesto); el esquema OpenAPI sigue disponible.
    app = FastAPI(
        title="EventU API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
    )
    app.add_middleware(RateLimitMiddleware, limit_per_minute=settings.rate_limit_per_minute)
    register_error_handlers(app)
    api = APIRouter(prefix=API_PREFIX)
    api.include_router(health.router, tags=["infra"])
    api.include_router(catalogo_router, tags=["catalogo"])
    api.include_router(proveedores_router, tags=["proveedores"])
    api.include_router(recomendador_router, tags=["recomendador"])
    api.include_router(reservas_router, tags=["reservas"])
    api.include_router(pagos_router, tags=["pagos"])
    app.include_router(api)
    return app


app = create_app()
