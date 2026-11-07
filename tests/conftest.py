import os

# Base de datos aislada para las pruebas (antes de importar la app).
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["RATE_LIMIT_PER_MINUTE"] = "0"
os.environ["SEED_ON_STARTUP"] = "false"

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import StaticPool, create_engine, event  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402


def make_test_engine():  # type: ignore[no-untyped-def]
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _fk(dbapi_conn, _):  # type: ignore[no-untyped-def]
        dbapi_conn.execute("PRAGMA foreign_keys = ON")

    cfg = Config("alembic.ini")
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")
    return engine


@pytest.fixture()
def engine():  # type: ignore[no-untyped-def]
    return make_test_engine()


@pytest.fixture()
def session(engine) -> Iterator[Session]:  # type: ignore[no-untyped-def]
    with Session(engine) as s:
        yield s


@pytest.fixture()
def client(engine):  # type: ignore[no-untyped-def]
    from fastapi.testclient import TestClient

    from app.main import create_app
    from app.shared import db

    def _override() -> Iterator[Session]:
        with Session(engine) as s:
            yield s

    app = create_app()
    app.dependency_overrides[db.get_session] = _override
    return TestClient(app, raise_server_exceptions=False)
