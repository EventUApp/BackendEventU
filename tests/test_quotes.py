from sqlalchemy import bindparam, text

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


def _service_cost(session, service_id: str, guests: int) -> int:
    price_model, base_price_cop = session.execute(
        text("select price_model, base_price_cop from services where id = :id"),
        {"id": service_id},
    ).one()
    return cost_for_guests(price_model, base_price_cop, guests)


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


def test_post_quotes_recalculates_total_when_a_service_is_changed(client, session):
    load_seed(session)
    original_service_ids = _recommended_service_ids(client)
    original_space_id = next(
        service_id
        for service_id in original_service_ids
        if session.execute(
            text("select category from services where id = :id"), {"id": service_id}
        ).scalar_one()
        == "espacio"
    )
    original_cost = _service_cost(session, original_space_id, 80)
    other_services_cost = sum(
        _service_cost(session, service_id, 80)
        for service_id in original_service_ids
        if service_id != original_space_id
    )
    alternatives = session.execute(
        text(
            "select s.id, s.price_model, s.base_price_cop from services s "
            "join service_event_types t on t.service_id = s.id "
            "where s.category = 'espacio' and t.event_type = 'boda' "
            "and s.id not in :service_ids "
            "and s.min_guests <= 80 and s.max_guests >= 80 order by s.id"
        ).bindparams(bindparam("service_ids", expanding=True)),
        {"service_ids": original_service_ids},
    ).all()
    alternative = next(
        (
            row
            for row in alternatives
            if (
                cost_for_guests(row.price_model, row.base_price_cop, 80) != original_cost
                and other_services_cost + cost_for_guests(row.price_model, row.base_price_cop, 80)
                <= 10_000_000
            )
        ),
        None,
    )
    assert alternative is not None
    changed_service_ids = [
        alternative.id if service_id == original_space_id else service_id
        for service_id in original_service_ids
    ]

    response = client.post(
        "/api/v1/quotes",
        json={
            "budget_cop": 10_000_000,
            "event_type": "boda",
            "guests": 80,
            "service_ids": changed_service_ids,
        },
    )

    assert response.status_code == 200
    body = response.json()
    expected_costs = {
        service_id: _service_cost(session, service_id, 80) for service_id in changed_service_ids
    }
    quoted_items = [item for category in body["breakdown"] for item in category["items"]]
    assert {item["service_id"] for item in quoted_items} == set(changed_service_ids)
    assert {item["service_id"]: item["cost_cop"] for item in quoted_items} == expected_costs
    assert body["total_cop"] == sum(expected_costs.values())
    assert body["remaining_cop"] == 10_000_000 - body["total_cop"]
    assert body["missing_categories"] == []


def test_post_quotes_allows_missing_optional_budget(client, session):
    load_seed(session)
    service_ids = _recommended_service_ids(client)

    response = client.post(
        "/api/v1/quotes",
        json={"event_type": "boda", "guests": 80, "service_ids": service_ids},
    )

    assert response.status_code == 200
    body = response.json()
    items = [item for category in body["breakdown"] for item in category["items"]]
    assert body["total_cop"] == sum(item["cost_cop"] for item in items)
    assert body["total_cop"] > 0
    assert body["remaining_cop"] is None
    assert body["missing_categories"] == []


def test_post_quotes_recalculates_total_when_optional_entertainment_is_removed(client, session):
    load_seed(session)
    service_ids = _recommended_service_ids(client)
    entertainment_id = session.execute(
        text(
            "select s.id from services s join service_event_types t on t.service_id = s.id "
            "where s.category = 'entretenimiento' and t.event_type = 'boda' "
            "and s.min_guests <= 80 and s.max_guests >= 80 order by s.id limit 1"
        )
    ).scalar_one()
    service_ids = [
        service_id
        for service_id in service_ids
        if session.execute(
            text("select category from services where id = :id"), {"id": service_id}
        ).scalar_one()
        != "entretenimiento"
    ]
    full_service_ids = [*service_ids, entertainment_id]

    full_quote = client.post(
        "/api/v1/quotes",
        json={"event_type": "boda", "guests": 80, "service_ids": full_service_ids},
    )
    quote_without_entertainment = client.post(
        "/api/v1/quotes",
        json={"event_type": "boda", "guests": 80, "service_ids": service_ids},
    )

    assert full_quote.status_code == quote_without_entertainment.status_code == 200
    full_body = full_quote.json()
    reduced_body = quote_without_entertainment.json()
    entertainment_cost = next(
        item["cost_cop"]
        for category in full_body["breakdown"]
        if category["category"] == "entretenimiento"
        for item in category["items"]
    )
    assert full_body["missing_categories"] == reduced_body["missing_categories"] == []
    assert reduced_body["total_cop"] == full_body["total_cop"] - entertainment_cost
    assert all(category["category"] != "entretenimiento" for category in reduced_body["breakdown"])


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


def test_post_quotes_revalidates_service_capacity_when_guest_count_changes(client, session):
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

    initial_quote = client.post(
        "/api/v1/quotes",
        json={
            "event_type": "boda",
            "guests": 50,
            "service_ids": ["svc-quote-ineligible"],
        },
    )

    assert initial_quote.status_code == 200
    assert initial_quote.json()["ineligible"] == []

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
    body = response.json()
    assert body["missing_categories"] == ["alimentacion", "decoracion"]
    assert body["total_cop"] == sum(
        item["cost_cop"] for category in body["breakdown"] for item in category["items"]
    )
    assert [category["category"] for category in body["breakdown"]] == ["espacio"]
