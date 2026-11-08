# Bitácora de prompts

Registre aquí, por cada tarea, el prompt dado al agente y el resultado (una fila por tarea). Es parte de la definición de terminado.

| Fecha | HU / Tarea | Persona | Prompt (resumen o enlace) | Resultado y ajustes manuales |
|---|---|---|---|---|
| 2026-11-07 | HU_EU_01_12 / T_HU_EU_01_12_2 | David | Implementar GET /home con destacados y conteo de proveedores por rubro | Endpoint listo con orden por calificación y conteo, validado con pruebas para /api/v1/home |
| 2026-11-07 | HU_EU_01_01 / T_HU_EU_01_01_2 | David | Definir el esquema de entrada de POST /recommendations con validación de rangos | Esquema agregado con validación de presupuesto, tipo de evento e invitados; pruebas de API en verde |
| 2026-11-07 | HU_EU_01_02 / T_HU_EU_01_02_1 | David | Conectar POST /recommendations al catálogo y mapear la salida de dominio al contrato de paquetes | Consulta de servicios elegibles y respuesta con desglose implementadas; `make check` verificado. La operación real depende de `recomendar()` de T_HU_EU_01_03_1, aún pendiente |
| 2026-11-07 | HU_EU_01_01 / T_HU_EU_01_01_4 | David | Verificar CI y preparar despliegue Render y URL base de la app | CI y Blueprint de Render ya existían; README documenta configuración manual y `EXPO_PUBLIC_API_BASE_URL`. El despliegue y la configuración móvil quedan pendientes de la cuenta/proyecto externos |
| 2026-11-07 | HU_EU_01_01 / T_HU_EU_01_01_3 | David | Pruebas de validación de POST /recommendations para datos vacíos, inválidos, válidos y fallo inesperado | Pruebas de API ampliadas; `make check` en verde (40 passed, 1 xfailed). Pruebas de la app móvil fuera de este repositorio |
