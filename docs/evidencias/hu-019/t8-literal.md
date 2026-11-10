# Evidencia T8 — Literal contractual `MSG_PERSISTENCE_UNAVAILABLE`

- **Fecha:** 2026-11-10
- **Rama:** `feature/hu-019-migracion-postgres`
- **HEAD:** `8ce511f`
- **Tarea:** T8 — Literal coordinado `MSG_PERSISTENCE_UNAVAILABLE`
- **Autorización:** expresa de la usuaria el 2026-11-10
- **Alcance:** solo constante contractual + espejo + prueba TC-019-011. No se
  implementa T9 (503/UX/templates/JS) ni ninguna otra tarea.

## 1. Trazabilidad

`Spec 019 RF-20 / RNF-5` → `plan.md D12` → `tasks.md T8` → `TC-019-011`.

- **RF-20:** si la base de datos no está disponible, se comunica el literal de
  indisponibilidad aprobado; la incorporación al contrato de contenido de las
  Specs 004/005 y su espejo se realizan mediante enmienda coordinada.
- **RNF-5:** sin regresiones; no cambian los literales contractuales vigentes.
- **D12:** la constante y su espejo exacto entran en el mismo PR; no se modifica
  ningún otro literal.
- **Enmiendas coordinadas:** Spec 004 y Spec 005, enmienda aprobada por la
  usuaria el **2026-11-08**. La Spec 005 reutiliza la clave fijada en la Spec
  004 y no duplica su definición.
- **TC-019-011:** `tests/test_hu_019.py` comprueba el valor literal exacto, la
  igualdad con el espejo y que los literales existentes de las Specs 004/005
  siguen intactos.

## 2. Valor literal exacto y espejo

Valor contractual (86 caracteres):

```text
No pudimos completar tu solicitud en este momento. Inténtalo de nuevo en unos minutos.
```

Representación ASCII verificada en ejecución:

```text
'No pudimos completar tu solicitud en este momento. Int\xe9ntalo de nuevo en unos minutos.'
len= 86
mirror_equal= True
```

- `consultorio/content/appointment_content.py` →
  `MSG_PERSISTENCE_UNAVAILABLE: str`
- `tests/expected_content.py` → `MSG_PERSISTENCE_UNAVAILABLE`
- Ambos valores son idénticos (`mirror_equal= True`).

## 3. Diff acotado

`git diff -- consultorio/content/appointment_content.py tests/expected_content.py`
(solo adiciones; `7 insertions, 0 deletions` por archivo):

```diff
diff --git a/consultorio/content/appointment_content.py b/consultorio/content/appointment_content.py
index b381db3..16d3926 100644
--- a/consultorio/content/appointment_content.py
+++ b/consultorio/content/appointment_content.py
@@ -42,6 +42,13 @@ MSG_NO_HOURS: str = "No hay horarios disponibles para esta fecha."
 MSG_INVALID_PARAMS: str = "Parámetros inválidos."
 MSG_SELECT_DATE_HINT: str = "Selecciona una fecha para ver las horas disponibles."
 
+# Spec 019 RF-20 / RNF-5: persistence unavailable. Contract fixed by the
+# coordinated Specs 004/005 amendment (approved 2026-11-08) and implemented
+# by T8/D12; never reused as a busy-slot (SLOT_TAKEN) message.
+MSG_PERSISTENCE_UNAVAILABLE: str = (
+    "No pudimos completar tu solicitud en este momento. Inténtalo de nuevo en unos minutos."
+)
+
 BOOKING_BLOCK_MORNING: str = "Mañana"
 BOOKING_BLOCK_AFTERNOON: str = "Tarde"
 
diff --git a/tests/expected_content.py b/tests/expected_content.py
index 75dc7ff..a07c95f 100644
--- a/tests/expected_content.py
+++ b/tests/expected_content.py
@@ -211,6 +211,13 @@ MSG_NO_HOURS = "No hay horarios disponibles para esta fecha."
 MSG_INVALID_PARAMS = "Parámetros inválidos."
 MSG_SELECT_DATE_HINT = "Selecciona una fecha para ver las horas disponibles."
 
+# --- Spec 019 RF-20: persistence unavailable (Specs 004/005 coordinated
+# amendment, approved 2026-11-08) — mirror of the contractual literal. ---
+
+MSG_PERSISTENCE_UNAVAILABLE = (
+    "No pudimos completar tu solicitud en este momento. Inténtalo de nuevo en unos minutos."
+)
+
 BOOKING_BLOCK_MORNING = "Mañana"
 BOOKING_BLOCK_AFTERNOON = "Tarde"
 
```

No se elimina ni modifica ninguna línea existente de esos dos archivos.

### Prueba añadida

`tests/test_hu_019.py` (archivo aún sin seguimiento en Git; creado en T5)
incorpora `test_tc_019_011_persistence_unavailable_literal_and_unchanged_mirror`,
que:

- fija el literal aprobado y lo compara con el espejo;
- comprueba que el nuevo literal no se reutiliza como `MSG_SLOT_TAKEN`;
- verifica que los literales existentes de la Spec 004
  (`MSG_REQUIRED_SERVICE`, `MSG_INVALID_SERVICE`, `MSG_REQUIRED_DATE`,
  `MSG_INVALID_DATE`, `MSG_REQUIRED_TIME`, `MSG_INVALID_TIME`,
  `MSG_SLOT_TAKEN`, `MSG_NO_HOURS`, `MSG_INVALID_PARAMS`,
  `MSG_SELECT_DATE_HINT`) y de la Spec 005 (`MSG_OCCUPIED_HOUR`,
  `MSG_CHECKING_HOURS`, `CALENDAR_LEGEND_FREE`, `CALENDAR_LEGEND_FULL`,
  `DAY_LABEL_NO_HOURS`) no cambian ni en el módulo ni en el espejo.

## 4. Comandos y resultados reales

El DSN local se suministró por variable de entorno y **no se registra** en esta
evidencia (redactado como `<DSN local>`).

### 4.1 TC-019-011

```powershell
$env:TEST_DATABASE_URL='<DSN local>'; python -m pytest -q tests/test_hu_019.py -k tc_019_011 -v
```

```text
============================= test session starts =============================
platform win32 -- Python 3.14.8, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Jaz\Documents\Proyectos Python\Consultorio_Carolina
collected 5 items / 4 deselected / 1 selected

tests\test_hu_019.py .                                                   [100%]

======================= 1 passed, 4 deselected in 0.24s =======================
```

**Resultado: 1 PASS / 0 FAIL / 0 SKIP.**

### 4.2 Content + HU-019

```powershell
$env:TEST_DATABASE_URL='<DSN local>'; python -m pytest -q tests/test_appointment_content.py tests/test_hu_019.py
```

```text
........                                                                 [100%]
8 passed in 1.52s
```

**Resultado: 8 PASS / 0 FAIL / 0 SKIP.**

### 4.3 Suite completa contra PostgreSQL real

```powershell
$env:TEST_DATABASE_URL='<DSN local>'; python -m pytest -q
```

```text
........................................................................ [ 18%]
........................................................................ [ 37%]
........................................................................ [ 55%]
........................................................................ [ 74%]
........................................................................ [ 93%]
..........................                                               [100%]
386 passed in 50.50s
```

**Resultado: 386 PASS / 0 FAIL / 0 SKIP.** No hay `skip`, `skipif` ni `xfail`
que oculten falta de PostgreSQL. El conteo es el real verificado (385 de T7 +
TC-019-011).

## 5. Confirmaciones de alcance

- No se modificaron `specs/`, `MEMORY.md` ni `tasks.md`. Las modificaciones que
  `git status` muestra en `specs/004`, `specs/005`, `specs/006`, `specs/010` y
  `MEMORY.md` son cambios previos de T2–T7 (ya presentes al iniciar T8), no de
  esta tarea.
- No se implementó T9: no se tocaron handlers, templates, `availability.js` ni
  servicios; la constante aún no se consume en código de aplicación.
- No se modificó ningún otro literal contractual.
- No se hizo `commit` ni `push`.
- No se registraron credenciales, DSN ni datos personales en esta evidencia.
