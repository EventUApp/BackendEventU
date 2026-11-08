import logging

from fastapi import HTTPException

from app.errors import GENERIC_MESSAGE, AppError


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_unknown_route_uses_uniform_error_format(client):
    r = client.get("/api/v1/no-existe")
    assert r.status_code == 404
    body = r.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"] == "No encontramos lo solicitado."
    assert set(body["error"]) == {"code", "message"}


def test_business_error_uses_uniform_format(client):
    def fail() -> None:
        raise AppError(
            "INVALID_STATE",
            "La reserva no se puede modificar.",
            status_code=409,
            fields={"status": "Estado inválido."},
        )

    client.app.add_api_route("/api/v1/test-business-error", fail, methods=["GET"])

    response = client.get("/api/v1/test-business-error")

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "INVALID_STATE",
            "message": "La reserva no se puede modificar.",
            "fields": {"status": "Estado inválido."},
        }
    }


def test_unexpected_error_is_generic_and_not_logged_with_details(client, caplog):
    internal_detail = "database-password-and-query"

    def fail() -> None:
        raise RuntimeError(internal_detail)

    client.app.add_api_route("/api/v1/test-unexpected-error", fail, methods=["GET"])

    with caplog.at_level(logging.ERROR, logger="eventu"):
        response = client.get("/api/v1/test-unexpected-error")

    assert response.status_code == 500
    assert response.json() == {"error": {"code": "INTERNAL_ERROR", "message": GENERIC_MESSAGE}}
    assert internal_detail not in response.text
    assert internal_detail not in caplog.text
    assert "Traceback" not in response.text
    assert "fields" not in response.json()["error"]


def test_http_server_error_does_not_expose_exception_detail(client):
    internal_detail = "database connection string"

    def fail() -> None:
        raise HTTPException(status_code=503, detail=internal_detail)

    client.app.add_api_route("/api/v1/test-http-failure", fail, methods=["GET"])

    response = client.get("/api/v1/test-http-failure")

    assert response.status_code == 503
    assert response.json() == {"error": {"code": "INTERNAL_ERROR", "message": GENERIC_MESSAGE}}
    assert internal_detail not in response.text


def test_openapi_available(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert "/api/v1/health" in r.json()["paths"]
