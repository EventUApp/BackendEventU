from seed.load import load_seed


def test_get_provider_detail_returns_profile_verification_and_services(client, session):
    load_seed(session)

    response = client.get("/api/v1/providers/prv-salon-los-guaduales")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "prv-salon-los-guaduales"
    assert body["name"] == "Salón Los Guaduales"
    assert body["categories"] == ["espacio"]
    assert body["description"]
    assert body["neighborhood"] == "Ciudad Jardín"
    assert body["municipality"] == "Cali"
    assert body["phone"] and body["email"]
    assert body["verification"]["status"] == "verificado"
    assert body["verification"]["checks"]
    assert all(check["type"] and check["date"] for check in body["verification"]["checks"])
    assert body["services"]
    service = body["services"][0]
    assert {
        "id",
        "name",
        "category",
        "description",
        "price_model",
        "unit_price_cop",
        "min_guests",
        "max_guests",
        "level",
    } == set(service)
    assert service["unit_price_cop"] > 0
    assert service["min_guests"] <= service["max_guests"]


def test_provider_without_verification_checks_is_in_review(client, session):
    load_seed(session)

    response = client.get("/api/v1/providers/prv-terraza-san-antonio")

    assert response.status_code == 200
    assert response.json()["verification"] == {"status": "en_revision", "checks": []}


def test_get_unknown_provider_returns_not_found_message(client):
    response = client.get("/api/v1/providers/prv-no-existe")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "No encontramos este proveedor.",
        }
    }


def test_provider_detail_includes_gallery_and_review_summary(client, session):
    load_seed(session)

    response = client.get("/api/v1/providers/prv-salon-los-guaduales")

    assert response.status_code == 200
    body = response.json()
    assert body["images"]
    assert body["images"][0]["url"].startswith("https://")
    assert body["rating_avg"] == 4.7
    assert body["rating_count"] == 3
    assert len(body["reviews"]) <= 5
    assert body["reviews"] == sorted(
        body["reviews"], key=lambda review: (review["reviewed_on"], review["author_name"]), reverse=True
    )
