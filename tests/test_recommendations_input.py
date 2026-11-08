import pytest


@pytest.mark.parametrize("event_type", ["cumpleanos", "boda", "xv"])
@pytest.mark.parametrize(
    ("budget_cop", "guests"),
    [(1_000_000, 1), (50_000_000, 500)],
)
def test_post_recommendations_accepts_valid_payload(client, event_type, budget_cop, guests, monkeypatch):
    from app.recomendador.domain.tipos import Recommendation

    monkeypatch.setattr("app.recomendador.service.recomendar", lambda *_: Recommendation((), ()))
    body = {"budget_cop": budget_cop, "event_type": event_type, "guests": guests}

    response = client.post("/api/v1/recommendations", json=body)

    assert response.status_code == 200
    assert response.json() == {"packages": [], "unavailable": []}


@pytest.mark.parametrize(
    ("body", "invalid_field"),
    [
        ({"event_type": "boda", "guests": 120}, "budget_cop"),
        ({"budget_cop": 2_500_000, "guests": 120}, "event_type"),
        ({"budget_cop": 2_500_000, "event_type": "boda"}, "guests"),
        ({"budget_cop": None, "event_type": "boda", "guests": 120}, "budget_cop"),
        ({"budget_cop": "", "event_type": "boda", "guests": 120}, "budget_cop"),
        ({"budget_cop": 999_999, "event_type": "boda", "guests": 120}, "budget_cop"),
        ({"budget_cop": 50_000_001, "event_type": "boda", "guests": 120}, "budget_cop"),
        ({"budget_cop": 2_500_000, "event_type": "", "guests": 120}, "event_type"),
        ({"budget_cop": 2_500_000, "event_type": None, "guests": 120}, "event_type"),
        ({"budget_cop": 2_500_000, "event_type": "otro", "guests": 120}, "event_type"),
        ({"budget_cop": 2_500_000, "event_type": "boda", "guests": None}, "guests"),
        ({"budget_cop": 2_500_000, "event_type": "boda", "guests": ""}, "guests"),
        ({"budget_cop": 2_500_000, "event_type": "boda", "guests": 0}, "guests"),
        ({"budget_cop": 2_500_000, "event_type": "boda", "guests": 501}, "guests"),
    ],
)
def test_post_recommendations_rejects_missing_or_invalid_fields(client, body, invalid_field):
    response = client.post("/api/v1/recommendations", json=body)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["message"] == "Revise los datos ingresados."
    assert invalid_field in error["fields"]
    assert error["fields"][invalid_field]
    assert "Input should" not in error["fields"][invalid_field]
    assert "greater than" not in error["fields"][invalid_field]


def test_unexpected_error_returns_generic_message(client):
    def fail() -> None:
        raise RuntimeError("internal detail")

    client.app.add_api_route("/api/v1/test-failure", fail, methods=["POST"])

    response = client.post("/api/v1/test-failure")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "No fue posible completar la operación. Intente nuevamente.",
        }
    }
