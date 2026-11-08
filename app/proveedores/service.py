"""Reglas de presentación y precio del listado de proveedores."""

from collections import defaultdict

from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.proveedores.repository import get_eligible_providers
from app.proveedores.schemas import ProviderListItem, ProviderListResponse

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50
CATEGORY_ORDER = ("espacio", "alimentacion", "decoracion", "entretenimiento")


def _service_cost(service: RowMapping, guests: int | None) -> int:
    base_price_cop = int(service["base_price_cop"])
    if service["price_model"] == "por_invitado":
        return base_price_cop * (guests if guests is not None else int(service["min_guests"]))
    return base_price_cop


def get_providers(
    session: Session,
    guests: int | None,
    event_type: str | None,
    page: int,
    page_size: int,
) -> ProviderListResponse:
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

    total = len(items)
    start = (page - 1) * page_size
    return ProviderListResponse(
        items=items[start : start + page_size], total=total, page=page, page_size=page_size
    )
