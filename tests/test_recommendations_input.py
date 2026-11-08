def test_post_recommendations_accepts_valid_payload(client, monkeypatch):
    from app.recomendador.domain.tipos import Recommendation

    monkeypatch.setattr("app.recomendador.service.recomendar", lambda *_: Recommendation((), ()))
    body = {"budget_cop": 2_500_000, "event_type": "boda", "guests": 120}

    r = client.post("/api/v1/recommendations", json=body)

    assert r.status_code == 200
    assert r.json() == {"packages": [], "unavailable": []}


def test_post_recommendations_rejects_invalid_ranges(client):
    r = client.post(
        "/api/v1/recommendations",
        json={"budget_cop": 500_000, "event_type": "", "guests": 0},
    )

    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Revise los datos ingresados."
    assert {"budget_cop", "event_type", "guests"}.issubset(body["error"]["fields"].keys())


def test_post_recommendations_requires_all_fields(client):
    r = client.post("/api/v1/recommendations", json={"budget_cop": 2_000_000})

    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert {"event_type", "guests"}.issubset(body["error"]["fields"].keys())
