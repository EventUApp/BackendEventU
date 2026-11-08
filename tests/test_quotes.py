from sqlalchemy import text

from app.shared.money import cost_for_guests
from seed.load import load_seed


def _recommended_service_ids(client) -> list[str]:
    response = client.post(
        "/api/v1/recommendations",
        json={"budget_cop": 10_000_000, "event_type": "boda", "guests": 80},
    )
    assert response.status_code == 200
    package = response.json()["packages"][1]
    return [item["service_id"] for category in package["breakdown"] for item in category["items"]]


def test_post_quotes_calculates_total_and_remaining_from_catalog(client, session):
    load_seed(session)
    service_ids = _recommended_service_ids(client)

    response = client.post(
        "/api/v1/quotes",
        json={
            "budget_cop": 10_000_000,
            "event_type": "boda",
            "guests": 80,
            "service_ids": service_ids,
        },
    )

    assert response.status_code == 200
    body = response.json()
    items = [item for category in body["breakdown"] for item in category["items"]]
    assert body["total_cop"] == sum(item["cost_cop"] for item in items)
    assert body["remaining_cop"] == 10_000_000 - body["total_cop"]
    assert body["missing_categories"] == []
    assert body["ineligible"] == []
    assert all(isinstance(item["cost_cop"], int) for item in items)
    for item in items:
        price_model, base_price_cop = session.execute(
            text("select price_model, base_price_cop from services where id = :id"),
            {"id": item["service_id"]},
        ).one()
        assert item["cost_cop"] == cost_for_guests(price_model, base_price_cop, 80)


def test_post_quotes_allows_missing_optional_budget(client, session):
    load_seed(session)
    service_ids = _recommended_service_ids(client)

    response = client.post(
        "/api/v1/quotes",
        json={"event_type": "boda", "guests": 80, "service_ids": service_ids},
    )

    assert response.status_code == 200
    assert response.json()["remaining_cop"] is None


def test_post_quotes_rejects_total_over_budget(client, session):
    load_seed(session)
    session.execute(
        text(
            "insert into services "
            "(id, provider_id, category, level, name, description, price_model, "
            "base_price_cop, min_guests, max_guests) "
            "values ('svc-quote-over-budget', 'prv-salon-los-guaduales', 'espacio', "
            "'premium', 'Espacio de prueba', 'Descripción', 'fijo', 1_500_000, 1, 500)"
        )
    )
    session.execute(
        text(
            "insert into service_event_types (service_id, event_type) "
            "values ('svc-quote-over-budget', 'boda')"
        )
    )
    session.commit()

    response = client.post(
        "/api/v1/quotes",
        json={
            "budget_cop": 1_000_000,
            "event_type": "boda",
            "guests": 80,
            "service_ids": ["svc-quote-over-budget"],
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BUDGET_EXCEEDED"
    assert response.json()["error"]["message"] == ("Ese cambio supera su presupuesto. Elija otra opción.")


def test_post_quotes_rejects_services_that_are_not_eligible(client, session):
    load_seed(session)
    session.execute(
        text(
            "insert into services "
            "(id, provider_id, category, level, name, description, price_model, "
            "base_price_cop, min_guests, max_guests) "
            "values ('svc-quote-ineligible', 'prv-salon-los-guaduales', 'espacio', "
            "'premium', 'Espacio de prueba', 'Descripción', 'fijo', 1_500_000, 1, 50)"
        )
    )
    session.execute(
        text(
            "insert into service_event_types (service_id, event_type) values ('svc-quote-ineligible', 'boda')"
        )
    )
    session.commit()

    response = client.post(
        "/api/v1/quotes",
        json={
            "event_type": "boda",
            "guests": 80,
            "service_ids": ["svc-quote-ineligible"],
        },
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "service_ids" in error["fields"]


def test_post_quotes_rejects_multiple_services_from_same_category(client, session):
    load_seed(session)
    space_ids = (
        session.execute(
            text(
                "select s.id from services s "
                "join service_event_types t on t.service_id = s.id "
                "where s.category = 'espacio' and t.event_type = 'boda' "
                "and s.min_guests <= 80 and s.max_guests >= 80 "
                "order by s.id limit 2"
            )
        )
        .scalars()
        .all()
    )
    assert len(space_ids) == 2

    response = client.post(
        "/api/v1/quotes",
        json={"event_type": "boda", "guests": 80, "service_ids": space_ids},
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "service_ids" in error["fields"]


def test_post_quotes_reports_missing_required_categories(client, session):
    load_seed(session)
    service_ids = _recommended_service_ids(client)
    space_id = next(
        item_id
        for item_id in service_ids
        if session.execute(text("select category from services where id = :id"), {"id": item_id}).scalar_one()
        == "espacio"
    )

    response = client.post(
        "/api/v1/quotes",
        json={"event_type": "boda", "guests": 80, "service_ids": [space_id]},
    )

    assert response.status_code == 200
    assert response.json()["missing_categories"] == ["alimentacion", "decoracion"]
