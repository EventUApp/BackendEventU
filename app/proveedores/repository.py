"""Consultas de lectura del catálogo de proveedores."""

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

PROVIDER_QUERY = text(
    """
    SELECT p.id, p.name, p.neighborhood, p.municipality, p.latitude, p.longitude,
           p.featured, p.verification_status, p.rating_avg, p.rating_count,
           (
               SELECT i.url
               FROM provider_images i
               WHERE i.provider_id = p.id
               ORDER BY i.position ASC, i.id ASC
               LIMIT 1
           ) AS cover_url
    FROM v_providers p
    WHERE EXISTS (
        SELECT 1
        FROM services s
        WHERE s.provider_id = p.id
          AND (:guests IS NULL OR :guests BETWEEN s.min_guests AND s.max_guests)
          AND (
              :event_type IS NULL
              OR EXISTS (
                  SELECT 1
                  FROM service_event_types t
                  WHERE t.service_id = s.id AND t.event_type = :event_type
              )
          )
    )
    ORDER BY p.id ASC
    """
)

ELIGIBLE_SERVICES_QUERY = text(
    """
    SELECT s.provider_id, s.category, s.price_model, s.base_price_cop, s.min_guests
    FROM services s
    WHERE (:guests IS NULL OR :guests BETWEEN s.min_guests AND s.max_guests)
      AND (
          :event_type IS NULL
          OR EXISTS (
              SELECT 1
              FROM service_event_types t
              WHERE t.service_id = s.id AND t.event_type = :event_type
          )
      )
    ORDER BY s.category ASC, s.id ASC
    """
)


def get_eligible_providers(
    session: Session, guests: int | None, event_type: str | None
) -> tuple[list[RowMapping], list[RowMapping]]:
    parameters = {"guests": guests, "event_type": event_type}
    providers = list(session.execute(PROVIDER_QUERY, parameters).mappings().all())
    services = list(session.execute(ELIGIBLE_SERVICES_QUERY, parameters).mappings().all())
    return providers, services
