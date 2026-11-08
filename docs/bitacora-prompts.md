# Bitácora de prompts

Registre aquí, por cada tarea, el prompt dado al agente y el resultado (una fila por tarea). Es parte de la definición de terminado.

| Fecha | HU / Tarea | Persona | Prompt (resumen o enlace) | Resultado y ajustes manuales |
|---|---|---|---|---|
| 2026-11-07 | HU_EU_01_12 / T_HU_EU_01_12_2 | David | Implementar GET /home con destacados y conteo de proveedores por rubro | Endpoint listo con orden por calificación y conteo, validado con pruebas para /api/v1/home |
| 2026-11-07 | HU_EU_01_01 / T_HU_EU_01_01_2 | David | Definir el esquema de entrada de POST /recommendations con validación de rangos | Esquema agregado con validación de presupuesto, tipo de evento e invitados; pruebas de API en verde |
| 2026-11-07 | HU_EU_01_02 / T_HU_EU_01_02_1 | David | Conectar POST /recommendations al catálogo y mapear la salida de dominio al contrato de paquetes | Consulta de servicios elegibles y respuesta con desglose implementadas; `make check` verificado. La operación real depende de `recomendar()` de T_HU_EU_01_03_1, aún pendiente |
