from alembic import context

import app.catalogo.models  # noqa: F401  (registra los modelos)
import app.pagos.models  # noqa: F401
import app.reservas.models  # noqa: F401
from app.shared.db import Base, make_engine

target_metadata = Base.metadata


def run_migrations_online() -> None:
    # Una conexión ya abierta (p. ej. en pruebas) se puede pasar con config.attributes["connection"].
    connection = context.config.attributes.get("connection")
    if connection is not None:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = make_engine()
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
