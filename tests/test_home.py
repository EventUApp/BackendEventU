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
    assert all(item["count"] > 0 for item in body["categories"])
    assert len(body["featured"]) == 6
    first = body["featured"][0]
    assert first["featured"] is True
    assert first["cover_url"].startswith("https://")
    assert "price_from_cop" in first
    assert "rating_avg" in first
    assert "verification_status" in first


def test_home_featured_order_breaks_rating_ties_by_id_not_review_count(client, session):
    load_seed(session)
    provider_ids = (
        session.execute(text("select id from providers where featured order by id limit 2")).scalars().all()
    )
    assert len(provider_ids) == 2
    first_id, second_id = provider_ids
    session.execute(text("delete from provider_reviews"))
    session.execute(text("update providers set featured = false"))
    session.execute(
        text("update providers set featured = true where id in (:first_id, :second_id)"),
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
