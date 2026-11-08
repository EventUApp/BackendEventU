import uuid
from datetime import date

from sqlalchemy import text

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


def test_provider_detail_gallery_matches_list_cover_photo(client, session):
    load_seed(session)

    detail = client.get("/api/v1/providers/prv-salon-los-guaduales").json()
    listing = client.get("/api/v1/providers", params={"page_size": 50}).json()
    card = next(item for item in listing["items"] if item["id"] == detail["id"])

    assert detail["images"][0]["url"] == card["cover_url"]
    assert detail["images"][0]["alt_text"]
    assert len(detail["images"]) >= 3


def test_provider_detail_returns_only_five_newest_reviews(client, session):
    load_seed(session)
    session.execute(
        text(
            "insert into provider_reviews "
            "(id, provider_id, author_name, rating, comment, reviewed_on) "
            "values (:id, :provider_id, :author_name, :rating, :comment, :reviewed_on)"
        ),
        [
            {
                "id": str(uuid.uuid4()),
                "provider_id": "prv-salon-los-guaduales",
                "author_name": "Reseña reciente",
                "rating": 5,
                "comment": "Reseña de ejemplo",
                "reviewed_on": date(2026, 11, 7),
            },
            {
                "id": str(uuid.uuid4()),
                "provider_id": "prv-salon-los-guaduales",
                "author_name": "Reseña siguiente",
                "rating": 4,
                "comment": "Reseña de ejemplo",
                "reviewed_on": date(2026, 11, 6),
            },
        ],
    )
    session.commit()

    response = client.get("/api/v1/providers/prv-salon-los-guaduales")

    assert response.status_code == 200
    body = response.json()
    review_dates = [review["reviewed_on"] for review in body["reviews"]]
    assert len(body["reviews"]) == 5
    assert review_dates == sorted(review_dates, reverse=True)
    assert review_dates[:2] == ["2026-11-07", "2026-11-06"]
    expected_rating, expected_count = session.execute(
        text(
            "select round(avg(rating), 1), count(*) "
            "from provider_reviews where provider_id = 'prv-salon-los-guaduales'"
        )
    ).one()
    assert body["rating_avg"] == expected_rating
    assert body["rating_count"] == expected_count


def test_provider_detail_without_images_or_reviews_returns_empty_collections(client, session):
    session.execute(
        text(
            "insert into providers "
            "(id, name, description, neighborhood, municipality, phone, email) "
            "values ('prv-sin-galeria', 'Proveedor sin galería', 'Descripción', "
            "'Centro', 'Cali', '3000000000', 'contacto@ejemplo.invalid')"
        )
    )
    session.commit()

    response = client.get("/api/v1/providers/prv-sin-galeria")

    assert response.status_code == 200
    body = response.json()
    assert body["images"] == []
    assert body["reviews"] == []
    assert body["rating_avg"] is None
    assert body["rating_count"] == 0
