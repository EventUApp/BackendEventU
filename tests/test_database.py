import json
import re
import uuid
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import CheckConstraint, inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.catalogo.models import Provider, ProviderImage, ProviderReview, ProviderVerification
from app.pagos.models import Payment
from app.reservas.models import Reservation, ReservationItem
from app.shared.db import Base
from app.shared.money import cost_for_guests
from seed.load import load_seed


def test_payment_model_has_only_documented_columns(engine):
    columns = {column["name"] for column in inspect(engine).get_columns("payments")}
    assert columns == {"id", "reservation_id", "status", "amount_cop", "reference", "created_at"}


def test_payment_model_declares_status_and_amount_checks():
    checks = {
        re.sub(r"\s+", "", str(constraint.sqltext)).lower()
        for constraint in Payment.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert "statusin('aprobado','rechazado')" in checks
    assert "amount_cop>0" in checks


def test_migration_matches_models(engine):
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    assert set(Base.metadata.tables) <= tables
    for name, table in Base.metadata.tables.items():
        db_cols = {c["name"] for c in insp.get_columns(name)}
        assert {c.name for c in table.columns} == db_cols, name


def test_no_card_columns(engine):
    insp = inspect(engine)
    cols = {c["name"] for t in insp.get_table_names() for c in insp.get_columns(t)}
    assert not {c for c in cols if "card" in c or "cvv" in c or "expiry" in c}


def test_seed_is_idempotent_and_complete(session):
    load_seed(session)
    load_seed(session)
    n = lambda q: session.execute(text(q)).scalar()  # noqa: E731
    assert n("select count(*) from providers") == 16
    assert n("select count(*) from services") == 35
    assert n("select count(*) from v_providers where verification_status='verificado'") == 10
    assert n("select count(*) from v_providers where verification_status='en_revision'") == 6
    assert n("select count(*) from provider_images") == 64
    assert n("select count(*) from provider_reviews") == 63
    assert n("select count(*) from providers where featured") == 6
    seed = json.loads((Path(__file__).parent.parent / "seed" / "seed.json").read_text(encoding="utf-8"))
    assert len(seed["services"]) == 35


def test_provider_verification_models_load_seed_and_derive_status(session):
    load_seed(session)
    seed = json.loads((Path(__file__).parent.parent / "seed" / "seed.json").read_text(encoding="utf-8"))

    providers = session.scalars(select(Provider)).all()
    verifications = session.scalars(select(ProviderVerification)).all()
    expected_checks = {
        (
            check["id"],
            provider["id"],
            check["check_type"],
            check["checked_on"],
        )
        for provider in seed["providers"]
        for check in provider["verifications"]
    }
    loaded_checks = {
        (check.id, check.provider_id, check.check_type, check.checked_on.isoformat())
        for check in verifications
    }
    verified_provider_ids = {check.provider_id for check in verifications}

    assert {provider.id for provider in providers} == {provider["id"] for provider in seed["providers"]}
    assert loaded_checks == expected_checks
    assert session.execute(
        text("select id from v_providers where verification_status = 'verificado' order by id")
    ).scalars().all() == sorted(verified_provider_ids)


def test_provider_gallery_and_reviews_models_seed_and_rating_view(session):
    load_seed(session)
    seed = json.loads((Path(__file__).parent.parent / "seed" / "seed.json").read_text(encoding="utf-8"))

    providers = session.scalars(select(Provider)).all()
    images = session.scalars(select(ProviderImage)).all()
    reviews = session.scalars(select(ProviderReview)).all()
    images_by_provider: dict[str, list[ProviderImage]] = {}
    reviews_by_provider: dict[str, list[ProviderReview]] = {}
    for image in images:
        images_by_provider.setdefault(image.provider_id, []).append(image)
    for review in reviews:
        reviews_by_provider.setdefault(review.provider_id, []).append(review)

    assert len(providers) == len(seed["providers"]) == 16
    assert len(images) == 64
    assert len(reviews) == 63
    for provider in providers:
        provider_images = images_by_provider[provider.id]
        provider_reviews = reviews_by_provider[provider.id]
        assert len(provider_images) >= 3
        assert len(provider_reviews) >= 3
        assert sum(image.position == 1 for image in provider_images) == 1
        assert all(image.url.startswith("https://") and image.alt_text for image in provider_images)
        assert all(1 <= review.rating <= 5 for review in provider_reviews)
        expected_rating = session.execute(
            text("select round(avg(rating), 1) from provider_reviews where provider_id = :provider_id"),
            {"provider_id": provider.id},
        ).scalar_one()
        actual_rating, actual_count = session.execute(
            text("select rating_avg, rating_count from v_providers where id = :provider_id"),
            {"provider_id": provider.id},
        ).one()
        assert actual_rating == pytest.approx(expected_rating)
        assert actual_count == len(provider_reviews)


def _reservation(session, code="EU-AB12CD", total=100, budget=1000):
    rid = str(uuid.uuid4())
    session.execute(
        text(
            "insert into reservations (id,code,event_type,guests,budget_cop,modality,total_cop,"
            "customer_name,customer_email,customer_phone,event_date) values "
            "(:id,:code,'boda',50,:budget,'ahorro',:total,'Ejemplo','a@ejemplo.invalid','3000000000',:d)"
        ),
        {"id": rid, "code": code, "budget": budget, "total": total, "d": date(2027, 1, 10)},
    )
    return rid


def test_total_cannot_exceed_budget(session):
    with pytest.raises(IntegrityError):
        _reservation(session, total=2000, budget=1000)


def test_invalid_reservation_code(session):
    with pytest.raises(IntegrityError):
        _reservation(session, code="XX-123456")


def test_only_one_approved_payment_per_reservation(session):
    rid = _reservation(session)
    ins = "insert into payments (id,reservation_id,status,amount_cop,reference) values (:i,:r,:s,100,:ref)"
    session.execute(text(ins), {"i": str(uuid.uuid4()), "r": rid, "s": "rechazado", "ref": "SIM-1"})
    session.execute(text(ins), {"i": str(uuid.uuid4()), "r": rid, "s": "aprobado", "ref": "SIM-2"})
    with pytest.raises(IntegrityError):
        session.execute(text(ins), {"i": str(uuid.uuid4()), "r": rid, "s": "aprobado", "ref": "SIM-3"})


@pytest.mark.parametrize(
    ("status", "amount"),
    [("pendiente", 100), ("aprobado", 0), ("rechazado", -1)],
)
def test_payment_migration_rejects_invalid_status_and_amount(session, status, amount):
    rid = _reservation(session)
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "insert into payments (id,reservation_id,status,amount_cop,reference) "
                "values (:id,:reservation_id,:status,:amount,:reference)"
            ),
            {
                "id": str(uuid.uuid4()),
                "reservation_id": rid,
                "status": status,
                "amount": amount,
                "reference": f"SIM-{uuid.uuid4().hex}",
            },
        )
    session.rollback()


def test_rating_is_derived_from_reviews(session):
    load_seed(session)
    avg, cnt = session.execute(
        text("select rating_avg, rating_count from v_providers where id='prv-salon-los-guaduales'")
    ).one()
    assert cnt == 3 and avg == pytest.approx(4.7, abs=0.05)
    expected = session.execute(
        text("select round(avg(rating),1) from provider_reviews where provider_id='prv-salon-los-guaduales'")
    ).scalar()
    assert avg == pytest.approx(float(expected))


def test_geo_columns_all_or_nothing(session):
    ins = (
        "insert into providers "
        "(id,name,description,neighborhood,municipality,phone,email,latitude,longitude) "
        "values ('prv-geo-test','x','x','x','x','3000000000','a@ejemplo.invalid',:la,:lo)"
    )
    with pytest.raises(IntegrityError):
        session.execute(text(ins), {"la": 3.4, "lo": None})
    session.rollback()
    with pytest.raises(IntegrityError):
        session.execute(text(ins), {"la": 95.0, "lo": -76.5})


def test_image_position_unique_and_https_only(session):
    load_seed(session)
    ins = (
        "insert into provider_images (id,provider_id,url,alt_text,position) "
        "values (:i,'prv-salon-los-guaduales',:u,'x',:p)"
    )
    with pytest.raises(IntegrityError):
        session.execute(text(ins), {"i": str(uuid.uuid4()), "u": "https://ejemplo.invalid/a.jpg", "p": 1})
    session.rollback()
    with pytest.raises(IntegrityError):
        session.execute(text(ins), {"i": str(uuid.uuid4()), "u": "http://ejemplo.invalid/a.jpg", "p": 9})


def test_review_rating_range(session):
    load_seed(session)
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "insert into provider_reviews (id,provider_id,author_name,rating,comment,reviewed_on) "
                "values (:i,'prv-salon-los-guaduales','Ana',6,'x',:d)"
            ),
            {"i": str(uuid.uuid4()), "d": date(2026, 6, 1)},
        )


def test_reservation_without_budget_and_custom_modality(session):
    rid = str(uuid.uuid4())
    session.execute(
        text(
            "insert into reservations (id,code,event_type,guests,budget_cop,modality,total_cop,"
            "customer_name,customer_email,customer_phone,event_date) values "
            "(:id,'EU-ZZ99ZZ','boda',50,NULL,'personalizado',0,'Ejemplo','a@ejemplo.invalid','3000000000',:d)"
        ),
        {"id": rid, "d": date(2027, 1, 10)},
    )
    assert session.execute(text("select count(*) from reservations where budget_cop is null")).scalar() == 1


def test_reservation_models_preserve_service_snapshot_after_catalog_removal(session):
    load_seed(session)
    service = session.execute(
        text(
            "select s.id, s.category, s.name, s.price_model, s.base_price_cop, "
            "p.name as provider_name "
            "from services s join providers p on p.id = s.provider_id "
            "where s.category = 'espacio' order by s.id limit 1"
        )
    ).one()
    reservation_id = str(uuid.uuid4())
    guests = 50
    cost_cop = cost_for_guests(service.price_model, service.base_price_cop, guests)
    reservation = Reservation(
        id=reservation_id,
        code="EU-SNAP01",
        status="creada",
        event_type="boda",
        guests=guests,
        budget_cop=None,
        modality="personalizado",
        total_cop=cost_cop,
        customer_name="Organizador de prueba",
        customer_email="organizador@example.invalid",
        customer_phone="3000000000",
        event_date=date(2027, 1, 10),
    )
    item = ReservationItem(
        reservation_id=reservation_id,
        category=service.category,
        service_id=service.id,
        service_name=service.name,
        provider_name=service.provider_name,
        price_model=service.price_model,
        unit_price_cop=service.base_price_cop,
        cost_cop=cost_cop,
    )
    session.add_all((reservation, item))
    session.commit()

    session.execute(text("delete from services where id = :service_id"), {"service_id": service.id})
    session.commit()

    saved_reservation = session.get(Reservation, reservation_id)
    saved_item = session.get(ReservationItem, (reservation_id, service.category))
    assert saved_reservation is not None
    assert saved_reservation.status == "creada"
    assert saved_reservation.budget_cop is None
    assert saved_reservation.modality == "personalizado"
    assert saved_item is not None
    assert saved_item.service_id is None
    assert saved_item.service_name == service.name
    assert saved_item.provider_name == service.provider_name
    assert saved_item.price_model == service.price_model
    assert saved_item.unit_price_cop == service.base_price_cop
    assert saved_item.cost_cop == cost_cop
