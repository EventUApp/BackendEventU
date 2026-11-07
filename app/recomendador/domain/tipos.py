"""Tipos del dominio del recomendador. Sin dependencias de FastAPI ni SQLAlchemy (ADR-03)."""

from dataclasses import dataclass

CATEGORIES = ("espacio", "alimentacion", "decoracion", "entretenimiento")
MODALITIES = ("ahorro", "equilibrado", "premium")


@dataclass(frozen=True)
class ServiceOption:
    id: str
    provider_id: str
    provider_name: str
    verification_status: str
    category: str
    level: str
    name: str
    price_model: str  # 'fijo' | 'por_invitado'
    base_price_cop: int
    min_guests: int
    max_guests: int
    event_types: tuple[str, ...]


@dataclass(frozen=True)
class PackageItem:
    service: ServiceOption
    cost_cop: int


@dataclass(frozen=True)
class PackageResult:
    modality: str
    items: tuple[PackageItem, ...]
    total_cop: int
    remaining_cop: int


@dataclass(frozen=True)
class Unavailable:
    modality: str
    cause: str  # 'presupuesto_insuficiente' | 'sin_servicios'


@dataclass(frozen=True)
class Recommendation:
    packages: tuple[PackageResult, ...]
    unavailable: tuple[Unavailable, ...]
