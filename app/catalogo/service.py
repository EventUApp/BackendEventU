"""Servicios del catálogo para la vista de inicio."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.shared.db import get_session


@dataclass(frozen=True)
class EligibleService:
    id: str
    category: str
    name: str
    provider_name: str
    price_model: str
    base_price_cop: int


def get_eligible_services(
    service_ids: list[str], event_type: str, guests: int, session: Session
) -> tuple[EligibleService, ...]:
    rows: list[RowMapping] = list(
        session.execute(
            text(
                """
                SELECT s.id, s.category, s.name, p.name AS provider_name,
                       s.price_model, s.base_price_cop
                FROM services s
                JOIN providers p ON p.id = s.provider_id
                JOIN service_event_types t ON t.service_id = s.id
                WHERE s.id IN :service_ids
                  AND t.event_type = :event_type
                  AND :guests BETWEEN s.min_guests AND s.max_guests
                ORDER BY s.id ASC
                """
            ).bindparams(bindparam("service_ids", expanding=True)),
            {"service_ids": service_ids, "event_type": event_type, "guests": guests},
        ).mappings()
    )
    return tuple(
        EligibleService(
            id=str(row["id"]),
            category=str(row["category"]),
            name=str(row["name"]),
            provider_name=str(row["provider_name"]),
            price_model=str(row["price_model"]),
            base_price_cop=int(row["base_price_cop"]),
        )
        for row in rows
    )


def get_home_data(session: Session | None = None) -> dict[str, Any]:
    """Devuelve los proveedores destacados y el conteo por rubro para /home."""
    session = session or next(get_session())

    categories = session.execute(
        text(
            """
            SELECT s.category AS category,
                   COUNT(DISTINCT s.provider_id) AS provider_count
            FROM services s
            GROUP BY s.category
            ORDER BY CASE s.category
                WHEN 'espacio' THEN 0
                WHEN 'alimentacion' THEN 1
                WHEN 'decoracion' THEN 2
                WHEN 'entretenimiento' THEN 3
                ELSE 4
            END
            """
        )
    ).all()

    featured = session.execute(
        text(
            """
            SELECT
                p.id,
                p.name,
                p.neighborhood,
                p.municipality,
                p.featured,
                p.verification_status,
                p.rating_avg,
                p.rating_count,
                (
                    SELECT i.url
                    FROM provider_images i
                    WHERE i.provider_id = p.id
                    ORDER BY i.position ASC, i.id ASC
                    LIMIT 1
                ) AS cover_url,
                (
                    SELECT MIN(
                        CASE
                            WHEN s.price_model = 'fijo' THEN s.base_price_cop
                            ELSE s.base_price_cop * s.min_guests
                        END
                    )
                    FROM services s
                    WHERE s.provider_id = p.id
                ) AS price_from_cop
            FROM v_providers p
            WHERE p.featured = 1
            ORDER BY
                CASE WHEN p.rating_avg IS NULL THEN 1 ELSE 0 END ASC,
                p.rating_avg DESC,
                p.id ASC
            LIMIT 6
            """
        )
    ).all()

    return {
        "categories": [{"category": row.category, "count": int(row.provider_count)} for row in categories],
        "featured": [
            {
                "id": row.id,
                "name": row.name,
                "neighborhood": row.neighborhood,
                "municipality": row.municipality,
                "featured": bool(row.featured),
                "verification_status": row.verification_status,
                "rating_avg": float(row.rating_avg) if row.rating_avg is not None else None,
                "rating_count": int(row.rating_count) if row.rating_count is not None else 0,
                "cover_url": row.cover_url,
                "price_from_cop": int(row.price_from_cop) if row.price_from_cop is not None else 0,
            }
            for row in featured
        ],
    }
