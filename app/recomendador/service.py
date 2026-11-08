"""Coordinación de catálogo, dominio y respuesta de recomendaciones."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.recomendador.domain.recomendar import recomendar
from app.recomendador.domain.tipos import CATEGORIES, Recommendation, ServiceOption
from app.recomendador.schemas import (
    RecommendationBreakdownResponse,
    RecommendationItemResponse,
    RecommendationPackageResponse,
    RecommendationResponse,
    RecommendationUnavailableResponse,
)


def _eligible_catalog(session: Session, event_type: str, guests: int) -> tuple[ServiceOption, ...]:
    rows = session.execute(
        text(
            """
            SELECT s.id, s.provider_id, p.name AS provider_name, p.verification_status,
                   s.category, s.level, s.name, s.price_model, s.base_price_cop,
                   s.min_guests, s.max_guests, t.event_type
            FROM services s
            JOIN v_providers p ON p.id = s.provider_id
            JOIN service_event_types t ON t.service_id = s.id AND t.event_type = :event_type
            WHERE :guests BETWEEN s.min_guests AND s.max_guests
            ORDER BY s.id ASC
            """
        ),
        {"event_type": event_type, "guests": guests},
    ).all()
    return tuple(
        ServiceOption(
            id=row.id,
            provider_id=row.provider_id,
            provider_name=row.provider_name,
            verification_status=row.verification_status,
            category=row.category,
            level=row.level,
            name=row.name,
            price_model=row.price_model,
            base_price_cop=row.base_price_cop,
            min_guests=row.min_guests,
            max_guests=row.max_guests,
            event_types=(row.event_type,),
        )
        for row in rows
    )


def _package_response(recommendation: Recommendation) -> RecommendationResponse:
    packages: list[RecommendationPackageResponse] = []
    for result in recommendation.packages:
        items_by_category: dict[str, list[RecommendationItemResponse]] = {}
        for item in result.items:
            service = item.service
            items_by_category.setdefault(service.category, []).append(
                RecommendationItemResponse(
                    service_id=service.id,
                    name=service.name,
                    provider_id=service.provider_id,
                    provider_name=service.provider_name,
                    verification_status=service.verification_status,
                    cost_cop=item.cost_cop,
                )
            )

        breakdown = [
            RecommendationBreakdownResponse(
                category=category,
                subtotal_cop=sum(item.cost_cop for item in category_items),
                items=category_items,
            )
            for category in CATEGORIES
            if (category_items := items_by_category.get(category))
        ]
        packages.append(
            RecommendationPackageResponse(
                modality=result.modality,
                total_cop=result.total_cop,
                remaining_cop=result.remaining_cop,
                breakdown=breakdown,
            )
        )

    unavailable = [
        RecommendationUnavailableResponse(modality=item.modality, cause=item.cause)
        for item in recommendation.unavailable
    ]
    return RecommendationResponse(packages=packages, unavailable=unavailable)


def get_recommendations(
    budget_cop: int, event_type: str, guests: int, session: Session
) -> RecommendationResponse:
    catalog = _eligible_catalog(session, event_type, guests)
    recommendation = recomendar(budget_cop, event_type, guests, catalog)
    return _package_response(recommendation)
