"""Función pura del recomendador (SAD §6).

Invariante: el total de todo paquete devuelto es <= presupuesto (RN-01).
"""

from collections.abc import Sequence

from app.recomendador.domain.tipos import (
    CATEGORIES,
    MODALITIES,
    PackageItem,
    PackageResult,
    Recommendation,
    ServiceOption,
    Unavailable,
)
from app.shared.money import cost_for_guests

MODALITY_TARGET_PERCENT = {
    "ahorro": 70,
    "equilibrado": 85,
    "premium": 100,
}

CATEGORY_WEIGHTS = {
    "espacio": 40,
    "alimentacion": 35,
    "decoracion": 15,
    "entretenimiento": 10,
}

REQUIRED_CATEGORIES = ("espacio", "alimentacion", "decoracion")


def _service_cost(service: ServiceOption, guests: int) -> int:
    return cost_for_guests(service.price_model, service.base_price_cop, guests)


def _sort_candidates(candidates: Sequence[ServiceOption], guests: int) -> list[ServiceOption]:
    return sorted(candidates, key=lambda service: (_service_cost(service, guests), service.id))


def _category_caps(objective_cop: int, categories: Sequence[str]) -> dict[str, int]:
    denominator = sum(CATEGORY_WEIGHTS[category] for category in categories)
    return {category: objective_cop * CATEGORY_WEIGHTS[category] // denominator for category in categories}


def _select_service(modality: str, candidates: Sequence[ServiceOption], guests: int) -> ServiceOption:
    if modality == "ahorro":
        return candidates[0]
    if modality == "premium":
        highest_cost = _service_cost(candidates[-1], guests)
        return next(service for service in candidates if _service_cost(service, guests) == highest_cost)
    return candidates[(len(candidates) - 1) // 2]


def _build_package(
    modality: str, chosen: dict[str, ServiceOption], budget_cop: int, guests: int
) -> PackageResult:
    items = tuple(
        PackageItem(service=chosen[category], cost_cop=_service_cost(chosen[category], guests))
        for category in CATEGORIES
        if category in chosen
    )
    total_cop = sum(item.cost_cop for item in items)
    return PackageResult(
        modality=modality,
        items=items,
        total_cop=total_cop,
        remaining_cop=budget_cop - total_cop,
    )


def recomendar(
    presupuesto: int, tipo_evento: str, invitados: int, catalogo: Sequence[ServiceOption]
) -> Recommendation:
    eligible_by_category = {
        category: _sort_candidates(
            [
                service
                for service in catalogo
                if service.category == category
                and tipo_evento in service.event_types
                and service.min_guests <= invitados <= service.max_guests
            ],
            invitados,
        )
        for category in CATEGORIES
    }

    packages: list[PackageResult] = []
    unavailable: list[Unavailable] = []

    for modality in MODALITIES:
        objective_cop = presupuesto * MODALITY_TARGET_PERCENT[modality] // 100
        categories = list(REQUIRED_CATEGORIES)

        if modality != "ahorro":
            entertainment_cap = objective_cop * CATEGORY_WEIGHTS["entretenimiento"] // 100
            eligible_entertainment = [
                service
                for service in eligible_by_category["entretenimiento"]
                if _service_cost(service, invitados) <= entertainment_cap
            ]
            if eligible_entertainment:
                categories.append("entretenimiento")

        caps = _category_caps(objective_cop, categories)
        chosen: dict[str, ServiceOption] = {}
        missing_required = False

        for category in categories:
            candidates = eligible_by_category[category]
            within_cap = [
                service for service in candidates if _service_cost(service, invitados) <= caps[category]
            ]
            if within_cap:
                chosen[category] = _select_service(modality, within_cap, invitados)
            elif category in REQUIRED_CATEGORIES and candidates:
                chosen[category] = candidates[0]
            elif category in REQUIRED_CATEGORIES:
                missing_required = True
                break

        if missing_required:
            unavailable.append(Unavailable(modality=modality, cause="sin_servicios"))
            continue

        total_cop = sum(_service_cost(service, invitados) for service in chosen.values())
        if total_cop > objective_cop:
            unavailable.append(Unavailable(modality=modality, cause="presupuesto_insuficiente"))
            continue

        packages.append(_build_package(modality, chosen, presupuesto, invitados))

    return Recommendation(packages=tuple(packages), unavailable=tuple(unavailable))
