# Especificación de Requisitos de Software (SRS) — EventU

## 1. Portada e información documental

| Campo | Valor |
|---|---|
| Proyecto | EventU — aplicación móvil para organizar eventos sociales en Cali |
| Documento | SRS conforme a ISO/IEC/IEEE 29148:2018; RNF clasificados según ISO/IEC 25010 |
| Siglas | EU |
| Versión | 2.0 (borrador para revisión del equipo). Incorpora el cambio CR-01: EventU como marketplace de servicios para eventos |
| Fecha | 7 de noviembre de 2026 (v1.0: 5 de noviembre de 2026) |
| Autores | Equipo EventU: David Enciso, Jean Paul Davalos, Yenny Rivas, Juan Manuel Perea, Juan Carlos Cruz (redactado con apoyo de IA) |
| Curso | Innovación y Emprendimiento Empresarial · Universidad del Valle · Prof. Víctor Bucheli |
| Fuentes | Entrega 1 — Proyecto EventU; Proyecto de MVP v1.1; Solicitud de cambio CR-01 (7 de noviembre de 2026); prototipo de frontend de Juan Carlos (referencia de diseño; por decisión del equipo no se concilia en este documento) |

**Convención:** «Propuesto» = valor sin fuente en la Entrega 1, a validar. «Supuesto» = decisión tomada para poder avanzar.

## 2. Introducción

### 2.1 Propósito
Especificar los requisitos del MVP de EventU para que sirvan de base única de historias de usuario, arquitectura, base de datos y pruebas.

### 2.2 Objetivos
OE-1 a OE-5 del Proyecto de MVP: recomendar paquetes que respeten el presupuesto (T1), cotizar sin conversaciones individuales (T2), dar confianza sobre cada proveedor (T3), ofrecer modalidades comparables (T4) y completar el flujo hasta la reserva con pago simulado.

### 2.3 Audiencia
Equipo de desarrollo (backend y frontend móvil), responsable de datos y contenido, responsables de pruebas, docente evaluador.

### 2.4 Convenciones de redacción
- **«debe»** indica requisito obligatorio; **«puede»**, opcional.
- IDs: `RF-<MÓDULO>-nn` (funcionales), `RNF-<CARACTERÍSTICA>-nn` (no funcionales), `RN-nn` (reglas de negocio). Son estables: no se renumeran entre versiones.
- Prioridad MoSCoW: M (Must), S (Should), C (Could), W (Won't, en esta versión).
- Módulos: CAT Catálogo · EXP Exploración (marketplace) · REC Recomendador · PRO Proveedores · RES Reserva · PAG Pago simulado · CNF Confirmación · GEN Transversales.
- Los textos literales de mensajes no se fijan aquí: se indica «mensaje requerido» y se definen en el backlog.

## 3. Alcance

**Capacidades incluidas:** exploración tipo marketplace (referencia: Booking, Trivago y TripAdvisor) con inicio, buscador, categorías, destacados, resultados en lista y en mapa, filtros y orden; fichas de proveedor con galería de fotos, calificación, reseñas de solo lectura y estado de verificación; «Mi evento» (carrito de servicios) con total y presupuesto opcional; recomendador de tres paquetes por presupuesto como atajo que llena «Mi evento»; datos de contacto; reserva; pago simulado; confirmación y consulta de reservas.

**Exclusiones y límites:** alta de reseñas por los usuarios (las reseñas son de ejemplo y de solo lectura); disponibilidad por fecha de cada proveedor; ordenar o comparar por distancia al usuario; pasarela de pago real; abonos por fases y gestión automatizada de reservas; RSVP e invitaciones digitales; panel y suscripciones de proveedores; cuentas de usuario del cliente; IA generativa; personalización estética como función independiente (T5); publicación en tiendas de aplicaciones.

**Dependencias externas:** API desplegado en Render (puede tener arranque en frío); distribución de la app con Expo Go o APK de prueba (Propuesto); datos del catálogo preparados por el equipo (datos de ejemplo); prototipo de frontend de Juan Carlos como referencia de diseño.

## 4. Fuentes y referencias

### 4.1 Fuentes
1. Entrega 1 — Proyecto EventU (noviembre de 2026): §2 (entorno), §3 (consumidor y JTBD), §3.8 (tareas T1–T4 y criterios), §4 (propuesta de valor y lienzo), §5 (curva de valor).
2. Proyecto de MVP v1.1 (5 de noviembre de 2026).
3. Prototipo de frontend de Juan Carlos (referencia de diseño; no se concilia en este documento por decisión del equipo).
4. ISO/IEC/IEEE 29148:2018; ISO/IEC 25010.

### 4.2 Conciliación entre el prototipo de frontend y la Entrega 1

Por decisión del equipo no se revisa el prototipo para este documento: Juan Carlos ya lo entregó y no tiene tareas en el sprint, y las pantallas se definen a partir de los requisitos de este SRS. Diferencias conocidas entre las demás fuentes:

| # | Diferencia | Decisión propuesta |
|---|---|---|
| C-1 | La Entrega 1 (§4.3.2) deja la pasarela de pago como fase futura; el MVP incluye reserva y pago **simulado** | Mantener el pago simulado (RN-09) y avisar al docente (S-02) |
| C-2 | T1 define el paquete con lugar, alimentación y decoración; el lienzo menciona DJs | Entretenimiento como cuarto rubro opcional (S-01, RN-03) |
| C-3 | T5 (personalización estética) es un atributo complementario | Sin RF propio; se excluye (§3) |
| C-4 | Pantallas, navegación y textos del prototipo vs flujo de 7 pasos | No se concilia: el SRS prevalece y el frontend adapta el prototipo a los requisitos (S-04, P-08 cerrado) |

## 5. Definiciones, siglas y abreviaturas

| Término | Definición |
|---|---|
| Paquete | Combinación de servicios de distintos rubros con costo total y desglose |
| Modalidad | Nivel de paquete: Ahorro, Equilibrado o Premium |
| Rubro | Categoría de servicio: espacio, alimentación, decoración, entretenimiento |
| Servicio | Oferta concreta de un proveedor con precio, capacidad y tipos de evento admitidos |
| Proveedor verificado | Proveedor cuya ficha tiene datos y comprobaciones documentadas; no garantiza el cumplimiento del servicio |
| Presupuesto restante | Presupuesto ingresado menos el total del paquete vigente |
| Reserva | Registro del paquete elegido, con copia de servicios y precios, y datos de contacto del cliente |
| Pago simulado | Pago de prueba que no mueve dinero ni guarda datos de tarjeta |
| COP | Pesos colombianos, siempre enteros |
| MVP | Producto mínimo viable |

## 6. Matriz de actores y permisos

| Capacidad | Organizador | Sistema | Pasarela simulada | Administrador del catálogo |
|---|---|---|---|---|
| Buscar, filtrar y ver proveedores en lista y mapa; consultar fichas, fotos y reseñas | ✔ | Calcula precios y calificaciones | — | — |
| Armar «Mi evento» (agregar, cambiar y quitar servicios) | ✔ | Valida | — | — |
| Solicitar recomendación y ajustar paquete | ✔ | Calcula | — | — |
| Crear reserva | ✔ | Valida y registra | — | — |
| Pagar | ✔ | Orquesta | Aprueba o rechaza | — |
| Consultar confirmación | ✔ | Entrega | — | — |
| Cargar y verificar catálogo | — | — | — | ✔ (fuera de la app, mediante datos semilla) |

El Organizador no requiere cuenta (S-03). El Administrador del catálogo no tiene interfaz en el MVP (P-03).

## 7. Descripción funcional por módulos

- **CAT — Catálogo:** mantiene la oferta de servicios y proveedores de Cali y su área metropolitana. Su interfaz es la de EXP; el endpoint de catálogo se conserva.
- **EXP — Exploración (marketplace):** inicio con buscador, categorías y destacados; resultados en tarjetas con foto, calificación y precio «desde», filtros, orden y mapa; ficha con galería y reseñas; «Mi evento» con las reglas de un servicio por rubro y presupuesto opcional; navegación por pestañas.
- **REC — Recomendador:** atajo «Arma mi evento por presupuesto». Recibe presupuesto, tipo de evento e invitados y genera tres paquetes que nunca superan el presupuesto, con desglose, presupuesto restante y comparación; el paquete elegido se carga en «Mi evento», donde se ajusta en tiempo real.
- **PRO — Proveedores:** muestra la ficha de cada proveedor con contacto, alcance del servicio y estado de verificación respaldado por comprobaciones registradas.
- **RES — Reserva:** convierte «Mi evento» (con o sin paquete de origen) en una reserva con datos de contacto y una copia de servicios y precios.
- **PAG — Pago simulado:** simula el pago con tarjetas de prueba (aprobada y rechazada) y registra solo el resultado.
- **CNF — Confirmación:** muestra el resumen y el número de reserva y permite consultarlo.
- **GEN — Transversales:** navegación, estados de carga, error y vacío, teclados adecuados y mensajes de error.

## 8. Reglas de negocio

| ID | Regla | Origen |
|---|---|---|
| RN-01 | El costo total de cualquier paquete sugerido o ajustado nunca supera el presupuesto ingresado | T1, §3.8 |
| RN-02 | Existen tres modalidades: Ahorro (menor costo), Equilibrado (relación costo-calidad) y Premium (mayor nivel de servicio dentro del presupuesto) | T4 |
| RN-03 | Todo paquete incluye espacio, alimentación y decoración; el entretenimiento es opcional (Propuesto) | T1; S-01 |
| RN-04 | El total es la suma de los ítems del paquete; el dinero se maneja en COP enteros | Proyecto de MVP |
| RN-05 | Presupuesto restante = presupuesto ingresado − total del paquete vigente; se recalcula al ajustar | T4 |
| RN-06 | Si el presupuesto no alcanza ni para el paquete Ahorro, el sistema lo informa y no muestra paquetes que lo excedan | RN-01 |
| RN-07 | Una ficha «verificada» exige datos y comprobaciones documentadas; la verificación no garantiza el cumplimiento del servicio | T3, §3.8 |
| RN-08 | La reserva guarda una copia de los servicios y precios vigentes al reservar | OE-5 |
| RN-09 | El pago es simulado: no mueve dinero ni almacena datos de tarjeta; solo registra aprobado o rechazado | S-02 |
| RN-10 | Los precios y proveedores del catálogo inicial son datos de ejemplo, por validar | Proyecto de MVP |
| RN-11 | Cada modalidad compromete como máximo un porcentaje del presupuesto (**Propuesto**): Ahorro 70 %, Equilibrado 85 %, Premium 100 % | T4; P-09 |
| RN-12 | Reparto del monto objetivo por rubro (**Propuesto**): espacio 40 %, alimentación 35 %, decoración 15 %, entretenimiento 10 %. Si no se incluye entretenimiento, su porcentaje se reparte proporcionalmente entre los demás | T1; P-09 |
| RN-13 | Criterio de selección por rubro (**Propuesto**): Ahorro elige el servicio elegible de menor precio; Equilibrado, el de nivel intermedio; Premium, el de mayor nivel sin superar el tope del rubro. Desempate determinista: menor precio y, luego, menor identificador | T4; P-09 |
| RN-14 | Un servicio es elegible si admite el tipo de evento y su capacidad cubre el número de invitados | T1 |
| RN-15 | Los costos por invitado se multiplican por el número de invitados y se redondean a COP enteros | RN-04 |
| RN-16 | Si un rubro obligatorio no tiene servicios elegibles, no se genera el paquete de esa modalidad y se informa la causa | RN-06 |
| RN-17 | Pago simulado (**Propuesto**): una tarjeta de prueba aprobada y una rechazada, documentadas en la pantalla de pago; cualquier otro número se rechaza | RN-09; P-10 |
| RN-18 | El número de reserva es único (**Propuesto**: prefijo «EU-» + 6 caracteres alfanuméricos) | OE-5 |
| RN-19 | Validaciones de entrada (**Propuesto**): presupuesto entero de 1.000.000 a 50.000.000 COP; invitados entero de 1 a 500; tipo de evento: cumpleaños, boda o XV | T1; P-11 |
| RN-20 | La fecha del evento debe ser posterior a la fecha actual | OE-5 |
| RN-21 | El origen de la reserva es la modalidad del paquete elegido, si «Mi evento» no se modificó, o `personalizado` en cualquier otro caso (**Propuesto**) | CR-01 |
| RN-22 | En «Mi evento» el presupuesto es opcional. Si existe, rigen RN-01 y RN-05; si no, no hay tope ni presupuesto restante | CR-01; RN-01 |
| RN-23 | «Mi evento» admite un servicio por rubro; agregar otro del mismo rubro lo reemplaza previa confirmación. Para reservar se exigen espacio, alimentación y decoración (RN-03) | CR-01; RN-03 |
| RN-24 | La calificación de un proveedor es el promedio de sus reseñas con un decimal; sin reseñas se muestra «Sin reseñas» | CR-01 |
| RN-25 | El precio «desde» de un proveedor es el menor costo entre sus servicios elegibles: con invitados, el costo para ese número (RN-15); sin invitados, el costo con la capacidad mínima del servicio (**Propuesto**) | CR-01; RN-15 |
| RN-26 | Orden de resultados (**Propuesto**): «Recomendados» = destacados primero, luego mejor calificación, luego identificador; «Menor precio» y «Mayor precio» por precio «desde»; «Mejor calificados» por promedio y luego número de reseñas. Todo empate se resuelve por identificador | CR-01 |
| RN-27 | Las reseñas son datos de ejemplo, de solo lectura y rotuladas como tales; no hay alta de reseñas en el MVP | CR-01; RN-10 |
| RN-28 | Las coordenadas de un proveedor son aproximadas (3 decimales, unos 100 m); la app no muestra una dirección exacta | CR-01 |

## 9. Requisitos funcionales

### 9.1 Catálogo (CAT)

Con CR-01 los RF-CAT se cumplen desde la interfaz de exploración (RF-EXP-03 y RF-EXP-04); se conservan porque definen el comportamiento del servicio de catálogo.

| ID | Descripción | Prior. | Origen | Criterio de verificación |
|---|---|---|---|---|
| RF-CAT-01 | El sistema debe listar los servicios del catálogo mostrando nombre, rubro, proveedor y precio en COP | M | T2 | Cada servicio de la semilla aparece con los cuatro datos |
| RF-CAT-02 | El sistema debe permitir filtrar el catálogo por rubro y por tipo de evento | M | T2 | Al elegir un filtro solo se listan servicios que lo cumplen |
| RF-CAT-03 | El sistema puede permitir filtrar por rango de precio | S | T2 | Al fijar un rango, ningún servicio listado queda fuera de él |
| RF-CAT-04 | El sistema debe mostrar un estado vacío con mensaje requerido cuando ningún servicio cumple los filtros | M | T2 | Con filtros sin resultados se muestra el mensaje y la opción de limpiar filtros |

### 9.2 Exploración — marketplace (EXP)

| ID | Descripción | Prior. | Origen | Criterio de verificación |
|---|---|---|---|---|
| RF-EXP-01 | El sistema debe ofrecer un inicio con buscador por tipo de evento, fecha (opcional) y número de invitados | M | CR-01 | Los tres campos existen; con datos válidos, «Buscar» abre los resultados con esos criterios |
| RF-EXP-02 | El sistema debe mostrar en el inicio las categorías (rubros) y una sección de proveedores destacados | S | CR-01 | Tocar una categoría filtra los resultados; hay hasta 6 destacados |
| RF-EXP-03 | El sistema debe listar los proveedores en tarjetas con foto, nombre, rubros, ubicación, calificación, insignia de verificación y precio «desde» | M | CR-01; RN-24, RN-25 | Cada proveedor de la semilla aparece con esos datos |
| RF-EXP-04 | El sistema debe permitir filtrar por rubro, tipo de evento, rango de precio, calificación mínima y solo verificados, y ordenar según RN-26 | M | CR-01; RN-26 | Ningún proveedor listado incumple un filtro; el orden coincide con RN-26 |
| RF-EXP-05 | El sistema debe mostrar una galería de fotos en la ficha y la foto principal en la tarjeta | S | CR-01 | Cada ficha de la semilla muestra sus fotos; si una no carga se ve un recuadro neutro |
| RF-EXP-06 | El sistema debe mostrar la calificación y las reseñas de ejemplo de cada proveedor en modo de solo lectura | S | CR-01; RN-24, RN-27 | La calificación coincide con el promedio de las reseñas; no existe forma de escribir reseñas |
| RF-EXP-07 | El sistema debe permitir agregar, cambiar y quitar servicios en «Mi evento» y mostrar el total en COP | M | CR-01; RN-04 | Cada acción actualiza el total en la misma pantalla |
| RF-EXP-08 | El sistema debe aplicar en «Mi evento» las reglas RN-22 y RN-23 y revalidar los servicios si cambia el número de invitados | M | CR-01 | No se puede reservar sin los tres rubros obligatorios; con presupuesto, un cambio que lo excede no se aplica |
| RF-EXP-09 | El sistema puede mostrar los resultados en un mapa con marcadores y permitir «Buscar en esta zona» | C | CR-01; RN-28 | Cada proveedor con coordenadas aparece en el mapa; tocar un marcador abre su tarjeta |
| RF-EXP-10 | El sistema debe ofrecer en el inicio el acceso «Arma mi evento por presupuesto» y cargar el paquete elegido en «Mi evento» | S | CR-01; T1 | Elegir un paquete deja sus servicios en «Mi evento» con el origen del paquete (RN-21) |
| RF-EXP-11 | El sistema debe ofrecer navegación por pestañas: Inicio, Resultados, Mi evento y Reservas | M | CR-01 | Las cuatro pestañas existen y conservan su estado al cambiar entre ellas |

### 9.3 Recomendador (REC)

| ID | Descripción | Prior. | Origen | Criterio de verificación |
|---|---|---|---|---|
| RF-REC-01 | El sistema debe ofrecer un formulario con presupuesto (COP), tipo de evento y número de invitados | M | T1 | Los tres campos existen y son obligatorios |
| RF-REC-02 | El sistema debe validar las entradas según RN-19 y mostrar un mensaje requerido junto al campo inválido | M | T1; RN-19 | Valores fuera de rango o vacíos no permiten continuar |
| RF-REC-03 | El sistema debe generar los paquetes Ahorro, Equilibrado y Premium a partir de las entradas | M | T1, T4 | Con entradas válidas y catálogo suficiente se muestran las tres modalidades |
| RF-REC-04 | El sistema debe incluir en cada paquete espacio, alimentación y decoración, y entretenimiento de forma opcional | M | RN-03 | Todo paquete tiene los tres rubros obligatorios |
| RF-REC-05 | El sistema debe garantizar que el costo total de cada paquete no supere el presupuesto | M | T1; RN-01 | Prueba de propiedad con al menos 100 entradas aleatorias: 0 paquetes sobre el presupuesto |
| RF-REC-06 | El sistema debe mostrar el costo total y el desglose por rubro y por servicio de cada paquete | M | T1, T2 | La suma del desglose coincide con el total |
| RF-REC-07 | El sistema debe mostrar el presupuesto restante de cada paquete | M | T4; RN-05 | Restante = presupuesto − total |
| RF-REC-08 | El sistema debe informar cuando el presupuesto no alcanza (RN-06) o falta oferta en un rubro (RN-16), sin mostrar paquetes que excedan | M | RN-06, RN-16 | Con presupuesto menor al Ahorro más barato no se muestra ningún paquete y sí el mensaje |
| RF-REC-09 | El sistema debe devolver el mismo resultado para las mismas entradas y el mismo catálogo | S | OE-1; RN-13 | Dos ejecuciones idénticas producen paquetes idénticos |
| RF-REC-10 | El sistema debe permitir comparar al menos dos paquetes mostrando costo, servicios incluidos y presupuesto restante | C | T2, T4 | Dos paquetes se visualizan juntos con los tres datos |
| RF-REC-11 | El sistema debe permitir reemplazar un servicio por otro elegible del mismo rubro, o quitar el entretenimiento, y recalcular total y presupuesto restante; el ajuste ocurre en «Mi evento» | M | T2, T4; CR-01 | Tras el cambio, total y restante se actualizan en la misma pantalla |
| RF-REC-12 | El sistema debe impedir ajustes que superen el presupuesto e informar el motivo con un mensaje requerido | M | T4; RN-01 | Un reemplazo que excede el presupuesto no se aplica |
| RF-REC-13 | El sistema puede permitir restablecer el paquete a la propuesta original | C | T4 | Tras restablecer, los servicios vuelven a los iniciales |

### 9.4 Proveedores (PRO)

| ID | Descripción | Prior. | Origen | Criterio de verificación |
|---|---|---|---|---|
| RF-PRO-01 | El sistema debe mostrar la ficha de cada proveedor con nombre, descripción del alcance del servicio, rubros, ubicación y datos de contacto | M | T3 | Toda ficha de la semilla tiene los cinco datos |
| RF-PRO-02 | El sistema debe mostrar el estado de verificación de cada proveedor (verificado o en revisión) | M | T3; RN-07 | El estado es visible en la ficha y en el listado |
| RF-PRO-03 | El sistema solo debe marcar «verificado» a un proveedor con comprobaciones documentadas registradas | M | T3; RN-07 | Ningún proveedor «verificado» carece de comprobación registrada |
| RF-PRO-04 | El sistema debe permitir abrir la ficha desde el inicio, los resultados, el mapa, «Mi evento» y un paquete | M | T3; CR-01 | Desde cada punto se llega a la ficha del proveedor correcto |
| RF-PRO-05 | El sistema debe advertir en la ficha que la verificación no garantiza el cumplimiento del servicio | S | RN-07 | El aviso aparece en toda ficha verificada |

### 9.5 Reserva (RES)

| ID | Descripción | Prior. | Origen | Criterio de verificación |
|---|---|---|---|---|
| RF-RES-01 | El sistema debe permitir iniciar la reserva desde «Mi evento», con servicios elegidos uno a uno o cargados desde un paquete, ajustado o no | M | OE-5; CR-01 | Desde «Mi evento» completo se inicia la reserva |
| RF-RES-02 | El sistema debe capturar nombre, correo, teléfono y fecha del evento del cliente | M | OE-5 | Los cuatro campos existen y son obligatorios |
| RF-RES-03 | El sistema debe validar nombre no vacío, correo con formato válido, teléfono de 10 dígitos (Propuesto) y fecha futura (RN-20), con mensaje requerido por campo | M | OE-5; RN-20 | Datos inválidos impiden continuar y señalan el campo |
| RF-RES-04 | El sistema debe mostrar un resumen (paquete, servicios, total y datos) antes del pago | M | OE-5 | El resumen coincide con lo elegido |
| RF-RES-05 | El sistema debe crear la reserva en estado «creada» con copia de servicios y precios | M | RN-08 | Al cambiar luego un precio del catálogo, la reserva conserva el original |
| RF-RES-06 | El sistema debe asignar a cada reserva un número único (RN-18) | M | RN-18 | Dos reservas nunca comparten número |
| RF-RES-07 | El sistema debe revalidar en el servidor que el total coincide con la suma de los precios vigentes y no supera el presupuesto indicado | S | RN-01, RN-04 | Un total manipulado es rechazado con error |
| RF-RES-08 | El sistema puede permitir cancelar la reserva antes de pagar | C | RN-08 | La reserva pasa a «cancelada» y no admite pago |

### 9.6 Pago simulado (PAG)

| ID | Descripción | Prior. | Origen | Criterio de verificación |
|---|---|---|---|---|
| RF-PAG-01 | El sistema debe ofrecer una pantalla de pago con el resumen y campos de tarjeta de prueba | M | OE-5 | La pantalla muestra monto y campos de tarjeta |
| RF-PAG-02 | El sistema debe indicar de forma visible que el pago es simulado y que no se cobra dinero | M | RN-09 | El aviso aparece antes de confirmar |
| RF-PAG-03 | El sistema debe aprobar el pago con la tarjeta de prueba aprobada y marcar la reserva como «pagada» | M | RN-09, RN-17 | Pago con la tarjeta aprobada → pago «aprobado», reserva «pagada» |
| RF-PAG-04 | El sistema debe rechazar el pago con la tarjeta de prueba rechazada, marcar la reserva «pago_rechazado» y mostrar un mensaje requerido | M | RN-09, RN-17 | Pago con la tarjeta rechazada → pago «rechazado» y mensaje |
| RF-PAG-05 | El sistema debe permitir reintentar el pago tras un rechazo | S | RN-09 | Tras rechazo se puede pagar de nuevo y la reserva pasa a «pagada» si se aprueba |
| RF-PAG-06 | El sistema no debe almacenar número de tarjeta, vencimiento ni código; solo resultado, monto, referencia simulada y fecha | M | RN-09 | La base de datos no contiene datos de tarjeta |
| RF-PAG-07 | El sistema debe rechazar cualquier número de tarjeta distinto de las tarjetas de prueba (Propuesto) | S | RN-17 | Un número desconocido genera pago «rechazado» |
| RF-PAG-08 | El sistema debe evitar el doble pago: bloquear el botón mientras se procesa e ignorar un segundo pago aprobado sobre una reserva ya pagada | S | RN-09 | Dos envíos seguidos producen un solo pago aprobado |

### 9.7 Confirmación (CNF)

| ID | Descripción | Prior. | Origen | Criterio de verificación |
|---|---|---|---|---|
| RF-CNF-01 | El sistema debe mostrar tras el pago aprobado el número de reserva, paquete, servicios, total y datos de contacto | M | OE-5 | Todos los datos aparecen y coinciden con la reserva |
| RF-CNF-02 | El sistema debe permitir consultar una reserva por su número | S | OE-5 | Un número válido muestra la reserva; uno inexistente, un mensaje requerido |
| RF-CNF-03 | El sistema debe recordar en la confirmación que el pago fue simulado | S | RN-09 | El aviso aparece en la confirmación |
| RF-CNF-04 | El sistema puede permitir volver al inicio desde la confirmación para empezar un nuevo evento | C | T2; CR-01 | La acción lleva al inicio con «Mi evento» vacío |

### 9.8 Transversales (GEN)

| ID | Descripción | Prior. | Origen | Criterio de verificación |
|---|---|---|---|---|
| RF-GEN-01 | El sistema debe permitir navegar entre pantallas y volver a la anterior sin perder presupuesto, paquete ni datos ingresados | M | T2 | Ir y volver conserva los datos |
| RF-GEN-02 | El sistema debe mostrar un estado de carga durante las operaciones con el API | S | RNF-FIA-02 | Se ve el indicador mientras llega la respuesta |
| RF-GEN-03 | El sistema debe mostrar un error de red con opción de reintentar sin cerrar la app | M | RNF-FIA-01 | Con el API inaccesible aparece el error y el reintento funciona al recuperarse |
| RF-GEN-04 | El sistema debe mostrar estados vacíos con mensaje requerido cuando no hay datos que mostrar | M | RF-CAT-04 | Sin resultados se muestra el estado vacío |
| RF-GEN-05 | El sistema debe usar el teclado adecuado por campo (numérico para presupuesto e invitados, correo, teléfono) | S | RNF-USA-02 | Cada campo abre el teclado correspondiente |
| RF-GEN-06 | El sistema debe mostrar un mensaje de fallo técnico genérico requerido ante errores inesperados | M | RNF-FIA-01 | Un error 5xx muestra el mensaje y no datos técnicos |

## 10. Requisitos no funcionales (ISO/IEC 25010)

| ID | Característica | Requisito | Métrica | Prior. | Fuente |
|---|---|---|---|---|---|
| RNF-ADF-01 | Adecuación funcional | El cálculo de paquetes debe ser correcto y respetar el presupuesto | 0 paquetes sobre el presupuesto en escenarios de prueba; total = suma de ítems | M | Entrega 1 §3.8 |
| RNF-EFI-01 | Eficiencia de desempeño | La recomendación debe responder rápido en red móvil | ≤ 3 s con el catálogo semilla en 4G | S | Propuesto |
| RNF-EFI-02 | Eficiencia de desempeño | El ajuste de un paquete debe reflejarse casi al instante | ≤ 1 s desde la acción hasta ver el nuevo total | S | Propuesto |
| RNF-EFI-03 | Eficiencia de desempeño | El listado de resultados debe responder rápido en red móvil | ≤ 3 s con la semilla (16 proveedores) en 4G | S | Propuesto (CR-01) |
| RNF-USA-05 | Usabilidad | Las imágenes deben tener texto alternativo y no bloquear la pantalla si fallan | 100 % de las fotos de la semilla con texto alternativo; una foto caída no genera error visible | S | Propuesto (CR-01) |
| RNF-COM-01 | Compatibilidad | La app debe funcionar en versiones recientes de Android e iOS | Android 10+ e iOS 15+ | M | Propuesto |
| RNF-COM-02 | Compatibilidad | El API debe exponer REST/JSON bajo un prefijo versionado | Rutas bajo `/api/v1` | S | Propuesto |
| RNF-USA-01 | Usabilidad | El usuario debe poder comparar dos paquetes y consultar su desglose rápidamente | ≤ 5 min en pruebas con usuarios (se registra el tiempo real) | M | Entrega 1 §3.8 |
| RNF-USA-02 | Usabilidad | La interfaz debe estar adaptada a pantalla móvil en vertical con áreas táctiles suficientes | Áreas táctiles ≥ 44×44 pt; sin desplazamiento horizontal | M | Propuesto |
| RNF-USA-03 | Usabilidad | Los textos deben ser legibles y respetar el tamaño de fuente del sistema | Texto base ≥ 16 pt; la interfaz no se rompe con fuente ampliada | S | Propuesto |
| RNF-USA-04 | Usabilidad | Los errores de validación deben indicarse junto al campo | Todo campo inválido muestra mensaje en el campo | M | Propuesto |
| RNF-FIA-01 | Fiabilidad | La app debe tolerar red lenta o sin conexión sin cerrarse | 0 cierres inesperados en pruebas con red cortada; error con reintento | M | Propuesto |
| RNF-FIA-02 | Fiabilidad | La app debe tolerar el arranque en frío del API desplegado | Estado de carga visible y espera de hasta 60 s antes de mostrar error | S | Propuesto |
| RNF-SEG-01 | Seguridad | Toda comunicación con el API debe usar HTTPS | 100 % de las peticiones en HTTPS en el entorno desplegado | M | Propuesto |
| RNF-SEG-02 | Seguridad | No deben almacenarse datos de tarjeta | 0 columnas o registros con número, vencimiento o código | M | RN-09 |
| RNF-SEG-03 | Seguridad | El servidor debe validar todas las entradas, sin confiar en el cliente | Peticiones inválidas devuelven error de validación | M | Propuesto |
| RNF-SEG-04 | Seguridad | Los secretos y URLs sensibles deben estar fuera del repositorio | 0 secretos en el código fuente | M | Propuesto |
| RNF-SEG-05 | Seguridad | Los datos personales deben limitarse a nombre, correo y teléfono de la reserva, con aviso de tratamiento (a validar frente a la Ley 1581 de 2012) | Solo esos tres datos persistidos; aviso visible | S | Propuesto; P-12 |
| RNF-MAN-01 | Mantenibilidad | El recomendador debe ser una función pura con pruebas automatizadas | Cobertura ≥ 80 % del módulo recomendador | M | Propuesto |
| RNF-MAN-02 | Mantenibilidad | Debe existir una puerta de calidad antes de fusionar | Lint, tipos y tests en verde en cada PR | M | Proyecto de MVP |
| RNF-MAN-03 | Mantenibilidad | El contrato del API debe estar documentado | Documentación OpenAPI generada por FastAPI disponible | S | Propuesto |
| RNF-POR-01 | Portabilidad | La URL del API debe configurarse por variable de entorno | Cambiar de entorno sin modificar código | M | Propuesto |
| RNF-POR-02 | Portabilidad | Android e iOS deben compartir la misma base de código | Una sola base de código móvil | S | Propuesto |

## 11. Requisitos de datos

El detalle va en el documento de base de datos. El SRS exige las siguientes entidades y atributos:

| Entidad | Atributos exigidos |
|---|---|
| Proveedor | Identificador, nombre, descripción, ubicación (barrio y municipio), coordenadas aproximadas, destacado, contacto, estado de verificación, calificación derivada |
| Imagen de proveedor | Proveedor, URL, texto alternativo, posición |
| Reseña de proveedor | Proveedor, autor (ficticio), puntaje de 1 a 5, comentario, fecha |
| Verificación de proveedor | Proveedor, tipo de comprobación, fecha, evidencia o descripción |
| Servicio | Proveedor, rubro, nombre, nivel de servicio (1–3), tipo de precio (fijo o por invitado), precio en COP, capacidad mínima y máxima, tipos de evento admitidos |
| Reserva | Número, estado, presupuesto indicado (opcional), origen (modalidad del paquete o personalizado), tipo de evento, invitados, fecha del evento, nombre, correo y teléfono del cliente, total en COP |
| Ítem de reserva | Reserva, servicio, copia de nombre, proveedor y precio, cantidad |
| Pago | Reserva, resultado (aprobado o rechazado), monto, referencia simulada, fecha |

## 12. Matriz de trazabilidad

| Origen | Reglas de negocio | Requisitos funcionales | Requisitos no funcionales | HU |
|---|---|---|---|---|
| T1 Paquete por presupuesto | RN-01, RN-03, RN-04, RN-06, RN-12, RN-14, RN-15, RN-16, RN-19 | RF-REC-01, 02, 03, 04, 05, 06, 08; RF-RES-07 | RNF-ADF-01, RNF-EFI-01 | (se llena en el backlog) |
| T2 Cotización inmediata | RN-05 | RF-CAT-01 a 04; RF-REC-06, 10, 11; RF-GEN-01; RF-CNF-04 | RNF-USA-01, RNF-EFI-02 | (se llena en el backlog) |
| T3 Confianza y verificación | RN-07, RN-10 | RF-PRO-01 a 05 | RNF-SEG-05 | (se llena en el backlog) |
| T4 Modalidades de paquete | RN-02, RN-05, RN-11, RN-13 | RF-REC-03, 07, 09, 10, 11, 12, 13 | RNF-ADF-01 | (se llena en el backlog) |
| OE-5 Flujo hasta reserva y pago simulado | RN-08, RN-09, RN-17, RN-18, RN-20 | RF-RES-01 a 08; RF-PAG-01 a 08; RF-CNF-01 a 03 | RNF-SEG-01, RNF-SEG-02, RNF-SEG-03 | (se llena en el backlog) |
| CR-01 Marketplace | RN-21 a RN-28 | RF-EXP-01 a 11; RF-PRO-04; RF-RES-01 | RNF-EFI-03, RNF-USA-05 | (se llena en el backlog) |
| Transversal | — | RF-GEN-02 a 06 | RNF-FIA-01, RNF-FIA-02, RNF-USA-02 a 04, RNF-COM, RNF-POR, RNF-MAN | (se llena en el backlog) |

## 13. Supuestos, ambigüedades y decisiones pendientes

**Supuestos heredados del Proyecto de MVP:** S-01 entretenimiento como cuarto rubro opcional · S-02 pago simulado dentro del MVP, aunque la Entrega 1 lo dejaba como fase futura (avisar al docente) · S-03 el cliente no tiene cuenta · S-04 el prototipo de Juan Carlos es solo referencia de diseño y Juan Carlos no tiene tareas en el sprint.

**Supuestos del cambio CR-01 (7 de noviembre de 2026):** S-05 las reseñas y calificaciones son de ejemplo y de solo lectura · S-06 las fotos son imágenes de ejemplo alojadas en un banco de imágenes, a sustituir por fotos con licencia · S-07 las coordenadas son aproximadas, por barrio · S-08 el marketplace es la entrada principal y el recomendador por presupuesto queda como atajo; el alcance completo del cambio se acepta aunque exceda la capacidad estimada de 3 días (ver backlog y R-10).

**Decisiones del equipo (5 de noviembre de 2026):** el framework móvil es React Native con Expo (P-04); David asume las pruebas además del backend (P-07); no se concilia el SRS con el prototipo (P-08).

| ID | Pendiente | Responsable sugerido | Fecha límite sugerida |
|---|---|---|---|
| P-01 | Fecha de entrega del MVP | Equipo | Antes del Día 1 |
| P-02 | Rol de Juan Manuel Perea y líder gestor | Equipo | Antes del Día 1 |
| P-03 | ¿Administración del catálogo desde la app o solo por semilla? | David | Día 1 |
| P-04 | **Resuelto:** framework móvil confirmado, React Native con Expo | — | — |
| P-05 | Porcentajes de reparto por rubro y modalidad | Yenny y David | Día 1 |
| P-06 | Fuente de precios y proveedores reales para sustituir datos de ejemplo | Yenny | Después del MVP |
| P-07 | **Resuelto:** David asume las pruebas (QA) además del backend (ver R-09) | — | — |
| P-08 | **Cerrado por decisión del equipo:** no se concilia con el prototipo; el frontend lo adapta según los requisitos | — | — |
| P-09 | Validar RN-11, RN-12 y RN-13 con el catálogo real de ejemplo | Yenny y David | Día 1 |
| P-10 | Definir las tarjetas de prueba y los mensajes de éxito y fallo | David | Día 1 |
| P-11 | Confirmar rangos de validación (RN-19) y formato de teléfono | Yenny | Día 1 |
| P-12 | Revisar el aviso de tratamiento de datos personales | Equipo | Día 3 |
| P-13 | Confirmar versiones mínimas de Android e iOS | Jean Paul | Día 1 |
| P-14 | Origen y licencia de las fotos de proveedores (S-06) | Yenny | Día 2 |
| P-15 | Definir si habrá reseñas reales después del MVP (S-05) | Equipo | Después del MVP |
| P-16 | Coordenadas de cada proveedor de ejemplo (S-07) | Yenny | Día 2 |
| P-17 | Criterio de «Recomendados» y de los destacados (RN-26) | Equipo | Día 2 |
| P-18 | Rol de Juan Manuel ante el aumento de alcance (relacionado con P-02 y R-10) | Equipo | Antes del Día 1 |

## 14. Riesgos y dependencias relevantes

| ID | Riesgo o dependencia | Mitigación |
|---|---|---|
| R-01 | Datos del catálogo insuficientes o poco creíbles (afecta RF-REC y RN-16) | Semilla de 15–20 proveedores el Día 1, marcada como ejemplo |
| R-02 | Los 3 días no alcanzan | Recortar primero RF de prioridad S y C |
| R-03 | Crecimiento del alcance | §3 como referencia única |
| R-04 | El agente genera código incorrecto | Plan previo, PRs pequeños y puerta de calidad (RNF-MAN-02) |
| R-05 | Fallos de despliegue del API o de distribución de la app | API desplegado y app instalada el Día 1 |
| R-06 | Expectativa de pago real | Aviso visible (RF-PAG-02, RF-CNF-03) |
| R-07 | Precios tomados como definitivos | Etiquetar como «por validar» (RN-10) |
| R-08 | El frontend móvil depende de una sola persona | Partir del prototipo y definir apoyo (P-02) |
| D-01 | Arranque en frío del API en Render | RNF-FIA-02 y RF-GEN-02 |
| R-10 | El alcance del CR-01 supera la capacidad estimada (≈ 141 SP frente a 108) | Priorizar los RF Must del flujo hasta el pago; dejar RF-EXP-09 (mapa), RF-REC-10 y RF-EXP-05/06 como recorte; evaluar un día de colchón |
| R-11 | Las fotos dependen de un servicio externo de imágenes | Recuadro neutro si falla; fotos con licencia después (P-14) |
| R-12 | El mapa depende de una librería nativa y, en Android fuera de Expo Go, de una clave de Google Maps | Hacerlo al final (Could); probar solo en Expo Go; si no cabe, omitirlo |
| R-09 | David concentra backend y pruebas | Automatizar las pruebas del recomendador, priorizar los RF Must y hacer revisión cruzada de PRs con Jean Paul |

## 15. Criterios de validación y checklist de calidad documental

| Criterio | Estado |
|---|---|
| Todo RF tiene origen (T1–T4, RN, OE o RNF) y criterio de verificación | ✔ |
| T1–T4 tienen al menos un RF cada una | ✔ |
| Ningún requisito usa términos sin métrica («rápido», «amigable») | ✔ |
| Todo valor sin fuente está marcado «Propuesto» y listado | ✔ |
| Sin pasarela real ni almacenamiento de datos de tarjeta | ✔ |
| Mensajes de usuario sin texto literal | ✔ |
| Conciliación con el prototipo de frontend | No requerida (decisión del equipo) |
| Columna HU de la matriz de trazabilidad | Pendiente (se llena en el backlog) |
| Alcance CR-01 incorporado (RF-EXP, RN-21 a RN-28) | ✔ |
| Revisión del equipo | Pendiente |

---

## Autoverificación

**Número de RF por módulo:** CAT 4 · EXP 11 · REC 13 · PRO 5 · RES 8 · PAG 8 · CNF 4 · GEN 6 — **59 en total** (48 de la versión 1.0 y 11 nuevos de CR-01).

**Cobertura T1–T4:** T1 → RF-REC-01 a 08 y RF-RES-07; T2 → RF-CAT-01 a 04, RF-EXP-03, 04, RF-REC-06, 10, 11; T3 → RF-PRO-01 a 05; T4 → RF-REC-03, 07, 10, 11, 12, 13. Cada una tiene al menos un RF.

**Requisitos sin origen:** 0.

**Valores «Propuesto» a validar:** porcentajes de compromiso del presupuesto por modalidad (RN-11); reparto por rubro (RN-12); criterio de selección por modalidad (RN-13); rango de presupuesto 1.000.000–50.000.000 COP, invitados 1–500 y tipos de evento (RN-19); formato del número de reserva (RN-18); tarjetas de prueba (RN-17); teléfono de 10 dígitos (RF-RES-03); entretenimiento opcional (RN-03); todos los RNF marcados «Propuesto» (tiempos de respuesta, versiones de Android e iOS, áreas táctiles, tamaño de texto, arranque en frío, cobertura ≥ 80 %, prefijo `/api/v1`).

**Diferencias y pendientes que afectan este documento:** pago simulado frente a la Entrega 1 (C-1, S-02); rol de Juan Manuel por confirmar (P-02); sobrecarga de David con backend y pruebas (R-09). Resueltos: framework móvil (P-04), responsable de pruebas (P-07) y prototipo sin conciliar (P-08).
