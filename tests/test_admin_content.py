"""Mirror tests for HU-018 admin content (spec 018, RNF literales / constitución #1).

TC-018-014: the 14 contractual literals of the «Textos de interfaz
(contractuales)» table of spec 018 and the 6 functional labels must match
``tests/expected_content.py`` character by character; «Confirmada»/«Cancelada»
are reused from ``appointment_content`` without duplicating the text.
TC-018-015: ``admin_content`` must only import stdlib and ``consultorio``;
``requirements.txt`` keeps only Flask and gunicorn.
"""

import ast
import sys
from pathlib import Path

from consultorio.config import Config
from consultorio.content import admin_content as admin
from consultorio.content import appointment_content

from tests import expected_content as expected

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ADMIN_CONTENT_PATH = PROJECT_ROOT / "consultorio" / "content" / "admin_content.py"
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"

# Trazabilidad: tabla «Textos de interfaz (contractuales)» de la spec 018,
# incluida la fila «Cita ya cancelada» de la enmienda 2026-11-05. Literales
# hardcodeados a propósito: el test no lee el Markdown en tiempo de ejecución.
CONTRACTUAL_LITERALS = {
    "ADMIN_PAGE_TITLE": "Gestión de citas",
    "ADMIN_CANCEL_TITLE": "Cancelar cita",
    "ADMIN_CANCEL_NOTICE": (
        "La cita quedará Cancelada, el horario se liberará y el paciente "
        "recibirá la notificación."
    ),
    "ADMIN_CANCEL_BUTTON": "Sí, cancelar cita",
    "ADMIN_RESCHEDULE_TITLE": "Reprogramar cita",
    "ADMIN_RESCHEDULE_NOTICE": (
        "Se cancelará la cita actual y se registrará una nueva. El paciente "
        "recibirá la cancelación y la nueva confirmación."
    ),
    "ADMIN_RESCHEDULE_BUTTON": "Sí, reprogramar",
    "ADMIN_BACK_BUTTON": "Volver",
    "ADMIN_CANCEL_SUCCESS": "Cita cancelada.",
    "ADMIN_RESCHEDULE_SUCCESS_TEMPLATE": "Cita reprogramada. Nueva cita #{id}.",
    "ADMIN_ACCESS_DENIED": "No tienes acceso a la gestión de citas.",
    "ADMIN_APPOINTMENT_NOT_FOUND": "No encontramos esa cita. Revisa la referencia.",
    "ADMIN_MSG_ALREADY_CANCELLED": "La cita ya estaba cancelada.",
    "ADMIN_SLOT_TAKEN": "Ese horario ya está ocupado. Elige otro.",
}

# Functional labels (plan 018, D6). Not contractual copy.
FUNCTIONAL_LABELS = {
    "ADMIN_LABEL_SERVICE": "Servicio",
    "ADMIN_LABEL_NEW_DATE": "Nueva fecha",
    "ADMIN_LABEL_TIME": "Hora",
    "ADMIN_LABEL_SUMMARY": "Resumen de la cita",
    "ADMIN_LABEL_PATIENT": "Paciente",
    "ADMIN_LABEL_STATUS": "Estado",
}


def test_tc_018_014_literales_admin_coinciden_con_expected_content_y_tabla_spec() -> None:
    # 14 contractual literals: module == mirror == spec, character by character.
    for name, spec_text in CONTRACTUAL_LITERALS.items():
        assert getattr(admin, name) == spec_text, name
        assert getattr(expected, name) == spec_text, name

    # 6 functional labels: module == expected_content.
    for name, label in FUNCTIONAL_LABELS.items():
        assert getattr(admin, name) == label, name
        assert getattr(expected, name) == label, name

    # Exactly the 20 ADMIN_ constants, no more and no less.
    exported = {name for name in vars(admin) if name.startswith("ADMIN_")}
    assert exported == set(CONTRACTUAL_LITERALS) | set(FUNCTIONAL_LABELS)

    # «Confirmada»/«Cancelada» are reused from appointment_content, not duplicated.
    assert admin.STATUS_CONFIRMED_LABEL is appointment_content.STATUS_CONFIRMED_LABEL
    assert admin.STATUS_CANCELLED_LABEL is appointment_content.STATUS_CANCELLED_LABEL
    assert admin.STATUS_CONFIRMED_LABEL == expected.STATUS_CONFIRMED_LABEL
    assert admin.STATUS_CANCELLED_LABEL == expected.STATUS_CANCELLED_LABEL
    assert admin.STATUS_CONFIRMED_LABEL == "Confirmada"
    assert admin.STATUS_CANCELLED_LABEL == "Cancelada"

    # The reused status labels are not part of the 20 admin literals.
    admin_values = {getattr(admin, name) for name in exported}
    assert "Confirmada" not in admin_values
    assert "Cancelada" not in admin_values

    # The occupied-slot literal is the spec 018 one, not the appointment one.
    assert admin.ADMIN_SLOT_TAKEN != appointment_content.MSG_SLOT_TAKEN


def test_tc_018_015_sin_dependencias_nuevas() -> None:
    tree = ast.parse(ADMIN_CONTENT_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "admin_content must use absolute imports"
            assert node.module is not None
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots, "admin_content must import consultorio"
    for root in imported_roots:
        assert root == "consultorio" or root in sys.stdlib_module_names, root

    requirement_lines = [
        line.strip()
        for line in REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert requirement_lines == ["Flask", "gunicorn"]
