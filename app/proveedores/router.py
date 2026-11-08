"""Rutas del módulo proveedores. Cada HU añade aquí sus endpoints (ver docs/ y CLAUDE.md)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.proveedores.detail_schemas import ProviderDetailResponse
from app.proveedores.detail_service import get_provider_detail
from app.proveedores.schemas import ProviderCategory, ProviderListResponse, ProviderSort
from app.proveedores.service import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, get_providers
from app.shared.db import get_session

router = APIRouter()


@router.get("/providers/{provider_id}", response_model=ProviderDetailResponse)
def provider_detail(
    provider_id: str,
    db: Annotated[Session, Depends(get_session)],
) -> ProviderDetailResponse:
    return get_provider_detail(db, provider_id)


@router.get("/providers", response_model=ProviderListResponse)
def list_providers(
    db: Annotated[Session, Depends(get_session)],
    guests: Annotated[int | None, Query(ge=1, le=500)] = None,
    event_type: Annotated[Literal["cumpleanos", "boda", "xv"] | None, Query()] = None,
    category: Annotated[ProviderCategory | None, Query()] = None,
    min_price_cop: Annotated[int | None, Query(ge=0)] = None,
    max_price_cop: Annotated[int | None, Query(ge=0)] = None,
    min_rating: Annotated[float | None, Query(ge=3, le=4.5)] = None,
    verified: bool | None = None,
    sort: ProviderSort = "recomendados",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> ProviderListResponse:
    return get_providers(
        db,
        guests,
        event_type,
        category,
        min_price_cop,
        max_price_cop,
        min_rating,
        verified,
        sort,
        page,
        page_size,
    )
