"""Consultas para la ficha de proveedor."""

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

PROVIDER_DETAIL_QUERY = text(
    """
    SELECT id, name, description, neighborhood, municipality, phone, email,
           latitude, longitude, verification_status, rating_avg, rating_count
    FROM v_providers
    WHERE id = :provider_id
    """
)

VERIFICATION_CHECKS_QUERY = text(
    """
    SELECT check_type, checked_on
    FROM provider_verifications
    WHERE provider_id = :provider_id
    ORDER BY checked_on ASC, id ASC
    """
)

PROVIDER_SERVICES_QUERY = text(
    """
    SELECT id, name, category, description, price_model, base_price_cop,
           min_guests, max_guests, level
    FROM services
    WHERE provider_id = :provider_id
    ORDER BY category ASC, id ASC
    """
)

PROVIDER_IMAGES_QUERY = text(
    """
    SELECT url, alt_text
    FROM provider_images
    WHERE provider_id = :provider_id
    ORDER BY position ASC, id ASC
    """
)

PROVIDER_REVIEWS_QUERY = text(
    """
    SELECT author_name, rating, comment, reviewed_on
    FROM provider_reviews
    WHERE provider_id = :provider_id
    ORDER BY reviewed_on DESC, id ASC
    LIMIT 5
    """
)


def get_provider_detail_data(
    session: Session, provider_id: str
) -> tuple[RowMapping | None, list[RowMapping], list[RowMapping], list[RowMapping], list[RowMapping]]:
    parameters = {"provider_id": provider_id}
    provider = session.execute(PROVIDER_DETAIL_QUERY, parameters).mappings().one_or_none()
    if provider is None:
        return None, [], [], [], []

    checks = list(session.execute(VERIFICATION_CHECKS_QUERY, parameters).mappings().all())
    services = list(session.execute(PROVIDER_SERVICES_QUERY, parameters).mappings().all())
    images = list(session.execute(PROVIDER_IMAGES_QUERY, parameters).mappings().all())
    reviews = list(session.execute(PROVIDER_REVIEWS_QUERY, parameters).mappings().all())
    return provider, checks, services, images, reviews
