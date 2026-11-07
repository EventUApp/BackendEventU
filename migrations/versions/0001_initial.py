"""Esquema inicial de EventU, versión 2 con marketplace (docs/20261105_BD_BaseDatos_EU.md §8).

Revision ID: 0001
Revises:
"""

import re
from pathlib import Path

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def _statements(text: str, sep: str) -> list[str]:
    marker = "@@SPLIT@@"
    text = text.replace("-- @@", marker)
    text = re.sub(r"--[^\n]*", "", text)  # quita comentarios (algunos contienen ';')
    separator = marker if sep == "-- @@" else sep
    return [s.strip() for s in text.split(separator) if s.strip()]


def upgrade() -> None:
    bind = op.get_bind()
    schema = (SQL_DIR / "0001_schema.sql").read_text(encoding="utf-8")
    # El esquema portable no contiene ';' dentro de cadenas, por lo que se separa por ';'.
    for stmt in _statements(schema, ";"):
        bind.exec_driver_sql(stmt.replace("%", "%%"))  # psycopg interpreta %
    if bind.dialect.name == "postgresql":
        pg_only = (SQL_DIR / "0001_pg_only.sql").read_text(encoding="utf-8")
        for stmt in _statements(pg_only, "-- @@"):
            bind.exec_driver_sql(stmt.replace("%", "%%"))  # psycopg interpreta %


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        bind.exec_driver_sql("DROP FUNCTION IF EXISTS fn_check_reservation_total() CASCADE")
    for obj in (
        "DROP VIEW IF EXISTS v_providers",
        "DROP TABLE IF EXISTS payments",
        "DROP TABLE IF EXISTS reservation_items",
        "DROP TABLE IF EXISTS reservations",
        "DROP TABLE IF EXISTS service_event_types",
        "DROP TABLE IF EXISTS services",
        "DROP TABLE IF EXISTS provider_reviews",
        "DROP TABLE IF EXISTS provider_images",
        "DROP TABLE IF EXISTS provider_verifications",
        "DROP TABLE IF EXISTS providers",
    ):
        bind.exec_driver_sql(obj)
