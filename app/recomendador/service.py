"""Coordinación de catálogo, dominio y respuesta de recomendaciones."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.errors import AppError
from app.recomendador.domain.recomendar import recomendar
from app.recomendador.domain.tipos import CATEGORIES, Recommendation, ServiceOption
from app.recomendador.schemas import (
    QuoteResponse,
    RecommendationBreakdownResponse,
    RecommendationItemResponse,
    RecommendationPackageResponse,
    RecommendationResponse,
    RecommendationUnavailableResponse,
)
from app.shared.money import cost_for_guests

REQUIRED_CATEGORIES = ("espacio", "alimentacion", "decoracion")


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


def get_quote(
    budget_cop: int | None,
    event_type: str,
    guests: int,
    service_ids: list[str],
    session: Session,
) -> QuoteResponse:
    catalog = _eligible_catalog(session, event_type, guests)
    services_by_id = {service.id: service for service in catalog}

    if len(set(service_ids)) != len(service_ids):
        raise AppError(
            "VALIDATION_ERROR",
            "Revise los datos ingresados.",
            422,
            {"service_ids": "No se puede incluir el mismo servicio más de una vez."},
        )

    selected = [services_by_id.get(service_id) for service_id in service_ids]
    if any(service is None for service in selected):
        raise AppError(
            "VALIDATION_ERROR",
            "Revise los datos ingresados.",
            422,
            {
                "service_ids": (
                    "Uno o más servicios no están disponibles para el tipo de evento o número de invitados."
                )
            },
        )

    selected_services = [service for service in selected if service is not None]
    selected_categories = [service.category for service in selected_services]
    if len(set(selected_categories)) != len(selected_categories):
        raise AppError(
            "VALIDATION_ERROR",
            "Revise los datos ingresados.",
            422,
            {"service_ids": "Solo se permite un servicio por rubro."},
        )

    items_by_category: dict[str, list[RecommendationItemResponse]] = {}
    total_cop = 0
    for service in selected_services:
        cost_cop = cost_for_guests(service.price_model, service.base_price_cop, guests)
        total_cop += cost_cop
        items_by_category[service.category] = [
            RecommendationItemResponse(
                service_id=service.id,
                name=service.name,
                provider_id=service.provider_id,
                provider_name=service.provider_name,
                verification_status=service.verification_status,
                cost_cop=cost_cop,
            )
        ]

    if budget_cop is not None and total_cop > budget_cop:
        raise AppError(
            "BUDGET_EXCEEDED",
            "Ese cambio supera su presupuesto. Elija otra opción.",
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
    missing_categories = [category for category in REQUIRED_CATEGORIES if category not in items_by_category]

    return QuoteResponse(
        total_cop=total_cop,
        remaining_cop=budget_cop - total_cop if budget_cop is not None else None,
        breakdown=breakdown,
        missing_categories=missing_categories,
        ineligible=[],
    )
