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

## Documentación de la API

En desarrollo, abre `http://localhost:8000/docs` para explorar y probar los endpoints.
La especificación OpenAPI está disponible en `http://localhost:8000/openapi.json`.
En producción, la interfaz `/docs` está deshabilitada, pero la especificación JSON se
puede consultar en `https://<servicio>.onrender.com/openapi.json`.

Todos los endpoints usan el prefijo `/api/v1`. Entre los principales:

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/v1/recommendations` | Genera paquetes sugeridos a partir del presupuesto. |
| `POST` | `/api/v1/quotes` | Calcula una cotización desde los identificadores de servicio seleccionados. |
| `POST` | `/api/v1/reservations` | Revalida el total y registra una reserva desde los servicios seleccionados. |
| `POST` | `/api/v1/payments` | Procesa un pago simulado de una reserva. |
| `GET` | `/api/v1/reservations/{code}` | Consulta el estado y resumen de una reserva. |

El contrato completo —parámetros, cuerpos, respuestas y errores— está en
[`docs/20261105_SAD_EU.md`, §7.1](docs/20261105_SAD_EU.md#71-contrato-de-la-api).

## CI

GitHub Actions ejecuta `make check` en cada pull request y en los cambios a `main`.
El workflow usa Python 3.12 e instala las dependencias de desarrollo antes de validar.

## Despliegue manual en Render

1. En Render, crea un Blueprint desde este repositorio y selecciona `render.yaml`.
   El servicio web ejecuta `alembic upgrade head` antes de iniciar FastAPI y comprueba
   `/api/v1/health`.
2. Crea o selecciona una base de datos PostgreSQL y configura su URL de conexión como
   `DATABASE_URL` en el servicio. Usa la URL interna cuando la base esté en Render.
   No guardes credenciales ni la URL de conexión en Git.
3. Conserva `ENVIRONMENT=production` y `SEED_ON_STARTUP=true`, definidos en el Blueprint.
   Después del despliegue, comprueba `https://<servicio>.onrender.com/api/v1/health`;
   debe responder `{"status":"ok"}`. En producción, `/docs` no está habilitado.
4. En el entorno de compilación de la app Expo, define `EXPO_PUBLIC_API_BASE_URL` con
   el origen HTTPS asignado por Render, por ejemplo `https://<servicio>.onrender.com`.
   La app debe añadir el prefijo `/api/v1` a sus rutas. Vuelve a compilar la app para que
   Expo incluya el valor. Esta URL no es un secreto; no pongas credenciales en variables
   `EXPO_PUBLIC_*`.

Para desarrollo en un dispositivo físico, usa la IP local del computador en
`EXPO_PUBLIC_API_BASE_URL` (por ejemplo `http://192.168.x.x:8000`), no `localhost`.
Usa HTTP solo en desarrollo local.

La creación del servicio, la base de datos y la URL real dependen de la cuenta y del
proyecto de Render. Este repositorio no contiene el código de la app Expo; su variable
de entorno debe configurarse en el repositorio o servicio de compilación móvil.
