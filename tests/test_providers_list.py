import pytest
from sqlalchemy import text

from seed.load import load_seed


def test_list_providers_returns_summaries_and_default_page(client, session):
    load_seed(session)

    response = client.get("/api/v1/providers")

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["total"] == 16
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert len(body["items"]) == 10
    keys = [
        (
            not item["featured"],
            item["rating_avg"] is None,
            -(item["rating_avg"] or 0),
            item["id"],
        )
        for item in body["items"]
    ]
    assert keys == sorted(keys)
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

    assert response.status_code == 200, response.json()
    body = response.json()
    providers = {item["id"]: item for item in body["items"]}
    assert "prv-salon-los-guaduales" in providers
    assert "prv-salon-comunal-versalles" in providers
    assert "prv-terraza-san-antonio" not in providers
    assert providers["prv-salon-los-guaduales"]["price_from_cop"] == 1_600_000
    assert providers["prv-sabor-valluno"]["price_from_cop"] == 1_400_000
    expected_prices = dict(
        session.execute(
            text(
                """
                SELECT provider_id,
                       MIN(CASE WHEN price_model = 'por_invitado'
                                THEN base_price_cop * :guests
                                ELSE base_price_cop END) AS price_from_cop
                FROM services
                WHERE :guests BETWEEN min_guests AND max_guests
                GROUP BY provider_id
                """
            ),
            {"guests": 100},
        ).all()
    )
    assert set(providers) == set(expected_prices)
    assert {
        provider_id: provider["price_from_cop"] for provider_id, provider in providers.items()
    } == expected_prices


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

    first_ids = [item["id"] for item in first_page["items"]]
    second_ids = [item["id"] for item in second_page["items"]]
    assert first_page["total"] == second_page["total"] == 16
    assert first_page["page"] == 1
    assert second_page["page"] == 2
    assert first_page["page_size"] == second_page["page_size"] == 10
    assert len(first_ids) == 10
    assert len(second_page["items"]) == 6
    assert set(first_ids).isdisjoint(second_ids)
    assert len(first_ids + second_ids) == first_page["total"]


def test_list_providers_returns_empty_page_when_filters_match_no_providers(client, session):
    load_seed(session)

    response = client.get("/api/v1/providers", params={"max_price_cop": 0})

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "page_size": 10}


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


def test_list_providers_applies_combined_filters(client, session):
    load_seed(session)

    response = client.get(
        "/api/v1/providers",
        params={
            "category": "espacio",
            "event_type": "boda",
            "guests": 100,
            "min_price_cop": 1_000_000,
            "max_price_cop": 5_000_000,
            "min_rating": 4,
            "verified": True,
            "sort": "precio_asc",
            "page_size": 50,
        },
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["total"] == len(body["items"])
    assert body["items"]
    assert all("espacio" in provider["categories"] for provider in body["items"])
    assert all(
        provider["rating_avg"] is not None and provider["rating_avg"] >= 4 for provider in body["items"]
    )
    assert all(provider["verification_status"] == "verificado" for provider in body["items"])
    assert all(1_000_000 <= provider["price_from_cop"] <= 5_000_000 for provider in body["items"])
    assert [(provider["price_from_cop"], provider["id"]) for provider in body["items"]] == sorted(
        (provider["price_from_cop"], provider["id"]) for provider in body["items"]
    )
    eligible_ids = set(
        session.execute(
            text(
                """
                SELECT DISTINCT s.provider_id
                FROM services s
                JOIN service_event_types t ON t.service_id = s.id
                WHERE s.category = 'espacio'
                  AND t.event_type = 'boda'
                  AND 100 BETWEEN s.min_guests AND s.max_guests
                """
            )
        ).scalars()
    )
    assert {provider["id"] for provider in body["items"]} <= eligible_ids


def test_list_providers_rejects_minimum_price_greater_than_maximum(client):
    response = client.get(
        "/api/v1/providers",
        params={"min_price_cop": 2_000_000, "max_price_cop": 1_000_000},
    )

    assert response.status_code == 422
    error = response.json()["error"]
    expected_message = "El precio mínimo no puede ser mayor que el máximo."
    assert error["code"] == "VALIDATION_ERROR"
    assert error["message"] == expected_message
    assert error["fields"] == {"min_price_cop": expected_message}


def test_list_providers_requires_integer_price_filters(client):
    response = client.get("/api/v1/providers", params={"min_price_cop": "1000.5"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "min_price_cop" in error["fields"]


def test_list_providers_filters_bbox_inclusively_and_returns_coordinates(client, session):
    load_seed(session)

    response = client.get(
        "/api/v1/providers",
        params={"bbox": "3.368,-76.538,3.368,-76.538", "page_size": 50},
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == "prv-salon-los-guaduales"
    assert body["items"][0]["latitude"] == 3.368
    assert body["items"][0]["longitude"] == -76.538


def test_list_providers_bbox_excludes_providers_without_coordinates(client, session):
    load_seed(session)
    session.execute(
        text("update providers set latitude = null, longitude = null where id = :id"),
        {"id": "prv-salon-los-guaduales"},
    )
    session.commit()

    response = client.get(
        "/api/v1/providers",
        params={"bbox": "3.368,-76.538,3.368,-76.538", "page_size": 50},
    )

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def test_list_providers_without_bbox_includes_provider_without_coordinates(client, session):
    load_seed(session)
    session.execute(
        text("update providers set latitude = null, longitude = null where id = :id"),
        {"id": "prv-salon-los-guaduales"},
    )
    session.commit()

    response = client.get(
        "/api/v1/providers",
        params={"page_size": 50},
    )

    assert response.status_code == 200
    provider = next(item for item in response.json()["items"] if item["id"] == "prv-salon-los-guaduales")
    assert provider["latitude"] is None
    assert provider["longitude"] is None


def test_list_providers_combines_bbox_with_existing_filters_and_sort(client, session):
    load_seed(session)

    response = client.get(
        "/api/v1/providers",
        params={
            "bbox": "3.2,-76.6,3.5,-76.5",
            "category": "espacio",
            "sort": "precio_asc",
            "page_size": 50,
        },
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all("espacio" in item["categories"] for item in items)
    assert all(3.2 <= item["latitude"] <= 3.5 for item in items)
    assert all(-76.6 <= item["longitude"] <= -76.5 for item in items)
    assert [item["price_from_cop"] for item in items] == sorted(item["price_from_cop"] for item in items)


@pytest.mark.parametrize(
    "bbox",
    [
        "3.3,-76.6,3.4",
        "north,-76.6,3.4,-76.5",
        "91,-76.6,92,-76.5",
        "3.3,-181,3.4,-180",
        "3.4,-76.6,3.3,-76.5",
        "3.3,-76.5,3.4,-76.6",
    ],
)
def test_list_providers_validates_bbox(client, bbox):
    response = client.get("/api/v1/providers", params={"bbox": bbox})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "bbox" in error["fields"]


@pytest.mark.parametrize("min_rating", [3, 4, 4.5])
def test_list_providers_accepts_proposed_rating_thresholds(client, session, min_rating):
    load_seed(session)

    response = client.get(
        "/api/v1/providers",
        params={"min_rating": min_rating, "page_size": 50},
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(item["rating_avg"] is not None and item["rating_avg"] >= min_rating for item in items)


@pytest.mark.parametrize("sort", ["recomendados", "precio_asc", "precio_desc", "calificacion"])
def test_list_providers_uses_deterministic_sort_rules(client, session, sort):
    load_seed(session)

    response = client.get("/api/v1/providers", params={"sort": sort, "page_size": 50})

    assert response.status_code == 200
    items = response.json()["items"]
    if sort == "recomendados":
        keys = [
            (
                not item["featured"],
                item["rating_avg"] is None,
                -(item["rating_avg"] or 0),
                item["id"],
            )
            for item in items
        ]
    elif sort == "precio_asc":
        keys = [(item["price_from_cop"], item["id"]) for item in items]
    elif sort == "precio_desc":
        keys = [(-item["price_from_cop"], item["id"]) for item in items]
    else:
        keys = [
            (
                item["rating_avg"] is None,
                -(item["rating_avg"] or 0),
                -item["rating_count"],
                item["id"],
            )
            for item in items
        ]
    assert keys == sorted(keys)


@pytest.mark.parametrize("sort", ["recomendados", "precio_asc", "precio_desc", "calificacion"])
def test_list_providers_breaks_complete_sort_ties_by_id(client, session, sort):
    load_seed(session)
    session.execute(text("update providers set featured = 0"))
    session.execute(text("delete from provider_reviews"))
    session.execute(text("update services set price_model = 'fijo', base_price_cop = 1000"))
    session.commit()

    response = client.get("/api/v1/providers", params={"sort": sort, "page_size": 50})

    assert response.status_code == 200
    ids = [provider["id"] for provider in response.json()["items"]]
    assert len(ids) == 16
    assert ids == sorted(ids)


def test_list_providers_validates_filter_values(client):
    response = client.get(
        "/api/v1/providers",
        params={"category": "unknown", "sort": "nearest"},
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert {"category", "sort"}.issubset(error["fields"])

    response = client.get("/api/v1/providers", params={"min_rating": 3.5})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "min_rating" in error["fields"]
