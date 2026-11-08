import re
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from seed.load import load_seed


def _quote(client) -> dict[str, object]:
    response = client.post(
        "/api/v1/recommendations",
        json={"budget_cop": 10_000_000, "event_type": "boda", "guests": 80},
    )
    assert response.status_code == 200
    package = response.json()["packages"][1]
    return {
        "service_ids": [
            item["service_id"] for category in package["breakdown"] for item in category["items"]
        ],
        "expected_total_cop": package["total_cop"],
    }


def _reservation_payload(client, **overrides: object) -> dict[str, object]:
    quote = _quote(client)
    body: dict[str, object] = {
        "budget_cop": 10_000_000,
        "event_type": "boda",
        "guests": 80,
        "modality": "personalizado",
        "service_ids": quote["service_ids"],
        "expected_total_cop": quote["expected_total_cop"],
        "customer": {
            "name": "Organizador de prueba",
            "email": "organizador@example.invalid",
            "phone": "3001234567",
        },
        "event_date": (date.today() + timedelta(days=30)).isoformat(),
    }
    body.update(overrides)
    return body


def test_post_reservations_creates_unique_code_and_service_snapshot(client, session):
    load_seed(session)
    body = _reservation_payload(client)

    response = client.post("/api/v1/reservations", json=body)

    assert response.status_code == 201
    result = response.json()
    assert re.fullmatch(r"EU-[A-Z0-9]{6}", result["code"])
    assert result["status"] == "creada"
    assert result["total_cop"] == body["expected_total_cop"]
    assert result["customer"] == body["customer"]
    assert result["event_date"] == body["event_date"]
    assert len(result["items"]) == len(body["service_ids"])
    stored = session.execute(
        text(
            "select r.budget_cop, r.modality, r.total_cop, i.service_id, i.category, i.service_name, "
            "i.provider_name, i.price_model, i.unit_price_cop, i.cost_cop "
            "from reservations r join reservation_items i on i.reservation_id = r.id "
            "where r.code = :code order by i.category"
        ),
        {"code": result["code"]},
    ).all()
    assert len(stored) == len(body["service_ids"])
    assert all(row.budget_cop == 10_000_000 for row in stored)
    assert all(row.modality == "personalizado" for row in stored)
    assert sum(row.cost_cop for row in stored) == result["total_cop"]
    stored_by_service_id = {row.service_id: row for row in stored}
    for service_id in body["service_ids"]:
        catalog = session.execute(
            text(
                "select s.category, s.name, p.name as provider_name, s.price_model, "
                "s.base_price_cop, case when s.price_model = 'fijo' then s.base_price_cop "
                "else s.base_price_cop * :guests end as cost_cop "
                "from services s join providers p on p.id = s.provider_id where s.id = :service_id"
            ),
            {"service_id": service_id, "guests": body["guests"]},
        ).one()
        snapshot = stored_by_service_id[service_id]
        assert snapshot.service_name == catalog.name
        assert snapshot.provider_name == catalog.provider_name
        assert snapshot.price_model == catalog.price_model
        assert snapshot.unit_price_cop == catalog.base_price_cop
        assert snapshot.cost_cop == catalog.cost_cop
        assert snapshot.category == catalog.category

    second_response = client.post("/api/v1/reservations", json=body)
    assert second_response.status_code == 201
    assert second_response.json()["code"] != result["code"]


def test_post_reservations_accepts_missing_budget(client, session):
    load_seed(session)
    body = _reservation_payload(client)
    body.pop("budget_cop")

    response = client.post("/api/v1/reservations", json=body)

    assert response.status_code == 201
    assert response.json()["status"] == "creada"
    assert response.json()["total_cop"] == body["expected_total_cop"]
    assert (
        session.execute(
            text("select budget_cop from reservations where code = :code"),
            {"code": response.json()["code"]},
        ).scalar_one()
        is None
    )


@pytest.mark.parametrize(
    ("field", "value", "expected_message"),
    [
        ("customer.name", "", "Ingrese su nombre."),
        ("customer.name", "   ", "Ingrese su nombre."),
        ("customer.email", "correo-invalido", "Ingrese un correo electrónico válido."),
        ("customer.phone", "300123", "Ingrese un teléfono de 10 dígitos."),
        ("event_date", date.today().isoformat(), "Seleccione una fecha posterior a hoy."),
        ("event_date", "", "Seleccione una fecha posterior a hoy."),
    ],
)
def test_post_reservations_validates_customer_and_event_fields(
    client, session, field, value, expected_message
):
    load_seed(session)
    body = _reservation_payload(client)
    if field.startswith("customer."):
        body["customer"][field.split(".", maxsplit=1)[1]] = value
    else:
        body[field] = value

    response = client.post("/api/v1/reservations", json=body)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["fields"][field] == expected_message
    assert session.execute(text("select count(*) from reservations")).scalar_one() == 0


def test_post_reservations_rejects_mismatched_total(client, session):
    load_seed(session)
    body = _reservation_payload(client)
    body["expected_total_cop"] += 1

    response = client.post("/api/v1/reservations", json=body)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TOTAL_MISMATCH"
    assert (
        response.json()["error"]["message"]
        == "No fue posible crear la reserva. Revise su evento e intente nuevamente."
    )
    assert session.execute(text("select count(*) from reservations")).scalar_one() == 0


def test_post_reservations_rejects_budget_exceeded(client, session):
    load_seed(session)
    body = _reservation_payload(client, budget_cop=1_000_000)

    response = client.post("/api/v1/reservations", json=body)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BUDGET_EXCEEDED"
    assert "No fue posible crear la reserva." in response.json()["error"]["message"]
    assert session.execute(text("select count(*) from reservations")).scalar_one() == 0


def test_post_reservations_rejects_missing_required_categories(client, session):
    load_seed(session)
    quote = _quote(client)
    first_service_id = quote["service_ids"][0]
    single_service_cost = session.execute(
        text(
            "select case when s.price_model = 'fijo' then s.base_price_cop "
            "else s.base_price_cop * 80 end from services s where s.id = :service_id"
        ),
        {"service_id": first_service_id},
    ).scalar_one()
    body = _reservation_payload(
        client,
        service_ids=[first_service_id],
        expected_total_cop=single_service_cost,
    )

    response = client.post("/api/v1/reservations", json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "No fue posible crear la reserva." in response.json()["error"]["message"]
    assert session.execute(text("select count(*) from reservations")).scalar_one() == 0


def test_post_reservations_revalidates_current_catalog_prices(client, session):
    load_seed(session)
    body = _reservation_payload(client)
    service_id = body["service_ids"][0]
    session.execute(
        text("update services set base_price_cop = base_price_cop + 1000 where id = :id"),
        {"id": service_id},
    )
    session.commit()

    response = client.post("/api/v1/reservations", json=body)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TOTAL_MISMATCH"
    assert session.execute(text("select count(*) from reservations")).scalar_one() == 0


def test_post_reservations_rejects_ineligible_service(client, session):
    load_seed(session)
    body = _reservation_payload(client, guests=500)

    response = client.post("/api/v1/reservations", json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "No fue posible crear la reserva." in response.json()["error"]["message"]
    assert session.execute(text("select count(*) from reservations")).scalar_one() == 0
