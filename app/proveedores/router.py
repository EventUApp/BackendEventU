"""Rutas del módulo proveedores. Cada HU añade aquí sus endpoints (ver docs/ y CLAUDE.md)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.proveedores.schemas import ProviderListResponse
from app.proveedores.service import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, get_providers
from app.shared.db import get_session

router = APIRouter()


@router.get("/providers", response_model=ProviderListResponse)
def list_providers(
    db: Annotated[Session, Depends(get_session)],
    guests: Annotated[int | None, Query(ge=1, le=500)] = None,
    event_type: Annotated[Literal["cumpleanos", "boda", "xv"] | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> ProviderListResponse:
    return get_providers(db, guests, event_type, page, page_size)
