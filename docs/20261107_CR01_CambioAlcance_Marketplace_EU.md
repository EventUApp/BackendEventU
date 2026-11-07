# Solicitud de cambio CR-01 — EventU como marketplace de servicios para eventos

| Campo | Valor |
|---|---|
| Proyecto | EventU (EU) |
| Fecha | 7 de noviembre de 2026 |
| Solicita | David Enciso |
| Estado | **Borrador para aprobación del equipo.** Todavía no modifica el SRS, el backlog, el SAD ni la base de datos |
| Referencia de diseño | Booking, Trivago y TripAdvisor: buscar, comparar en lista y mapa, abrir la ficha, reservar |

## 1. Decisiones tomadas

| Tema | Decisión |
|---|---|
| Recomendador de paquetes | Se conserva como **atajo** («Arma mi evento por presupuesto»). La entrada principal pasa a ser el marketplace |
| Flujo de reserva | Buscar → resultados → ficha → «Mi evento» (carrito de servicios) → datos del cliente → pago simulado → confirmación |
| Elementos incluidos | Fotos y galería por proveedor; filtros y orden; vista de mapa |
| Elementos excluidos de este cambio | Reseñas escritas por usuarios, cuentas de usuario, disponibilidad por fecha y pago real (siguen como en el SRS) |

Supuesto mío, para que lo confirmes: las **calificaciones y reseñas** se muestran en modo lectura con datos de ejemplo del seed, porque sin ellas la tarjeta no se parece a las de TripAdvisor. No se pueden escribir reseñas en el MVP.

## 2. Flujo y pantallas (de 7 a 10 pantallas)

```
Inicio (buscador + rubros + destacados + atajo por presupuesto)
   ├─ Resultados (lista) ⇄ Resultados (mapa)  ── filtros y orden
   │        └─ Ficha del proveedor (galería, calificación, servicios, ubicación)
   │                 └─ «Agregar a mi evento»
   ├─ Mi evento (carrito: servicios por rubro, total, presupuesto opcional)
   │        └─ Datos del cliente → Pago simulado → Confirmación
   └─ Atajo: Presupuesto → 3 paquetes → Detalle → «Elegir» (carga el paquete en Mi evento)
```

Cambio clave: **todo camino termina en «Mi evento»**. Así el backend de reservas y pagos no cambia: una reserva sigue siendo una lista de servicios con su precio y total. El paquete recomendado pasa a ser una forma rápida de llenar el carrito.

## 3. Impacto en las historias de usuario

Se conservan los 11 ID actuales; se agregan 3 nuevos. IDs nuevos siguen el consecutivo continuo del backlog.

| ID | Cambio | Resumen |
|---|---|---|
| HU_EU_01_12 | **Nueva** | Inicio tipo marketplace |
| HU_EU_02_13 | **Nueva** | Mi evento (carrito de servicios) |
| HU_EU_03_14 | **Nueva** | Vista de mapa de resultados |
| HU_EU_01_01 | Modificada | Pasa a ser el formulario del atajo por presupuesto; se abre desde el Inicio |
| HU_EU_02_05 | Modificada | De «Catálogo» a «Resultados» con tarjetas, filtros ampliados y orden |
| HU_EU_02_08 | Modificada | La ficha agrega galería, calificación, ubicación y botón «Agregar a mi evento» |
| HU_EU_02_06 | Modificada | El ajuste del paquete ocurre dentro de «Mi evento» |
| HU_EU_02_07 | Baja de prioridad | Comparar paquetes pasa de Must a **Could** |
| HU_EU_03_09 | Modificada | La reserva se crea desde «Mi evento», no desde un paquete |
| HU_EU_01_02, 01_03, 01_04, 03_10, 03_11 | Sin cambio de fondo | Solo se actualizan referencias de pantalla (por ejemplo, la confirmación ofrece «Volver al inicio») |

### HU_EU_01_12 — Inicio tipo marketplace (Sprint 1)

**Historia.** Yo como Organizador, quiero una pantalla de inicio con buscador, categorías y proveedores destacados, para encontrar servicios para mi evento como en una app de reservas.

1. **Dónde:** pantalla 'Inicio', primera pantalla de la app.
2. **Campos:**
   - 2.1 Buscador: tipo de evento (lista: 'Cumpleaños', 'Boda', 'XV años'), fecha del evento (selector), número de invitados (entero) y botón 'Buscar'.
   - 2.2 Categorías: espacio, alimentación, decoración y entretenimiento, como accesos con ícono.
   - 2.3 Sección 'Destacados': hasta 6 proveedores con foto, nombre, calificación y precio 'Desde'.
   - 2.4 Acceso 'Arma mi evento por presupuesto' (HU_EU_01_01).
   - 2.5 Acceso 'Mi evento' con el número de servicios agregados.
3. **Validación:**
   - 3.1 Tipo de evento sin seleccionar: 'Seleccione el tipo de evento.'
   - 3.2 Invitados fuera de 1 a 500 (Propuesto): 'Ingrese un número de invitados entre 1 y 500.'
   - 3.3 Fecha, si se ingresa, no posterior a hoy: 'Seleccione una fecha posterior a hoy.' La fecha es opcional en la búsqueda y obligatoria al reservar.
4. **Restricción:** no se pide registro ni contraseña; las categorías y destacados no requieren llenar el buscador; la búsqueda no guarda datos en el servidor.
5. **Éxito:** 'Buscar' abre 'Resultados' con los criterios aplicados; tocar una categoría abre 'Resultados' filtrado por ese rubro; tocar un destacado abre su ficha (HU_EU_02_08).
6. **Fallo:** errores 3.1 a 3.3 junto al campo; si falla la conexión se aplica HU_EU_01_04; error inesperado: 'No fue posible completar la operación. Intente nuevamente.'

### HU_EU_02_05 — Resultados con tarjetas, filtros y orden (modificada, Sprint 2)

**Historia.** Yo como Organizador, quiero ver los proveedores en una lista de tarjetas que pueda filtrar y ordenar, para comparar opciones rápidamente.

1. **Dónde:** pantalla 'Resultados', abierta desde 'Inicio'; endpoint de listado de proveedores del API.
2. **Campos:**
   - 2.1 Tarjeta por proveedor: foto principal, nombre, rubros, barrio y municipio, calificación (promedio y número de reseñas), insignia 'Verificado' si aplica y precio 'Desde' en COP.
   - 2.2 Filtros: rubro, tipo de evento, rango de precio (mínimo y máximo opcionales, enteros), calificación mínima (3, 4 o 4,5) y solo verificados.
   - 2.3 Orden: 'Recomendados', 'Menor precio', 'Mayor precio', 'Mejor calificados'.
   - 2.4 Contador 'N resultados' y acción 'Limpiar filtros'.
   - 2.5 Conmutador 'Lista / Mapa' (HU_EU_03_14).
3. **Validación:**
   - 3.1 Precio mínimo mayor que el máximo: 'El precio mínimo no puede ser mayor que el máximo.'
   - 3.2 Los campos de precio solo aceptan enteros.
   - 3.3 Si hay número de invitados en la búsqueda, solo se listan proveedores con al menos un servicio cuya capacidad lo cubra.
4. **Restricción:** no se listan proveedores que no cumplan los filtros; el precio 'Desde' es el menor precio entre sus servicios elegibles, calculado en el servidor; el orden es determinista (empate: menor identificador, Propuesto); la app no edita el catálogo.
5. **Éxito:** la lista se actualiza con filtros y orden; tocar una tarjeta abre la ficha (HU_EU_02_08); la lista carga por páginas de 10 (Propuesto).
6. **Fallo:** sin resultados: 'No encontramos proveedores con esos filtros.' con 'Limpiar filtros'; conexión: HU_EU_01_04; error inesperado: 'No fue posible completar la operación. Intente nuevamente.'

### HU_EU_02_08 — Ficha del proveedor con galería y calificación (modificada, Sprint 2)

**Historia.** Yo como Organizador, quiero ver la ficha completa de un proveedor con fotos, calificación, ubicación y servicios, para decidir si lo agrego a mi evento.

1. **Dónde:** pantalla 'Ficha del proveedor', abierta desde 'Inicio', 'Resultados', 'Mapa' o 'Mi evento'; endpoint de proveedor del API.
2. **Campos:**
   - 2.1 Galería de 3 a 6 fotos desplazables, con contador 'n/N'.
   - 2.2 Nombre, rubros, descripción del alcance, barrio y municipio.
   - 2.3 Calificación promedio y número de reseñas; lista de hasta 5 reseñas de ejemplo con autor, fecha, puntaje y comentario.
   - 2.4 Estado de verificación ('Verificado' o 'En revisión') y comprobaciones con tipo y fecha.
   - 2.5 Contacto: teléfono y correo.
   - 2.6 Lista de servicios con nombre, descripción, capacidad, precio y botón 'Agregar a mi evento'.
   - 2.7 Mapa pequeño con la ubicación aproximada (HU_EU_03_14).
3. **Validación:**
   - 3.1 'Verificado' solo si existe al menos una comprobación registrada.
   - 3.2 Un servicio no se puede agregar si su capacidad no cubre el número de invitados de la búsqueda: 'Este servicio no admite ese número de invitados.'
   - 3.3 No se puede agregar un segundo servicio de espacio, alimentación o decoración sin reemplazar el primero (Propuesto): 'Ya tiene un servicio de este rubro. ¿Desea reemplazarlo?'
4. **Restricción:** la ficha no promete el cumplimiento del servicio; las reseñas son de solo lectura; el estado 'Verificado' nunca aparece sin comprobaciones; la app no edita la ficha.
5. **Éxito:** 'Agregar a mi evento' actualiza el contador de 'Mi evento' sin salir de la ficha; en proveedores verificados aparece 'La verificación confirma los datos del proveedor, pero no garantiza el cumplimiento del servicio.'
6. **Fallo:** proveedor inexistente: 'No encontramos este proveedor.'; foto que no carga: se muestra un recuadro neutro, sin error; conexión: HU_EU_01_04; error inesperado: 'No fue posible completar la operación. Intente nuevamente.'

### HU_EU_02_13 — Mi evento, el carrito de servicios (Sprint 2)

**Historia.** Yo como Organizador, quiero reunir los servicios elegidos en «Mi evento» con su total, para revisar y ajustar antes de reservar.

1. **Dónde:** pantalla 'Mi evento', abierta desde cualquier pantalla; reemplaza a 'Detalle del paquete' como lugar de ajuste (HU_EU_02_06).
2. **Campos:**
   - 2.1 Servicios agrupados por rubro, con proveedor, precio y acciones 'Cambiar' y 'Quitar'.
   - 2.2 Total en COP, recalculado en cada cambio.
   - 2.3 Presupuesto opcional; si se ingresó, muestra el restante.
   - 2.4 Tipo de evento, invitados y fecha (editables).
   - 2.5 Botón 'Continuar a reservar' (HU_EU_03_09).
3. **Validación:**
   - 3.1 'Continuar' exige al menos espacio, alimentación y decoración (RN-03).
   - 3.2 Con presupuesto ingresado, no se permite un cambio que haga el total mayor: 'Ese cambio supera su presupuesto. Elija otra opción.'
   - 3.3 Si cambian los invitados, se revalida cada servicio y se avisa de los que dejan de ser elegibles.
4. **Restricción:** el servidor es la fuente de verdad del total (ADR-09); el carrito vive en la app y no requiere cuenta; el total mostrado nunca se envía como verdad al reservar.
5. **Éxito:** al elegir un paquete del atajo, sus servicios se cargan aquí; cambios y totales se actualizan en la misma pantalla.
6. **Fallo:** carrito vacío: 'Aún no ha agregado servicios.' con acceso a 'Inicio'; conexión: HU_EU_01_04; error inesperado: 'No fue posible completar la operación. Intente nuevamente.'

### HU_EU_03_14 — Vista de mapa de resultados (Sprint 3, Could)

**Historia.** Yo como Organizador, quiero ver los proveedores en un mapa, para elegir los que quedan cerca del lugar de mi evento.

1. **Dónde:** pantalla 'Resultados' en modo 'Mapa'.
2. **Campos:** 2.1 marcadores con el precio 'Desde'; 2.2 tarjeta emergente con foto, nombre, calificación y botón 'Ver ficha'; 2.3 filtros y orden compartidos con la lista; 2.4 botón 'Buscar en esta zona'.
3. **Validación:** 3.1 solo se dibujan proveedores con coordenadas válidas; 3.2 si el permiso de ubicación se niega, el mapa se centra en Cali y no se vuelve a pedir en la sesión.
4. **Restricción:** no se usa la ubicación del usuario para guardar datos; las coordenadas son aproximadas, nunca una dirección exacta.
5. **Éxito:** mover el mapa y 'Buscar en esta zona' actualiza los resultados; tocar un marcador abre la tarjeta y luego la ficha.
6. **Fallo:** si el mapa no carga: 'No fue posible mostrar el mapa. Use la vista de lista.' y se vuelve a la lista; conexión: HU_EU_01_04.

### HU_EU_03_09 y HU_EU_01_01 (cambios de fondo)

- **HU_EU_03_09:** el origen de la reserva es 'Mi evento'. Se elimina «paquete elegido» del resumen; se muestra la lista de servicios. La fecha del evento sigue obligatoria.
- **HU_EU_01_01:** el formulario por presupuesto se abre desde 'Inicio', y 'Ver paquetes' mantiene su comportamiento. Los datos que ya ingresó el usuario en el buscador se precargan (tipo de evento, invitados).

## 4. Impacto en el backend y la base de datos

**API (se agrega a `/api/v1`; lo existente no se rompe):**

| Endpoint | Uso |
|---|---|
| `GET /providers` | Listado con filtros (`category`, `event_type`, `min_price`, `max_price`, `min_rating`, `verified`, `guests`, `bbox`), orden (`sort`) y paginación (`page`, `page_size`) |
| `GET /providers/{id}` | Se amplía: fotos, calificación, reseñas, coordenadas |
| `GET /home` | Destacados y conteo por rubro (se puede reemplazar por `GET /providers?featured=true`) |
| `POST /reservations` | Pasa a recibir `service_ids` + datos del cliente; el servidor recalcula el total (ya era así) |

**Tablas nuevas o modificadas (la migración inicial 0001 se regeneró como v2; nada estaba desplegado, así que quien tenga una base local v1 debe recrearla):**

| Objeto | Cambio |
|---|---|
| `providers` | Agregar `latitude` y `longitude` (decimal, nulos permitidos), `featured` (booleano) |
| `provider_images` | **Nueva:** `id`, `provider_id`, `url`, `position`, `alt_text` |
| `provider_reviews` | **Nueva:** `id`, `provider_id`, `author_name`, `rating` (1 a 5, CHECK), `comment`, `reviewed_on`. Solo datos del seed |
| `v_providers` | Agrega `rating_avg`, `rating_count` y `price_from_cop` derivados (sin columnas que puedan contradecir los datos, igual que `verification_status`) |

**Algoritmo recomendador:** no cambia (SAD §6). Sigue siendo una función pura.

## 5. Impacto en el frontend móvil

- Navegación: pestañas inferiores **Inicio · Resultados · Mi evento · Reservas** (la última abre 'Consultar reserva').
- Componentes nuevos: `ProviderCard`, `PhotoGallery`, `RatingStars`, `FilterSheet`, `SortSheet`, `CartBadge`, `MapView` (con `react-native-maps` en Expo).
- Estado: un contexto `EventCart` con servicios, tipo de evento, invitados y fecha (reemplaza al estado del paquete elegido).
- Las pantallas de paquetes (HU_EU_01_02, 02_07) se mantienen detrás del atajo; el ajuste de HU_EU_02_06 se hace dentro de «Mi evento».

## 6. Impacto en esfuerzo y plan (estimación propuesta, puntos Fibonacci)

*Estimación inicial del cambio (borrador). El desglose final por tareas está en el Backlog Extendido v2: 57 tareas, 160 SP en total.*

| Trabajo | Rol | SP |
|---|---|---|
| HU_EU_01_12 Inicio: pantalla, `GET /home`, prueba | Frontend / Backend / Pruebas | 3 + 2 + 1 |
| HU_EU_02_05 modificada: tarjetas, filtros ampliados, orden | Frontend / Backend / Pruebas | +3 + 3 + 1 |
| HU_EU_02_08 modificada: galería, reseñas, agregar a evento | Frontend / Backend / BD | +5 + 2 + 2 |
| HU_EU_02_13 Mi evento: contexto, pantalla, revalidación | Frontend / Backend / Pruebas | 5 + 2 + 2 |
| HU_EU_03_14 Mapa | Frontend / Backend | 5 + 1 |
| Datos: fotos, coordenadas y reseñas de ejemplo para los proveedores | Datos/Contenido | 5 |
| Migración 0001 v2 y seed ampliado | Base de datos | 3 |
| **Total adicional** | | **≈ 48 SP (estimación inicial; el backlog v2 final suma 160 SP en total)** |

**Esto no cabe.** El plan anterior usaba 107 SP contra una capacidad de referencia de 108 (3 sprints × 36). Con el alcance completo del marketplace el backlog v2 suma **160 SP** (Sprint 1: 50, Sprint 2: 69, Sprint 3: 41): Must 111, Should 34, Could 15. Por responsable: David 85, Jean Paul 64, Yenny 11. Excede la capacidad en ≈ 52 SP y David carga más del doble de lo propuesto.

Corte propuesto, en este orden: `HU_EU_03_14` (mapa), `HU_EU_02_07` (comparar), `HU_EU_02_16` (galería y reseñas), `HU_EU_01_03` y `HU_EU_01_02` (paquetes). **El equipo tiene que decidir** qué se recorta, si se agrega un cuarto día de colchón o si Juan Manuel asume tareas (P-02).

## 7. Qué documentos habría que regenerar si se aprueba

| Documento | Cambio |
|---|---|
| SRS | Nuevos RF del módulo de exploración (RF-EXP), RN de carrito y orden, supuesto S-0x de reseñas solo lectura, P-0x de coordenadas y fotos |
| Backlog (PB) y Backlog Extendido (TSV y hoja de Google) | 14 HU, tareas nuevas, estimaciones, MoSCoW y registro de pendientes (PB-10 en adelante) |
| SAD | ADR nuevo (carrito en el cliente, servidor como verdad del total), contrato de la API ampliado, estructura de carpetas del front |
| BD | Migración 0002, `schema.sql`, `seed.sql`, `seed.json`, diagrama |
| Repos (`eventu-api`, `eventu-app`) | Prompts por tarea de las HU nuevas y modificadas; `CLAUDE.md` con las pantallas nuevas |
| Guía paso a paso | Nuevo orden de tareas por sprint |

## 8. Pendientes que son del equipo

| ID | Pendiente | Quién decide |
|---|---|---|
| CR-P1 | Aprobar el cambio y el recorte de la sección 6 | Equipo y profesor |
| CR-P2 | Confirmar que las reseñas son de solo lectura con datos de ejemplo | Equipo |
| CR-P3 | Origen de las fotos (banco libre de derechos o fotos reales de los proveedores) y su licencia | Yenny |
| CR-P4 | Coordenadas de cada proveedor de ejemplo | Yenny |
| CR-P5 | Rol de Juan Manuel (arrastra P-02) | Equipo |
