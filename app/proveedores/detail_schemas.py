"""Esquemas de la ficha del proveedor."""

from datetime import date

from pydantic import BaseModel


class ProviderImageItem(BaseModel):
    url: str
    alt_text: str


class ProviderReviewItem(BaseModel):
    author_name: str
    rating: int
    comment: str
    reviewed_on: date


class VerificationCheckItem(BaseModel):
    type: str
    date: date


class ProviderVerificationDetail(BaseModel):
    status: str
    checks: list[VerificationCheckItem]


class ProviderServiceItem(BaseModel):
    id: str
    name: str
    category: str
    description: str
    price_model: str
    unit_price_cop: int
    min_guests: int
    max_guests: int
    level: str


class ProviderDetailResponse(BaseModel):
    id: str
    name: str
    categories: list[str]
    description: str
    neighborhood: str
    municipality: str
    phone: str
    email: str
    latitude: float | None
    longitude: float | None
    images: list[ProviderImageItem]
    rating_avg: float | None
    rating_count: int
    reviews: list[ProviderReviewItem]
    verification: ProviderVerificationDetail
    services: list[ProviderServiceItem]
