-- =====================================================================
-- EventU (EU) - schema.sql  (PostgreSQL 16; compatible con SQLite salvo la
-- sección final "SOLO POSTGRESQL")
-- Convenciones: nombres en inglés snake_case; dinero en COP enteros (*_cop);
-- enumeraciones con CHECK (portables); sin columnas de tarjeta.
-- Diferencias para SQLite: ver la sección 8 del documento (UUID se genera en
-- la aplicación; se omite la sección "SOLO POSTGRESQL").
-- =====================================================================

-- ---------------------------------------------------------------------
-- Catálogo: proveedores
-- ---------------------------------------------------------------------
CREATE TABLE providers (
    id            TEXT PRIMARY KEY CHECK (length(id) BETWEEN 3 AND 80),   -- slug legible
    name          TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 100),
    description   TEXT NOT NULL,                                          -- alcance del servicio (RF-PRO-02)
    neighborhood  TEXT NOT NULL,                                          -- barrio (RF-PRO-03)
    municipality  TEXT NOT NULL,                                          -- municipio (RF-PRO-03)
    phone         TEXT NOT NULL,                                          -- contacto (RF-PRO-04)
    email         TEXT NOT NULL,                                          -- contacto (RF-PRO-04)
    latitude      DOUBLE PRECISION CHECK (latitude  BETWEEN -90  AND 90),  -- ubicación aproximada (RF-EXP-09)
    longitude     DOUBLE PRECISION CHECK (longitude BETWEEN -180 AND 180),
    featured      BOOLEAN NOT NULL DEFAULT FALSE,                         -- aparece en «Destacados» del Inicio (RF-EXP-02)
    created_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_providers_geo CHECK ((latitude IS NULL) = (longitude IS NULL))   -- ambas o ninguna
);

-- Galería de fotos del proveedor (RF-EXP-05). La URL apunta a un banco de
-- imágenes; la app no guarda archivos.
CREATE TABLE provider_images (
    id           UUID PRIMARY KEY,                                        -- generado por la app (uuid4)
    provider_id  TEXT NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    url          TEXT NOT NULL CHECK (url LIKE 'https://%'),
    alt_text     TEXT NOT NULL,                                           -- texto alternativo (accesibilidad)
    position     INTEGER NOT NULL CHECK (position >= 1),                  -- 1 = foto principal
    CONSTRAINT ux_provider_images_pos UNIQUE (provider_id, position)
);

-- Reseñas de ejemplo, solo lectura en el MVP (RF-EXP-06, supuesto S-04).
CREATE TABLE provider_reviews (
    id           UUID PRIMARY KEY,                                        -- generado por la app (uuid4)
    provider_id  TEXT NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    author_name  TEXT NOT NULL CHECK (length(author_name) BETWEEN 1 AND 60),
    rating       INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment      TEXT NOT NULL CHECK (length(comment) BETWEEN 1 AND 500),
    reviewed_on  DATE NOT NULL
);

-- Comprobaciones de verificación (RN-07): un proveedor es "verificado" si
-- tiene al menos una fila aquí; de lo contrario está "en revisión".
CREATE TABLE provider_verifications (
    id           UUID PRIMARY KEY,                                        -- generado por la app (uuid4)
    provider_id  TEXT NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    check_type   TEXT NOT NULL
                 CHECK (check_type IN ('identidad','registro_mercantil','visita','referencias')),
    checked_on   DATE NOT NULL,
    notes        TEXT NOT NULL                                            -- constancia documentada
);

-- Estado de verificación derivado (evita guardar un estado que pueda
-- contradecir las comprobaciones).
-- La calificación también se deriva de las reseñas (no se guarda como columna).
CREATE VIEW v_providers AS
SELECT p.*,
       CASE WHEN EXISTS (SELECT 1 FROM provider_verifications v WHERE v.provider_id = p.id)
            THEN 'verificado' ELSE 'en_revision' END AS verification_status,
       (SELECT ROUND(AVG(r.rating), 1) FROM provider_reviews r WHERE r.provider_id = p.id) AS rating_avg,
       (SELECT COUNT(*) FROM provider_reviews r WHERE r.provider_id = p.id)                AS rating_count
FROM providers p;

-- ---------------------------------------------------------------------
-- Catálogo: servicios
-- ---------------------------------------------------------------------
CREATE TABLE services (
    id              TEXT PRIMARY KEY CHECK (length(id) BETWEEN 3 AND 120),
    provider_id     TEXT NOT NULL REFERENCES providers(id) ON DELETE RESTRICT,
    category        TEXT NOT NULL
                    CHECK (category IN ('espacio','alimentacion','decoracion','entretenimiento')),
    level           TEXT NOT NULL                                         -- modalidad sugerida (RN-13)
                    CHECK (level IN ('ahorro','equilibrado','premium')),
    name            TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 120),
    description     TEXT NOT NULL,
    price_model     TEXT NOT NULL CHECK (price_model IN ('fijo','por_invitado')),
    base_price_cop  INTEGER NOT NULL CHECK (base_price_cop > 0),          -- RN-04
    min_guests      INTEGER NOT NULL CHECK (min_guests >= 1),
    max_guests      INTEGER NOT NULL,
    CONSTRAINT ck_services_capacity CHECK (max_guests >= min_guests)      -- RN-14
);

-- Tipos de evento que admite cada servicio (RN-14).
CREATE TABLE service_event_types (
    service_id  TEXT NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    event_type  TEXT NOT NULL CHECK (event_type IN ('cumpleanos','boda','xv')),
    PRIMARY KEY (service_id, event_type)
);

-- ---------------------------------------------------------------------
-- Reservas
-- ---------------------------------------------------------------------
CREATE TABLE reservations (
    id              UUID PRIMARY KEY,                                     -- generado por la app (uuid4)
    code            TEXT NOT NULL UNIQUE                                  -- RN-18: 'EU-' + 6 caracteres
                    CHECK (length(code) = 9 AND substr(code, 1, 3) = 'EU-'),
    status          TEXT NOT NULL DEFAULT 'creada'
                    CHECK (status IN ('creada','pagada','pago_rechazado','cancelada')),
    event_type      TEXT NOT NULL CHECK (event_type IN ('cumpleanos','boda','xv')),
    guests          INTEGER NOT NULL CHECK (guests > 0),                  -- rango 1..500 lo valida la app (RN-19, Propuesto)
    budget_cop      INTEGER CHECK (budget_cop > 0),                       -- opcional en «Mi evento» (RN-22); rango lo valida la app (RN-19, Propuesto)
    modality        TEXT NOT NULL                                         -- origen de la selección (RN-21)
                    CHECK (modality IN ('ahorro','equilibrado','premium','personalizado')),
    total_cop       INTEGER NOT NULL CHECK (total_cop >= 0),              -- = suma de reservation_items.cost_cop (RN-04)
    customer_name   TEXT NOT NULL CHECK (length(customer_name) BETWEEN 1 AND 100),
    customer_email  TEXT NOT NULL CHECK (length(customer_email) BETWEEN 3 AND 254),
    customer_phone  TEXT NOT NULL CHECK (length(customer_phone) > 0),     -- formato lo valida la app (Propuesto)
    event_date      DATE NOT NULL,                                        -- posterior a hoy: lo valida la app (RN-20)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_reservations_budget CHECK (budget_cop IS NULL OR total_cop <= budget_cop)   -- RN-01
);

-- Instantánea de los servicios y precios al reservar (RN-08). Un servicio
-- por rubro y reserva.
CREATE TABLE reservation_items (
    reservation_id  UUID NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
    category        TEXT NOT NULL
                    CHECK (category IN ('espacio','alimentacion','decoracion','entretenimiento')),
    service_id      TEXT REFERENCES services(id) ON DELETE SET NULL,      -- la copia sobrevive si el servicio se retira
    service_name    TEXT NOT NULL,
    provider_name   TEXT NOT NULL,
    price_model     TEXT NOT NULL CHECK (price_model IN ('fijo','por_invitado')),
    unit_price_cop  INTEGER NOT NULL CHECK (unit_price_cop > 0),
    cost_cop        INTEGER NOT NULL CHECK (cost_cop >= 0),               -- RN-15: fijo = unit; por_invitado = unit x invitados
    PRIMARY KEY (reservation_id, category)
);

-- ---------------------------------------------------------------------
-- Pagos simulados (RN-09): nunca datos de tarjeta
-- ---------------------------------------------------------------------
CREATE TABLE payments (
    id              UUID PRIMARY KEY,                                     -- generado por la app (uuid4)
    reservation_id  UUID NOT NULL REFERENCES reservations(id) ON DELETE RESTRICT,
    status          TEXT NOT NULL CHECK (status IN ('aprobado','rechazado')),
    amount_cop      INTEGER NOT NULL CHECK (amount_cop > 0),
    reference       TEXT NOT NULL UNIQUE,                                 -- referencia simulada, p. ej. 'SIM-...'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- Índices (ver sección 5 del documento)
-- ---------------------------------------------------------------------
CREATE INDEX ix_services_category_level ON services (category, level);
CREATE INDEX ix_services_provider       ON services (provider_id);
CREATE INDEX ix_service_event_types_evt ON service_event_types (event_type, service_id);
CREATE INDEX ix_verifications_provider  ON provider_verifications (provider_id);
CREATE INDEX ix_reviews_provider        ON provider_reviews (provider_id);
CREATE INDEX ix_providers_geo           ON providers (latitude, longitude);
CREATE INDEX ix_providers_featured      ON providers (featured);
CREATE INDEX ix_payments_reservation    ON payments (reservation_id);
-- Un solo pago aprobado por reserva (RF-PAG-07): índice parcial (PostgreSQL y SQLite).
CREATE UNIQUE INDEX ux_payments_one_approved ON payments (reservation_id) WHERE status = 'aprobado';

