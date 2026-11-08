import uuid
from datetime import date, timedelta

from sqlalchemy import text

from seed.load import load_seed


def test_get_provider_detail_returns_profile_verification_and_services(client, session):
    load_seed(session)

    response = client.get("/api/v1/providers/prv-salon-los-guaduales")

    assert response.status_code == 200
    body = response.json()
    assert {
        "id",
        "name",
        "categories",
        "description",
        "neighborhood",
        "municipality",
        "phone",
        "email",
        "latitude",
        "longitude",
        "images",
        "rating_avg",
        "rating_count",
        "reviews",
        "verification",
        "services",
    } == set(body)
    assert body["id"] == "prv-salon-los-guaduales"
    assert body["name"] == "Salón Los Guaduales"
    assert body["categories"] == ["espacio"]
    assert body["description"].strip()
    assert body["neighborhood"] == "Ciudad Jardín"
    assert body["municipality"] == "Cali"
    assert body["phone"].strip() and body["email"].strip()
    assert body["verification"]["status"] == "verificado"
    assert body["verification"]["checks"]
    expected_checks = session.execute(
        text(
            "select check_type, checked_on from provider_verifications "
            "where provider_id = :provider_id order by checked_on, id"
        ),
        {"provider_id": body["id"]},
    ).all()
    assert [(check["type"], check["date"]) for check in body["verification"]["checks"]] == [
        (check.check_type, str(check.checked_on)) for check in expected_checks
    ]
    assert body["services"]
    expected_services = session.execute(
        text(
            "select id, name, category, description, price_model, base_price_cop, "
            "min_guests, max_guests, level from services "
            "where provider_id = :provider_id order by category, id"
        ),
        {"provider_id": body["id"]},
    ).all()
    assert len(body["services"]) == len(expected_services)
    for service, expected in zip(body["services"], expected_services, strict=True):
        assert set(service) == {
            "id",
            "name",
            "category",
            "description",
            "price_model",
            "unit_price_cop",
            "min_guests",
            "max_guests",
            "level",
        }
        assert service == {
            "id": expected.id,
            "name": expected.name,
            "category": expected.category,
            "description": expected.description,
            "price_model": expected.price_model,
            "unit_price_cop": expected.base_price_cop,
            "min_guests": expected.min_guests,
            "max_guests": expected.max_guests,
            "level": expected.level,
        }
        assert service["description"].strip()
        assert service["unit_price_cop"] > 0
        assert service["min_guests"] <= service["max_guests"]


def test_provider_without_verification_checks_is_in_review(client, session):
    load_seed(session)

    response = client.get("/api/v1/providers/prv-terraza-san-antonio")

    assert response.status_code == 200
    verification = response.json()["verification"]
    assert verification == {"status": "en_revision", "checks": []}
    assert verification["status"] != "verificado"


def test_provider_detail_status_is_verified_only_when_checks_exist(client, session):
    load_seed(session)
    provider_ids = session.execute(text("select id from providers order by id")).scalars().all()

    for provider_id in provider_ids:
        response = client.get(f"/api/v1/providers/{provider_id}")

        assert response.status_code == 200
        verification = response.json()["verification"]
        if verification["checks"]:
            assert verification["status"] == "verificado"
        else:
            assert verification["status"] == "en_revision"


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
    expected_rating, expected_count = session.execute(
        text("select round(avg(rating), 1), count(*) from provider_reviews where provider_id = :provider_id"),
        {"provider_id": "prv-salon-los-guaduales"},
    ).one()
    assert body["rating_avg"] == expected_rating == 4.7
    assert body["rating_count"] == expected_count == 3
    assert len(body["reviews"]) <= 5
    assert all(
        review["author_name"] and 1 <= review["rating"] <= 5 and review["comment"]
        for review in body["reviews"]
    )


def test_provider_detail_rounds_review_average_to_one_decimal(client, session):
    load_seed(session)
    session.execute(
        text("update provider_reviews set rating = 4 where provider_id = :provider_id"),
        {"provider_id": "prv-salon-los-guaduales"},
    )
    session.execute(
        text(
            "update provider_reviews set rating = 5 where id = "
            "(select id from provider_reviews where provider_id = :provider_id "
            "order by id limit 1)"
        ),
        {"provider_id": "prv-salon-los-guaduales"},
    )
    session.commit()

    response = client.get("/api/v1/providers/prv-salon-los-guaduales")

    assert response.status_code == 200
    body = response.json()
    expected_rating = session.execute(
        text("select round(avg(rating), 1) from provider_reviews where provider_id = :provider_id"),
        {"provider_id": "prv-salon-los-guaduales"},
    ).scalar_one()
    assert expected_rating == 4.3
    assert body["rating_avg"] == expected_rating


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
    today = date.today()
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
                "reviewed_on": today,
            },
            {
                "id": str(uuid.uuid4()),
                "provider_id": "prv-salon-los-guaduales",
                "author_name": "Reseña siguiente",
                "rating": 4,
                "comment": "Reseña de ejemplo",
                "reviewed_on": today - timedelta(days=1),
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
    assert review_dates[:2] == [
        today.isoformat(),
        (today - timedelta(days=1)).isoformat(),
    ]
    expected_reviews = session.execute(
        text(
            "select author_name, rating, comment, reviewed_on from provider_reviews "
            "where provider_id = :provider_id order by reviewed_on desc, id asc limit 5"
        ),
        {"provider_id": "prv-salon-los-guaduales"},
    ).all()
    assert body["reviews"] == [
        {
            "author_name": review.author_name,
            "rating": review.rating,
            "comment": review.comment,
            "reviewed_on": str(review.reviewed_on),
        }
        for review in expected_reviews
    ]
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
