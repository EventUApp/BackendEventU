# eventu-api

Backend de EventU (FastAPI). Lea `CLAUDE.md` y `docs/`.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # DATABASE_URL vacío = SQLite local
make migrate && make seed
make run                      # http://localhost:8000/docs
make check
```

Despliegue en Render: ver `render.yaml` (Propuesto). Pegue `DATABASE_URL` en el panel, no en el repo.
