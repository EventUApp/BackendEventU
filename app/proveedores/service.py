"""Reglas de presentación y precio del listado de proveedores."""

from collections import defaultdict

from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.errors import AppError
from app.proveedores.repository import get_eligible_providers
from app.proveedores.schemas import ProviderListItem, ProviderListResponse, ProviderSort

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50
CATEGORY_ORDER = ("espacio", "alimentacion", "decoracion", "entretenimiento")
MINIMUM_RATINGS = (3.0, 4.0, 4.5)


def _service_cost(service: RowMapping, guests: int | None) -> int:
    base_price_cop = int(service["base_price_cop"])
    if service["price_model"] == "por_invitado":
        return base_price_cop * (guests if guests is not None else int(service["min_guests"]))
    return base_price_cop


def get_providers(
    session: Session,
    guests: int | None,
    event_type: str | None,
    category: str | None,
    min_price_cop: int | None,
    max_price_cop: int | None,
    min_rating: float | None,
    verified: bool | None,
    sort: ProviderSort,
    page: int,
    page_size: int,
) -> ProviderListResponse:
    if min_price_cop is not None and max_price_cop is not None and min_price_cop > max_price_cop:
        message = "El precio mínimo no puede ser mayor que el máximo."
        raise AppError("VALIDATION_ERROR", message, 422, {"min_price_cop": message})
    if min_rating is not None and min_rating not in MINIMUM_RATINGS:
        raise AppError(
            "VALIDATION_ERROR",
            "Seleccione una calificación mínima válida.",
            422,
            {"min_rating": "Seleccione 3, 4 o 4,5."},
        )

    providers, services = get_eligible_providers(session, guests, event_type)
    services_by_provider: dict[str, list[RowMapping]] = defaultdict(list)
    for service in services:
        services_by_provider[str(service["provider_id"])].append(service)

    items = []
    for provider in providers:
        provider_services = services_by_provider[str(provider["id"])]
        categories = {str(service["category"]) for service in provider_services}
        items.append(
            ProviderListItem(
                id=str(provider["id"]),
                name=str(provider["name"]),
                categories=[category for category in CATEGORY_ORDER if category in categories],
                neighborhood=str(provider["neighborhood"]),
                municipality=str(provider["municipality"]),
                latitude=float(provider["latitude"]) if provider["latitude"] is not None else None,
                longitude=float(provider["longitude"]) if provider["longitude"] is not None else None,
                cover_url=str(provider["cover_url"]) if provider["cover_url"] is not None else None,
                rating_avg=float(provider["rating_avg"]) if provider["rating_avg"] is not None else None,
                rating_count=int(provider["rating_count"]),
                verification_status=str(provider["verification_status"]),
                price_from_cop=min(_service_cost(service, guests) for service in provider_services),
                featured=bool(provider["featured"]),
            )
        )

    if category is not None:
        items = [item for item in items if category in item.categories]
    if min_price_cop is not None:
        items = [item for item in items if item.price_from_cop >= min_price_cop]
    if max_price_cop is not None:
        items = [item for item in items if item.price_from_cop <= max_price_cop]
    if min_rating is not None:
        items = [item for item in items if item.rating_avg is not None and item.rating_avg >= min_rating]
    if verified:
        items = [item for item in items if item.verification_status == "verificado"]

    if sort == "precio_asc":
        items.sort(key=lambda item: (item.price_from_cop, item.id))
    elif sort == "precio_desc":
        items.sort(key=lambda item: (-item.price_from_cop, item.id))
    elif sort == "calificacion":
        items.sort(
            key=lambda item: (
                item.rating_avg is None,
                -(item.rating_avg or 0),
                -item.rating_count,
                item.id,
            )
        )
    else:
        items.sort(
            key=lambda item: (
                not item.featured,
                item.rating_avg is None,
                -(item.rating_avg or 0),
                item.id,
            )
        )

    total = len(items)
    start = (page - 1) * page_size
    return ProviderListResponse(
        items=items[start : start + page_size], total=total, page=page, page_size=page_size
    )
