from sqlalchemy import text

from seed.load import load_seed


def test_home_returns_categories_and_featured_provider_summary(client, session):
    load_seed(session)

    r = client.get("/api/v1/home")

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"categories", "featured"}
    assert len(body["categories"]) == 4
    assert [item["category"] for item in body["categories"]] == [
        "espacio",
        "alimentacion",
        "decoracion",
        "entretenimiento",
    ]
    expected_counts = dict(
        session.execute(
            text("select category, count(distinct provider_id) from services group by category")
        ).all()
    )
    assert {item["category"]: item["count"] for item in body["categories"]} == expected_counts
    assert len(body["featured"]) <= 6
    expected_featured_ids = (
        session.execute(
            text(
                "select id from v_providers where featured = 1 "
                "order by case when rating_avg is null then 1 else 0 end, rating_avg desc, id asc limit 6"
            )
        )
        .scalars()
        .all()
    )
    assert [item["id"] for item in body["featured"]] == expected_featured_ids
    first = body["featured"][0]
    assert first["featured"] is True
    assert first["cover_url"].startswith("https://")
    assert "price_from_cop" in first
    assert "rating_avg" in first
    assert "verification_status" in first
    for item in body["featured"]:
        expected_price = session.execute(
            text(
                """
                select min(case when price_model = 'fijo'
                                then base_price_cop
                                else base_price_cop * min_guests end)
                from services
                where provider_id = :provider_id
                """
            ),
            {"provider_id": item["id"]},
        ).scalar_one()
        assert item["price_from_cop"] == expected_price


def test_home_featured_order_uses_identifier_to_break_rating_ties(client, session):
    load_seed(session)
    provider_ids = (
        session.execute(text("select id from providers where featured = 1 order by id limit 2"))
        .scalars()
        .all()
    )
    assert len(provider_ids) == 2
    first_id, second_id = provider_ids
    session.execute(text("delete from provider_reviews"))
    session.execute(text("update providers set featured = 0"))
    session.execute(
        text("update providers set featured = 1 where id in (:first_id, :second_id)"),
        {"first_id": first_id, "second_id": second_id},
    )
    session.execute(
        text(
            "insert into provider_reviews "
            "(id, provider_id, author_name, rating, comment, reviewed_on) "
            "values (:id, :provider_id, :author_name, 5, 'Prueba', '2026-01-01')"
        ),
        [
            {"id": "00000000-0000-0000-0000-000000000001", "provider_id": first_id, "author_name": "A"},
            {"id": "00000000-0000-0000-0000-000000000002", "provider_id": second_id, "author_name": "B"},
            {"id": "00000000-0000-0000-0000-000000000003", "provider_id": second_id, "author_name": "C"},
        ],
    )
    session.commit()

    r = client.get("/api/v1/home")
    featured = r.json()["featured"]

    assert [item["id"] for item in featured] == [first_id, second_id]
    assert [item["rating_avg"] for item in featured] == [5.0, 5.0]
    assert [item["rating_count"] for item in featured] == [1, 2]


def test_home_returns_empty_categories_and_featured_without_catalog_data(client):
    response = client.get("/api/v1/home")

    assert response.status_code == 200
    assert response.json() == {"categories": [], "featured": []}
