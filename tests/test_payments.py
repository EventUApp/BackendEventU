import uuid
from datetime import date

import pytest
from sqlalchemy import inspect, text

from app.pagos.gateway import APPROVED_TEST_CARD, DECLINED_TEST_CARD
from app.reservas.models import Reservation


def _create_reservation(session, code: str = "EU-PAY001", status: str = "creada") -> None:
    session.add(
        Reservation(
            id=str(uuid.uuid4()),
            code=code,
            status=status,
            event_type="boda",
            guests=50,
            budget_cop=None,
            modality="personalizado",
            total_cop=125_000,
            customer_name="Cliente de prueba",
            customer_email="cliente@example.invalid",
            customer_phone="3001234567",
            event_date=date(2027, 1, 10),
        )
    )
    session.commit()


def _payment_body(code: str, number: str = APPROVED_TEST_CARD) -> dict[str, object]:
    return {
        "reservation_code": code,
        "card": {"number": number, "expiry": "12/30", "cvv": "123"},
    }


def test_post_payments_approves_and_updates_reservation_without_storing_card(client, session):
    _create_reservation(session)
    card_body = _payment_body("EU-PAY001")

    response = client.post("/api/v1/payments", json=card_body)

    assert response.status_code == 200
    body = response.json()
    assert body["payment"]["status"] == "aprobado"
    assert body["payment"]["amount_cop"] == 125_000
    assert body["payment"]["reference"].startswith("SIM-")
    assert body["reservation_status"] == "pagada"
    payment_columns = {column["name"] for column in inspect(session.bind).get_columns("payments")}
    assert not any(
        token in column for column in payment_columns for token in ("card", "number", "expiry", "cvv")
    )
    stored_payment = session.execute(text("select status, amount_cop, reference from payments")).one()
    assert stored_payment.status == "aprobado"
    assert stored_payment.amount_cop == 125_000
    assert APPROVED_TEST_CARD not in repr(stored_payment)
    assert "12/30" not in repr(stored_payment)
    assert "123" not in repr(stored_payment)
    assert (
        session.execute(text("select status from reservations where code = 'EU-PAY001'")).scalar_one()
        == "pagada"
    )


def test_post_payments_declines_test_card_and_allows_approved_retry(client, session):
    _create_reservation(session)

    declined = client.post(
        "/api/v1/payments",
        json=_payment_body("EU-PAY001", DECLINED_TEST_CARD),
    )

    assert declined.status_code == 200
    assert declined.json()["payment"]["status"] == "rechazado"
    assert declined.json()["reservation_status"] == "pago_rechazado"
    approved = client.post("/api/v1/payments", json=_payment_body("EU-PAY001"))
    assert approved.status_code == 200
    assert approved.json()["payment"]["status"] == "aprobado"
    assert approved.json()["reservation_status"] == "pagada"
    assert session.execute(text("select count(*) from payments where status = 'rechazado'")).scalar_one() == 1
    assert session.execute(text("select count(*) from payments where status = 'aprobado'")).scalar_one() == 1


def test_post_payments_rejects_unknown_card_number(client, session):
    _create_reservation(session)

    response = client.post(
        "/api/v1/payments",
        json=_payment_body("EU-PAY001", "4111111111111111"),
    )

    assert response.status_code == 200
    assert response.json()["payment"]["status"] == "rechazado"
    assert response.json()["reservation_status"] == "pago_rechazado"


@pytest.mark.parametrize(
    ("card", "field", "message"),
    [
        (
            {"number": "", "expiry": "12/30", "cvv": "123"},
            "card.number",
            "Ingrese un número de tarjeta válido.",
        ),
        (
            {"number": "1234", "expiry": "12/30", "cvv": "123"},
            "card.number",
            "Ingrese un número de tarjeta válido.",
        ),
        (
            {"number": "424242424242424x", "expiry": "12/30", "cvv": "123"},
            "card.number",
            "Ingrese un número de tarjeta válido.",
        ),
        (
            {"number": APPROVED_TEST_CARD, "expiry": "13/30", "cvv": "123"},
            "card.expiry",
            "Ingrese una fecha de vencimiento válida.",
        ),
        (
            {"number": APPROVED_TEST_CARD, "expiry": "01/20", "cvv": "123"},
            "card.expiry",
            "Ingrese una fecha de vencimiento válida.",
        ),
        (
            {"number": APPROVED_TEST_CARD, "expiry": "12/30", "cvv": ""},
            "card.cvv",
            "Ingrese el código de seguridad.",
        ),
    ],
)
def test_post_payments_validates_card_fields_without_persisting_attempt(
    client, session, card, field, message
):
    _create_reservation(session)

    response = client.post(
        "/api/v1/payments",
        json={"reservation_code": "EU-PAY001", "card": card},
    )

    assert response.status_code == 422
    assert response.json()["error"]["fields"][field] == message
    assert session.execute(text("select count(*) from payments")).scalar_one() == 0


def test_post_payments_rejects_unknown_reservation(client, session):
    response = client.post("/api/v1/payments", json=_payment_body("EU-ABC123"))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize("status", ["pagada", "cancelada"])
def test_post_payments_rejects_reservation_that_cannot_be_paid(client, session, status):
    _create_reservation(session, status=status)

    response = client.post("/api/v1/payments", json=_payment_body("EU-PAY001"))

    expected_code = "ALREADY_PAID" if status == "pagada" else "INVALID_STATE"
    assert response.status_code == 409
    assert response.json()["error"]["code"] == expected_code
    assert session.execute(text("select count(*) from payments")).scalar_one() == 0


def test_post_payments_does_not_create_multiple_approved_payments(client, session):
    _create_reservation(session)
    first = client.post("/api/v1/payments", json=_payment_body("EU-PAY001"))
    second = client.post("/api/v1/payments", json=_payment_body("EU-PAY001"))

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "ALREADY_PAID"
    assert session.execute(text("select count(*) from payments where status = 'aprobado'")).scalar_one() == 1


def test_payment_attempts_never_log_sensitive_card_values(client, session, caplog):
    _create_reservation(session)
    number, expiry, cvv = APPROVED_TEST_CARD, "12/30", "123"

    response = client.post(
        "/api/v1/payments",
        json=_payment_body("EU-PAY001", number),
    )

    assert response.status_code == 200
    assert number not in caplog.text
    assert expiry not in caplog.text
    assert cvv not in caplog.text
