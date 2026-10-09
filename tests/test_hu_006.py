"""HU-006 — user story checks: submit guard, schema and literals (spec 006)."""

import re
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from consultorio.config import Config
from consultorio.content import appointment_content as content

from tests import expected_content as expected

MAIN_CSS = Config.STATIC_DIR / "css" / "main.css"
AVAILABILITY_JS = Config.STATIC_DIR / "js" / "availability.js"
SPECS_DIR = Config.BASE_DIR / "specs"

DIAGNOSTIC = """
SELECT service, date, time, COUNT(*) AS total
FROM appointments
GROUP BY service, date, time
HAVING COUNT(*) > 1
"""

FREE_HOURS = [
    "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00",
    "11:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
]


def _future_weekday() -> str:
    candidate = date.today()
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate.isoformat()


def _form(**overrides: str) -> dict[str, str]:
    base = {
        "service": "nutrition",
        "date": _future_weekday(),
        "time": "08:00",
        "document_type": "CC",
        "document_number": "1234567890",
        "patient_name": "Ana Pérez",
        "email": "ana@correo.com",
        "phone": "3001234567",
    }
    base.update(overrides)
    return base


def _database_path(app) -> Path:
    with app.app_context():
        return Path(app.config["DATABASE_PATH"])


def test_tc_006_011_js_guard_de_envio_en_curso() -> None:
    js = AVAILABILITY_JS.read_text(encoding="utf-8")

    assert re.search(r'addEventListener\(\s*"submit"', js)
    assert re.search(
        r"if\s*\(\s*submitting\s*\)\s*\{[^}]*event\.preventDefault\(\)", js, re.S
    )
    assert "button.disabled = true" in js
    assert 'dataAttr("data-submitting")' in js
    assert 'setAttribute("aria-busy", "true")' in js
    assert "initBookingSubmit" in js
    assert "import " not in js
    assert "import(" not in js
    assert "require(" not in js


def test_tc_006_012_css_estado_en_curso_paleta_justificado_y_sin_desborde() -> None:
    css = MAIN_CSS.read_text(encoding="utf-8")

    assert re.search(
        r"\.appointment__submit:disabled\s*\{[^}]*background-color:\s*var\(--color-support\)",
        css,
        re.S,
    )
    assert re.search(
        r"\.appointment__submit:disabled\s*\{[^}]*cursor:\s*not-allowed", css, re.S
    )
    assert re.search(
        r'\.appointment__form\[aria-busy="true"\]\s*\{[^}]*cursor:\s*wait', css, re.S
    )

    used = set(re.findall(r"#[0-9A-Fa-f]{6}", css))
    assert used
    assert used <= expected.PALETTE
    assert re.search(
        r"\.appointment__helper\s*\{[^}]*text-align:\s*justify;[^}]*hyphens:\s*none",
        css,
    )
    fixed_widths = [
        int(value)
        for value in re.findall(r"\.appointment[^{]*\{[^}]*width:\s*(\d+)px", css)
    ]
    assert all(width <= 375 for width in fixed_widths)


def test_tc_006_013_esquema_unico_y_diagnostico_sin_duplicados(app, client) -> None:
    for index, hour in enumerate(FREE_HOURS):
        assert (
            client.post("/citas", data=_form(time=hour, document_number=f"12345{index}"))
            .status_code
            == 303
        )
    for hour in ("08:00", "09:00"):
        assert (
            client.post(
                "/citas",
                data=_form(
                    service="psychology_integral",
                    time=hour,
                    document_number="55555000",
                ),
            ).status_code
            == 303
        )

    path = _database_path(app)
    connection = sqlite3.connect(str(path))
    try:
        schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'appointments'"
        ).fetchone()[0]
        assert "UNIQUE (service, date, time)" in schema
        duplicates = connection.execute(DIAGNOSTIC).fetchall()
    finally:
        connection.close()
    assert duplicates == []


def test_tc_006_014_espejo_msg_submitting_y_slot_taken_identicos() -> None:
    assert (
        expected.MSG_SUBMITTING
        == content.MSG_SUBMITTING
        == "Registrando tu cita…"
    )
    assert expected.MSG_SLOT_TAKEN == content.MSG_SLOT_TAKEN

    spec_004 = (SPECS_DIR / "004_agendar-cita" / "spec.md").read_text(
        encoding="utf-8"
    )
    spec_005 = (SPECS_DIR / "005_validar-dis-horarios" / "spec.md").read_text(
        encoding="utf-8"
    )
    spec_006 = (SPECS_DIR / "006_evitar-doble-reserva" / "spec.md").read_text(
        encoding="utf-8"
    )
    assert content.MSG_SLOT_TAKEN in spec_004
    assert content.MSG_SUBMITTING in spec_006
    assert content.MSG_SLOT_TAKEN in spec_006
    # La spec 005 no declara este literal: solo reutiliza los suyos propios,
    # de modo que ningún texto contradictorio convive con el de la spec 004.
    assert content.MSG_SLOT_TAKEN not in spec_005


def test_tc_006_015_diagnostico_detecta_duplicados_sin_indice(tmp_path) -> None:
    path = tmp_path / "without_index.db"
    connection = sqlite3.connect(str(path))
    try:
        connection.execute(
            """
            CREATE TABLE appointments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                document_type   TEXT NOT NULL,
                document_number TEXT NOT NULL,
                patient_name    TEXT NOT NULL,
                email           TEXT NOT NULL,
                phone           TEXT NOT NULL,
                service     TEXT NOT NULL,
                date        TEXT NOT NULL,
                time        TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'pending',
                created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
        insert = """
            INSERT INTO appointments (
                document_type, document_number, patient_name, email, phone,
                service, date, time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        row = ("CC", "1234567890", "Ana Pérez", "ana@correo.com", "3001234567",
               "nutrition", "2026-10-12", "08:00")
        connection.execute(insert, row)
        connection.execute(insert, row)
        duplicates = connection.execute(DIAGNOSTIC).fetchall()
    finally:
        connection.close()

    assert len(duplicates) == 1
    service, day, hour, total = duplicates[0]
    assert (service, day, hour) == ("nutrition", "2026-10-12", "08:00")
    assert total == 2
