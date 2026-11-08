from seed.load import load_seed


def test_list_providers_returns_summaries_and_default_page(client, session):
    load_seed(session)

    response = client.get("/api/v1/providers")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 16
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert len(body["items"]) == 10
    assert [item["id"] for item in body["items"]] == sorted(item["id"] for item in body["items"])
    item = body["items"][0]
    assert set(item) == {
        "id",
        "name",
        "categories",
        "neighborhood",
        "municipality",
        "latitude",
        "longitude",
        "cover_url",
        "rating_avg",
        "rating_count",
        "verification_status",
        "price_from_cop",
        "featured",
    }
    assert item["categories"]
    assert item["cover_url"].startswith("https://")
    assert item["price_from_cop"] > 0


def test_list_providers_uses_guest_eligibility_and_guest_based_price(client, session):
    load_seed(session)

    response = client.get("/api/v1/providers", params={"guests": 100, "page_size": 50})

    assert response.status_code == 200
    body = response.json()
    providers = {item["id"]: item for item in body["items"]}
    assert "prv-salon-los-guaduales" in providers
    assert "prv-salon-comunal-versalles" in providers
    assert "prv-terraza-san-antonio" not in providers
    assert providers["prv-salon-los-guaduales"]["price_from_cop"] == 1_600_000
    assert providers["prv-sabor-valluno"]["price_from_cop"] == 1_400_000


def test_list_providers_uses_minimum_capacity_for_per_guest_price_without_guests(client, session):
    load_seed(session)

    response = client.get("/api/v1/providers", params={"page_size": 50})

    assert response.status_code == 200
    providers = {item["id"]: item for item in response.json()["items"]}
    assert providers["prv-sabor-valluno"]["price_from_cop"] == 280_000


def test_list_providers_paginates_without_duplicates(client, session):
    load_seed(session)

    first_page = client.get("/api/v1/providers", params={"page": 1, "page_size": 10}).json()
    second_page = client.get("/api/v1/providers", params={"page": 2, "page_size": 10}).json()

    first_ids = {item["id"] for item in first_page["items"]}
    second_ids = {item["id"] for item in second_page["items"]}
    assert first_page["total"] == second_page["total"] == 16
    assert len(second_page["items"]) == 6
    assert first_ids.isdisjoint(second_ids)


def test_list_providers_returns_empty_page_when_catalog_is_empty(client):
    response = client.get("/api/v1/providers")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "page_size": 10}


def test_list_providers_validates_query_ranges(client):
    response = client.get("/api/v1/providers", params={"guests": 0, "page": 0, "page_size": 51})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert {"guests", "page", "page_size"}.issubset(error["fields"])
