"""Carga idempotente del catálogo de ejemplo (docs/20261105_BD_BaseDatos_EU.md §9, §10).

Uso: python -m seed.load   (omite lo que ya existe)
"""

import json
from datetime import date
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.catalogo.models import (
    Provider,
    ProviderImage,
    ProviderReview,
    ProviderVerification,
    Service,
    ServiceEventType,
)
from app.shared.db import get_engine

SEED_FILE = Path(__file__).with_name("seed.json")


def load_seed(session: Session) -> None:
    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    for p in data["providers"]:
        if session.get(Provider, p["id"]) is None:
            session.add(
                Provider(
                    id=p["id"],
                    name=p["name"],
                    description=p["description"],
                    neighborhood=p["neighborhood"],
                    municipality=p["municipality"],
                    phone=p["phone"],
                    email=p["email"],
                    latitude=p.get("latitude"),
                    longitude=p.get("longitude"),
                    featured=p.get("featured", False),
                )
            )
            for m in p.get("images", []):
                session.add(
                    ProviderImage(
                        id=m["id"],
                        provider_id=p["id"],
                        url=m["url"],
                        alt_text=m["alt_text"],
                        position=m["position"],
                    )
                )
            for r in p.get("reviews", []):
                session.add(
                    ProviderReview(
                        id=r["id"],
                        provider_id=p["id"],
                        author_name=r["author_name"],
                        rating=r["rating"],
                        comment=r["comment"],
                        reviewed_on=date.fromisoformat(r["reviewed_on"]),
                    )
                )
            for v in p["verifications"]:
                session.add(
                    ProviderVerification(
                        id=v["id"],
                        provider_id=p["id"],
                        check_type=v["check_type"],
                        checked_on=date.fromisoformat(v["checked_on"]),
                        notes=v["notes"],
                    )
                )
    session.flush()
    for s in data["services"]:
        if session.get(Service, s["id"]) is None:
            session.add(
                Service(
                    id=s["id"],
                    provider_id=s["provider_id"],
                    category=s["category"],
                    level=s["level"],
                    name=s["name"],
                    description=s["description"],
                    price_model=s["price_model"],
                    base_price_cop=s["base_price_cop"],
                    min_guests=s["min_guests"],
                    max_guests=s["max_guests"],
                )
            )
            for e in s["event_types"]:
                session.add(ServiceEventType(service_id=s["id"], event_type=e))
    session.commit()


def load_seed_if_empty() -> None:
    with Session(get_engine()) as session:
        if session.scalar(select(func.count()).select_from(Provider)) == 0:
            load_seed(session)


if __name__ == "__main__":
    with Session(get_engine()) as session:
        load_seed(session)
    print("Semilla cargada (datos de ejemplo, por validar con proveedores reales).")
