"""Esquemas de la lista de proveedores."""

from pydantic import BaseModel


class ProviderListItem(BaseModel):
    id: str
    name: str
    categories: list[str]
    neighborhood: str
    municipality: str
    latitude: float | None
    longitude: float | None
    cover_url: str | None
    rating_avg: float | None
    rating_count: int
    verification_status: str
    price_from_cop: int
    featured: bool


class ProviderListResponse(BaseModel):
    items: list[ProviderListItem]
    total: int
    page: int
    page_size: int
