# CLAUDE.md — eventu-api (backend de EventU)

API REST (FastAPI, Python 3.12) de EventU: convierte un presupuesto en tres paquetes de servicios para eventos en Cali y lleva el flujo hasta la reserva y el pago **simulado**. Equipo: David (backend y QA), Jean Paul (app móvil), Yenny (datos y contenido).

## Léase antes de programar (carpeta `docs/`)
- `20261105_SAD_EU.md`: arquitectura, algoritmo (§6) y contrato de la API (§7). **Manda sobre cualquier suposición.**
- `20261105_BD_BaseDatos_EU.md`: tablas, restricciones y consultas.
- `20261105_SRS_Requisitos_EU.md`: RF, RNF y reglas de negocio RN-xx.
- `20261105_PB_ProductBacklog_EU.md` y `..._PBS_ProductBacklogExtended_EU.tsv`: historias, criterios y tareas.
Los valores marcados «Propuesto» son simulados y se validan después: impleméntelos como constantes fáciles de cambiar, sin inventar otros.

## Comandos
- `make check` = ruff + mypy + pytest (debe estar en verde antes de cada PR).
- `make run` (puerto 8000), `make migrate`, `make seed`. Variables en `.env` (ver `.env.example`; nunca subir `.env`).

## Estructura y dependencias (SAD §8)
`app/<módulo>/` con `router.py → service.py → repository.py/models.py` y, solo en `recomendador`, `domain/` puro.
- `domain/` no importa FastAPI, SQLAlchemy ni otros módulos.
- `router.py` solo importa `service.py` y `schemas.py`; nunca repositorios ni modelos.
- `reservas` consulta el catálogo a través de `catalogo.service`; `pagos` consulta reservas a través de `reservas.service`.
- Errores de negocio: `raise AppError(code, message, status)`; el formato `{"error":{"code","message","fields"}}` ya está en `app/errors.py`.

## Reglas que no se rompen
1. **Ningún paquete supera el presupuesto** (RN-01). Todo total se calcula en el servidor.
2. **Dinero = entero en COP** (`*_cop`); nunca `float` ni `Decimal`. Use `app/shared/money.py`.
3. El cliente envía identificadores de servicio, **nunca precios**; el servidor recalcula desde el catálogo (ADR-09).
4. **Nunca guardar ni registrar datos de tarjeta** (número, vencimiento, CVV). Ni columnas, ni logs, ni cuerpos de petición en los registros (RNF-SEG-02).
5. Solo se persisten nombre, correo y teléfono como datos personales, y no van a los logs (RNF-SEG-05).
6. El recomendador es una **función pura y determinista**: misma entrada, misma salida; desempate por menor precio y luego menor id.
7. Rutas bajo `/api/v1`, JSON `snake_case`, códigos de error estables (SAD §7.2).
8. Pago simulado detrás de `PaymentGateway` (`app/pagos/gateway.py`); no llamar a pasarelas reales.
9. Cambios de esquema solo con una migración Alembic nueva (`0002_…` en adelante); `0001_schema` ya incluye el marketplace (versión 2) y no se edita.

## Cómo trabajar una historia
1. Lea la HU, sus criterios y sus tareas (`docs/`), y el endpoint en SAD §7.
2. Rama `hu/EU_<sprint>_<n>-<tema>`; **un PR pequeño por tarea** (`T_HU_…`).
3. Escriba primero las pruebas de los criterios de aceptación (incluido el fallo); luego el código.
4. Entregue cuando `make check` esté en verde, los criterios estén verificados, no haya secretos y la fila de `docs/bitacora-prompts.md` esté completa.
5. No toque archivos de otra HU ni cambie contratos del SAD sin avisar; si algo del SAD o del SRS no cuadra, dígalo en el PR y no lo resuelva en silencio.

## Mapa HU → dónde va el código
| HU | Módulo | Endpoint |
|---|---|---|
| 01_01, 01_02, 01_03 | `recomendador` (+ `domain/`) | `POST /recommendations` |
| 01_04 | transversal | errores uniformes, `/health` |
| 01_12 | `catalogo` | `GET /home` |
| 02_05, 02_15, 03_14 | `catalogo` | `GET /providers` (filtros, orden, paginación, `bbox`) |
| 02_08, 02_16 | `proveedores` | `GET /providers/{id}` (galería, calificación, reseñas) |
| 02_13, 02_06 | `recomendador` | `POST /quotes` (cotización de «Mi evento»; el servidor decide el total) |
| 03_09 | `reservas` | `POST /reservations` (modality `personalizado`), `POST /reservations/{code}/cancel` |
| 03_10 | `pagos` | `POST /payments` |
| 03_11 | `reservas` | `GET /reservations/{code}` |

## Flujo de Git (lo hace el agente al terminar cada tarea)
Aplica cuando el usuario pide implementar una tarea `T_HU_…` (por ejemplo desde `prompts/T_HU_EU_01_12_2.md`).

1. **Rama.** Antes de editar, mire la rama actual (`git branch --show-current`).
   - Nunca trabaje ni haga commit en `main`.
   - Cree la rama desde `main` actualizado (`git checkout main && git pull`) con el nombre `hu/EU_<sprint>_<n>_<k>-<tema>`: el identificador de la tarea sin el prefijo `T_HU_` y un tema corto en minúsculas, sin tildes, separado por guiones (máximo 4 palabras).
   - Ejemplos: `T_HU_EU_01_12_2` (GET /home) → `hu/EU_01_12_2-get-home`; `T_HU_EU_02_05_2` (pantalla Resultados) → `hu/EU_02_05_2-pantalla-resultados`.
   - Si ya está en una rama de esa misma tarea, sígala usando.
2. **Antes del commit.** Corra `make check`; debe estar en verde. Complete la fila de `docs/bitacora-prompts.md`. Compruebe con `git status --short` que solo cambiaron archivos de la tarea y que no hay `.env`, bases de datos, claves ni cachés.
3. **Commit.** Agregue solo los archivos de la tarea por nombre (no use `git add .` ni `git add -A`). Mensaje:
   `T_HU_EU_01_12_2: <qué se hizo en una línea, en español, en imperativo>`
   Un commit por tarea; si la tarea es grande, varios commits con el mismo prefijo.
4. **Push.** `git push -u origin <rama>`. Nunca haga push a `main`, nunca use `--force`.
5. **Pull Request.** Si `gh` está instalado y autenticado, abra el PR hacia `main` con `gh pr create`:
   - Título: `T_HU_EU_01_12_2: <descripción>`.
   - Descripción: criterios de aceptación con su estado, archivos cambiados, resultado de `make check`, supuestos y dudas abiertas.
   Si `gh` no está disponible, imprima el enlace o el texto sugerido del PR y diga que falta abrirlo a mano.
6. **No haga** merge, no borre ramas, no cambie la configuración de GitHub ni de Render. El merge lo hace David tras revisar.
7. Termine informando: nombre de la rama, hash del commit y URL del PR (si se creó).