import re

from consultorio.content import appointment_content as ac
from tests import expected_content as expected


def test_booking_hours_son_los_14_slots_exactos_y_ordenados() -> None:
    assert ac.BOOKING_HOURS == expected.BOOKING_HOURS
    assert len(ac.BOOKING_HOURS) == 14
    assert ac.BOOKING_HOURS == sorted(ac.BOOKING_HOURS)
    assert len(set(ac.BOOKING_HOURS)) == 14
    assert all(re.fullmatch(r"[0-9]{2}:[0-9]{2}", h) for h in ac.BOOKING_HOURS)
    assert ac.BOOKING_HOURS[0] == "08:00"
    assert ac.BOOKING_HOURS[7] == "11:30"
    assert ac.BOOKING_HOURS[8] == "14:00"
    assert ac.BOOKING_HOURS[-1] == "16:30"
    assert "12:00" not in ac.BOOKING_HOURS
    assert "13:00" not in ac.BOOKING_HOURS
    assert "17:00" not in ac.BOOKING_HOURS


def test_document_types_son_los_5_tipos_con_etiquetas_espanolas() -> None:
    assert ac.DOCUMENT_TYPES == expected.DOCUMENT_TYPES
    assert [code for code, _ in ac.DOCUMENT_TYPES] == [
        "CC", "TI", "CE", "PASSPORT", "RC",
    ]
    assert ac.DOCUMENT_TYPES[0][1] == "Cédula de ciudadanía"
    assert ac.DOCUMENT_TYPES[1][1] == "Tarjeta de identidad"
    assert ac.DOCUMENT_TYPES[2][1] == "Cédula de extranjería"
    assert ac.DOCUMENT_TYPES[3][1] == "Pasaporte"
    assert ac.DOCUMENT_TYPES[4][1] == "Registro civil"


def test_espejo_de_literales_identico_al_modulo_de_contenido() -> None:
    mirror = {
        "BOOKING_PAGE_TITLE": expected.BOOKING_PAGE_TITLE,
        "MSG_REQUIRED_SERVICE": expected.MSG_REQUIRED_SERVICE,
        "MSG_INVALID_SERVICE": expected.MSG_INVALID_SERVICE,
        "MSG_REQUIRED_DATE": expected.MSG_REQUIRED_DATE,
        "MSG_INVALID_DATE": expected.MSG_INVALID_DATE,
        "MSG_REQUIRED_TIME": expected.MSG_REQUIRED_TIME,
        "MSG_INVALID_TIME": expected.MSG_INVALID_TIME,
        "MSG_REQUIRED_DOC_TYPE": expected.MSG_REQUIRED_DOC_TYPE,
        "MSG_REQUIRED_DOC_NUMBER": expected.MSG_REQUIRED_DOC_NUMBER,
        "MSG_INVALID_DOC_NUMBER": expected.MSG_INVALID_DOC_NUMBER,
        "MSG_REQUIRED_NAME": expected.MSG_REQUIRED_NAME,
        "MSG_INVALID_NAME": expected.MSG_INVALID_NAME,
        "MSG_REQUIRED_EMAIL": expected.MSG_REQUIRED_EMAIL,
        "MSG_INVALID_EMAIL": expected.MSG_INVALID_EMAIL,
        "MSG_REQUIRED_PHONE": expected.MSG_REQUIRED_PHONE,
        "MSG_INVALID_PHONE": expected.MSG_INVALID_PHONE,
        "MSG_SLOT_TAKEN": expected.MSG_SLOT_TAKEN,
        "MSG_NO_HOURS": expected.MSG_NO_HOURS,
        "MSG_INVALID_PARAMS": expected.MSG_INVALID_PARAMS,
        "MSG_SELECT_DATE_HINT": expected.MSG_SELECT_DATE_HINT,
        "BOOKING_BLOCK_MORNING": expected.BOOKING_BLOCK_MORNING,
        "BOOKING_BLOCK_AFTERNOON": expected.BOOKING_BLOCK_AFTERNOON,
        "BOOKING_PATIENT_SECTION_TITLE": expected.BOOKING_PATIENT_SECTION_TITLE,
        "BOOKING_SCHEDULE_SECTION_TITLE": expected.BOOKING_SCHEDULE_SECTION_TITLE,
        "CONFIRMATION_TITLE": expected.CONFIRMATION_TITLE,
        "STATUS_PENDING_LABEL": expected.STATUS_PENDING_LABEL,
        "BOOKING_HELPER": expected.BOOKING_HELPER,
    }
    for name, literal in mirror.items():
        assert getattr(ac, name) == literal, name
    assert ac.STATUS_PENDING == "pending"
    assert ac.BOOKING_PAGE_TITLE == "Agendar cita"
    assert ac.CONFIRMATION_TITLE == "Cita registrada"
    assert ac.STATUS_PENDING_LABEL == "Pendiente"
    assert ac.MSG_SLOT_TAKEN == (
        "Ese horario ya no está disponible. Selecciona otro horario."
    )
