#!/usr/bin/env python3
"""Genera un prompt de implementación por tarea a partir del Backlog Extendido (TSV).

Uso (desde la raíz de un repo con docs/ y el .tsv):
    python3 tools/hu_prompt.py                 # escribe prompts/<tarea>.md para las tareas de este repo
    python3 tools/hu_prompt.py T_HU_EU_01_02_1 # imprime el prompt de una tarea
Parámetro --repo api|app define qué tareas se generan (por defecto se deduce de la carpeta).
"""
import csv, glob, os, sys

SAD = "docs/20261105_SAD_EU.md"
BD = "docs/20261105_BD_BaseDatos_EU.md"
SRS = "docs/20261105_SRS_Requisitos_EU.md"
PB = "docs/20261105_PB_ProductBacklog_EU.md"

LECTURA = {
    "HU_EU_01_01": [f"{SAD} §5.1, §6.1 (entradas y validaciones) y §7.1 (POST /recommendations)", f"{SRS} RF-REC-01 a RF-REC-03, RF-EXP-10 y RN-19 (rangos, Propuesto)"],
    "HU_EU_01_02": [f"{SAD} §5.1 (secuencia) y §7.1 (respuesta de POST /recommendations)", f"{BD} §11 (consultas de servicios elegibles)", f"{SRS} RF-REC-04 a RF-REC-09"],
    "HU_EU_01_03": [f"{SAD} §6 completo (algoritmo), ADR-03 y ADR-04", f"{SRS} RN-01, RN-02, RN-03, RN-06, RN-11 a RN-16", f"{BD} §2.3 y §2.4"],
    "HU_EU_01_04": [f"{SAD} §7.2 (error uniforme) y §7.3 (red móvil)", f"{SRS} RF-GEN-01 a RF-GEN-06, RF-EXP-11, RNF-FIA-01 y RNF-FIA-02"],
    "HU_EU_01_12": [f"{SAD} §5.6 (exploración), ADR-10, ADR-11 y §7.1 (GET /home)", f"{SRS} RF-EXP-01, RF-EXP-02, RF-EXP-10, RN-24 a RN-26", f"{BD} §2.1, §2.8 y §11 (v_providers)"],
    "HU_EU_02_05": [f"{SAD} §5.6, ADR-11 y §7.1 (GET /providers)", f"{BD} §2.1, §5 (índices) y §11 (listado con filtros)", f"{SRS} RF-EXP-03, RF-CAT-01, RF-CAT-04, RN-24 a RN-26"],
    "HU_EU_02_15": [f"{SAD} §5.6, ADR-11 y §7.1 (GET /providers: filtros y sort)", f"{BD} §5 (índices) y §11", f"{SRS} RF-EXP-04, RF-CAT-02, RF-CAT-03 y RN-26 (orden, Propuesto)"],
    "HU_EU_02_08": [f"{SAD} §5.6 y §7.1 (GET /providers/{{id}})", f"{BD} §2.1, §2.2, §2.8, §2.9 y §11", f"{SRS} RN-07, RN-24, RN-25, RF-PRO-01 a RF-PRO-05"],
    "HU_EU_02_16": [f"{SAD} ADR-12 y §7.1 (GET /providers/{{id}}: images y reviews)", f"{BD} §2.8 y §2.9", f"{SRS} RF-EXP-05, RF-EXP-06, RN-24, RN-27"],
    "HU_EU_02_13": [f"{SAD} §5.7, ADR-10 y §7.1 (POST /quotes)", f"{SRS} RF-EXP-07, RF-EXP-08, RN-22, RN-23", f"{BD} §2.3 y §2.4"],
    "HU_EU_02_06": [f"{SAD} §5.2, §5.7, ADR-09 y §7.1 (POST /quotes)", f"{SRS} RN-01, RN-05, RN-22, RN-23, RF-REC-11 a RF-REC-13, RF-EXP-07, RF-EXP-08"],
    "HU_EU_02_07": [f"{SAD} §7.1 (forma de los paquetes de POST /recommendations)", f"{SRS} RF-REC-10, RNF-USA-01"],
    "HU_EU_03_09": [f"{SAD} §5.3, ADR-09 y §7.1 (POST /reservations con modality 'personalizado')", f"{BD} §2.5, §2.6, §4 y §7", f"{SRS} RN-08, RN-18, RN-20, RN-21, RN-22, RF-RES-01 a RF-RES-08"],
    "HU_EU_03_10": [f"{SAD} §5.4 (secuencia y estados), ADR-05 y §7.1 (POST /payments)", f"{BD} §2.7 y §6", f"{SRS} RN-09, RN-17, RF-PAG-01 a RF-PAG-08"],
    "HU_EU_03_11": [f"{SAD} §5.5 (secuencia) y §7.1 (GET /reservations/{{code}})", f"{SRS} RF-CNF-01 a RF-CNF-04"],
    "HU_EU_03_14": [f"{SAD} ADR-13 y §7.1 (GET /providers con bbox)", f"{SRS} RF-EXP-09 y RN-28 (coordenadas aproximadas)", f"{BD} §2.1"],
}

def repo_of(task_type: str) -> str:
    # Las pruebas pueden cubrir la API o la app: se generan en ambos repos.
    return {"Frontend móvil": "app", "Pruebas": "both"}.get(task_type, "api")

def load():
    tsv = glob.glob("docs/*PBS_ProductBacklogExtended*.tsv")[0]
    with open(tsv, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f, delimiter="\t", quotechar='"'))
    head, rows = rows[0], rows[1:]
    hus = {r[1]: dict(zip(head, r)) for r in rows if r[0] == "HU"}
    tasks = [dict(zip(head, r)) for r in rows if r[0] == "Tarea"]
    return hus, tasks

def build(task, hu, repo):
    hid, tid = task["Id de la Historia"], task["Id de Tarea"]
    same = [t for t in load()[1] if t["Id de la Historia"] == hid]
    otras = "\n".join(f"- {t['Id de Tarea']} ({t['Tipo de tarea']}, {t['Estimación (SP Fibonacci)']} SP): {t['Característica / Funcionalidad']}" for t in same if t["Id de Tarea"] != tid)
    lectura = "\n".join(f"- {x}" for x in LECTURA[hid])
    comando = "make check" if repo == "api" else "npm run check"
    extra = ""
    if task["Tipo de tarea"] == "Frontend móvil":
        extra = "- Verifique la pantalla en emulador o dispositivo con el API desplegado (o local por IP de red) y describa cómo la probó.\n- Mensajes entre comillas simples: úselos literalmente.\n"
    elif task["Tipo de tarea"] == "Pruebas":
        extra = "- Escriba pruebas que verifiquen los criterios de aceptación, incluidos los de fallo; no cambie código de producción salvo para corregir un defecto que las pruebas revelen, y repórtelo.\n"
    elif task["Tipo de tarea"] == "Base de datos":
        extra = "- Los cambios de esquema van en una migración nueva; no edite `0001_schema` (ya es la v2 del marketplace). Mantenga `docs/…BaseDatos…` coherente si cambia algo.\n"
    elif task["Tipo de tarea"] == "Datos/Contenido":
        extra = "- Todo dato es de ejemplo y debe quedar marcado así; sin teléfonos ni correos reales. Respete el formato de `seed/seed.json`.\n"
    elif task["Tipo de tarea"] == "DevOps":
        extra = "- Sin secretos en el repo; variables solo por entorno. Documente cada paso manual (cuentas, variables) en el PR.\n"
    return f"""# Prompt de implementación — {tid}

## 1. Rol
Eres un ingeniero de software senior que trabaja en el repositorio `eventu-{repo}` de EventU, bajo la dirección de {task['Notas del analista'].replace('Responsable propuesto: ','').rstrip('.')}. Implementas **solo esta tarea**, con el cambio mínimo que cumple los criterios, sin inventar estructura.

## 2. Léase primero
1. `CLAUDE.md` de este repo (reglas que no se rompen, estructura y dependencias entre capas).
2. Documentos de esta tarea:
{lectura}
3. La historia completa y sus criterios (sección 3 de este prompt).

## 3. Historia {hid}
**{hu['Rol'] and 'Yo como ' + hu['Rol'] + ', quiero ' + hu['Característica / Funcionalidad'] + ', para ' + hu['Razón / Resultado'] + '.'}**
Épica: {hu['Épica']} · {hu['Sprint']} · Estado de validación: {hu['Estado de validación']} · Prioridad: {hu['Prioridad MoSCoW']}

Criterios de aceptación (son la fuente de verdad; los mensajes entre comillas simples son literales y los marcados «Propuesto» no se cambian en silencio):

{hu['Criterio de Aceptación']}

Observación de la historia: {hu['Observación']}
Notas del analista: {hu['Notas del analista']}

## 4. Su tarea
- **Id:** {tid} · **Tipo:** {task['Tipo de tarea']} · **Estimación:** {task['Estimación (SP Fibonacci)']} SP
- **Qué hacer:** {task['Característica / Funcionalidad']}
- **Por qué esa estimación:** {task['Justificación de estimación']}

Otras tareas de la misma historia (no las haga; solo respete sus interfaces):
{otras or '- (ninguna)'}

## 5. Alcance
- Toque únicamente los archivos necesarios para esta tarea. No refactorice, no cambie contratos del SAD, no toque módulos o pantallas de otras historias.
- Si el SAD, el SRS, el backlog o el prototipo se contradicen o falta un dato, **no lo resuelva en silencio**: elija la lectura más conservadora, anótela en el PR bajo «Supuestos» y pregunte.
- Valores marcados «Propuesto»: déjelos como constantes fáciles de cambiar.

## 6. Proceso
1. Plan breve (máx. 8 líneas): archivos a crear o modificar y pruebas a escribir.
2. Escriba primero las pruebas de los criterios que le corresponden (éxito, validación y fallo).
3. Implemente hasta que pasen. Ejecute `{comando}` y corrija hasta dejarlo en verde.
4. Verifique **cada criterio de aceptación** de la historia que esta tarea cubre.
5. Complete la fila de `docs/bitacora-prompts.md`.
{extra}
## 7. Definición de terminado (de esta tarea)
{task['DoD']}

## 8. Qué debe responder al terminar
1. Lista de criterios de aceptación con estado: cumplido, parcial o fuera de esta tarea (con motivo).
2. Archivos creados o modificados.
3. Resultado de `{comando}`.
4. Supuestos y dudas abiertas.
5. Texto sugerido del PR (título `{tid}: …`).
"""

def main():
    hus, tasks = load()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    repo = next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("--repo=")), None)
    if repo is None:
        repo = "app" if os.path.basename(os.getcwd()).endswith("app") else "api"
    if args:
        t = next(t for t in tasks if t["Id de Tarea"] == args[0])
        r = repo_of(t["Tipo de tarea"])
        print(build(t, hus[t["Id de la Historia"]], repo if r == "both" else r))
        return
    os.makedirs("prompts", exist_ok=True)
    n = 0
    for t in tasks:
        if repo_of(t["Tipo de tarea"]) not in (repo, "both"):
            continue
        with open(f"prompts/{t['Id de Tarea']}.md", "w", encoding="utf-8") as f:
            f.write(build(t, hus[t["Id de la Historia"]], repo))
        n += 1
    print(f"{n} prompts en prompts/")

if __name__ == "__main__":
    main()
