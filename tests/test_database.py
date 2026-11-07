import json
import uuid
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.shared.db import Base
from seed.load import load_seed


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
