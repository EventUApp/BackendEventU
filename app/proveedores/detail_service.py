"""Lógica de lectura de la ficha del proveedor."""

from sqlalchemy.orm import Session

from app.errors import AppError
from app.proveedores.detail_repository import get_provider_detail_data
from app.proveedores.detail_schemas import (
    ProviderDetailResponse,
    ProviderImageItem,
    ProviderReviewItem,
    ProviderServiceItem,
    ProviderVerificationDetail,
    VerificationCheckItem,
)


def get_provider_detail(session: Session, provider_id: str) -> ProviderDetailResponse:
    provider, checks, services, images, reviews = get_provider_detail_data(session, provider_id)
    if provider is None:
        raise AppError("NOT_FOUND", "No encontramos este proveedor.", 404)

    categories = sorted({str(service["category"]) for service in services})
    return ProviderDetailResponse(
        id=str(provider["id"]),
        name=str(provider["name"]),
        categories=categories,
        description=str(provider["description"]),
        neighborhood=str(provider["neighborhood"]),
        municipality=str(provider["municipality"]),
        phone=str(provider["phone"]),
        email=str(provider["email"]),
        latitude=float(provider["latitude"]) if provider["latitude"] is not None else None,
        longitude=float(provider["longitude"]) if provider["longitude"] is not None else None,
        images=[
            ProviderImageItem(url=str(image["url"]), alt_text=str(image["alt_text"])) for image in images
        ],
        rating_avg=float(provider["rating_avg"]) if provider["rating_avg"] is not None else None,
        rating_count=int(provider["rating_count"]),
        reviews=[
            ProviderReviewItem(
                author_name=str(review["author_name"]),
                rating=int(review["rating"]),
                comment=str(review["comment"]),
                reviewed_on=review["reviewed_on"],
            )
            for review in reviews
        ],
        verification=ProviderVerificationDetail(
            status=str(provider["verification_status"]),
            checks=[
                VerificationCheckItem(type=str(check["check_type"]), date=check["checked_on"])
                for check in checks
            ],
        ),
        services=[
            ProviderServiceItem(
                id=str(service["id"]),
                name=str(service["name"]),
                category=str(service["category"]),
                description=str(service["description"]),
                price_model=str(service["price_model"]),
                unit_price_cop=int(service["base_price_cop"]),
                min_guests=int(service["min_guests"]),
                max_guests=int(service["max_guests"]),
                level=str(service["level"]),
            )
            for service in services
        ],
    )
