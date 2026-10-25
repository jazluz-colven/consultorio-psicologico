"""Mirror tests for HU-017 cancellation content (spec 017, RF-2/3/4/7/9/12/13).

TC-017-010: every contractual literal and functional label in
``consultorio/content/cancellation_content.py`` must match
``tests/expected_content.py`` character by character; the shown status
«Cancelada» is reused from ``appointment_content`` without duplicating text.
"""

from consultorio.content import appointment_content
from consultorio.content import cancellation_content as cc

from tests import expected_content as expected


def test_tc_017_010_los_literales_contractuales_coinciden_con_el_espejo() -> None:
    mirror = {
        "CANCEL_PAGE_TITLE": expected.CANCEL_PAGE_TITLE,
        "CANCEL_NOTICE": expected.CANCEL_NOTICE,
        "CANCEL_CONFIRM_BUTTON": expected.CANCEL_CONFIRM_BUTTON,
        "CANCEL_BACK_BUTTON": expected.CANCEL_BACK_BUTTON,
        "CANCEL_SUCCESS_TITLE": expected.CANCEL_SUCCESS_TITLE,
        "CANCEL_SUCCESS_MESSAGE": expected.CANCEL_SUCCESS_MESSAGE,
        "MSG_VERIFICATION_FAILED": expected.MSG_VERIFICATION_FAILED,
        "MSG_ALREADY_CANCELLED": expected.MSG_ALREADY_CANCELLED,
        "MSG_NOTICE_PERIOD": expected.MSG_NOTICE_PERIOD,
        "CANCEL_BUTTON_LABEL": expected.CANCEL_BUTTON_LABEL,
        "EMAIL_CANCEL_LINK_LABEL": expected.EMAIL_CANCEL_LINK_LABEL,
    }
    for name, literal in mirror.items():
        assert getattr(cc, name) == literal, name


def test_tc_017_010_los_literales_coinciden_caracter_a_caracter_con_la_spec() -> None:
    assert cc.CANCEL_PAGE_TITLE == "Cancelar cita"
    assert cc.CANCEL_NOTICE == (
        "Si cancelas tu cita, este horario quedará libre y no podrás "
        "recuperarlo desde aquí."
    )
    assert cc.CANCEL_CONFIRM_BUTTON == "Sí, cancelar mi cita"
    assert cc.CANCEL_BACK_BUTTON == "No, volver"
    assert cc.CANCEL_SUCCESS_TITLE == "Cita cancelada"
    assert cc.CANCEL_SUCCESS_MESSAGE == (
        "Tu cita ha sido cancelada. El horario ya está disponible para "
        "otra persona."
    )
    assert cc.MSG_VERIFICATION_FAILED == (
        "No pudimos verificar tu cita. Revisa los datos e inténtalo de nuevo."
    )
    assert cc.MSG_ALREADY_CANCELLED == "Esta cita ya fue cancelada."
    assert cc.MSG_NOTICE_PERIOD == (
        "Solo puedes cancelar tu cita desde el sitio con al menos 3 horas "
        "de anticipación. Si necesitas cancelar con menos tiempo, "
        "contáctate con el consultorio."
    )
    assert cc.CANCEL_BUTTON_LABEL == "Cancelar cita"
    assert cc.EMAIL_CANCEL_LINK_LABEL == "Cancelar cita"


def test_tc_017_010_el_estado_cancelada_se_reutiliza_sin_duplicar_texto() -> None:
    assert cc.STATUS_CANCELLED_LABEL is appointment_content.STATUS_CANCELLED_LABEL
    assert cc.STATUS_CANCELLED_LABEL == appointment_content.STATUS_CANCELLED_LABEL
    assert cc.STATUS_CANCELLED_LABEL == expected.STATUS_CANCELLED_LABEL
    assert cc.STATUS_CANCELLED_LABEL == "Cancelada"


def test_tc_017_010_las_etiquetas_funcionales_coinciden_con_el_espejo() -> None:
    mirror = {
        "LABEL_REFERENCE": expected.LABEL_REFERENCE,
        "LABEL_DOCUMENT_NUMBER": expected.LABEL_DOCUMENT_NUMBER,
        "LABEL_SERVICE": expected.LABEL_SERVICE,
        "LABEL_DATE": expected.LABEL_DATE,
        "LABEL_TIME": expected.LABEL_TIME,
        "LABEL_STATUS": expected.LABEL_STATUS,
    }
    for name, label in mirror.items():
        assert getattr(cc, name) == label, name
    assert cc.LABEL_REFERENCE == "Referencia de la cita"
    assert cc.LABEL_DOCUMENT_NUMBER == "Número de documento"
    assert cc.LABEL_SERVICE == "Servicio"
    assert cc.LABEL_DATE == "Fecha"
    assert cc.LABEL_TIME == "Hora"
    assert cc.LABEL_STATUS == "Estado"


def test_tc_017_010_el_titulo_y_el_boton_comparten_el_mismo_texto() -> None:
    # The spec lists both literals with the same text (plan 017, D5).
    assert cc.CANCEL_PAGE_TITLE == "Cancelar cita"
    assert cc.CANCEL_BUTTON_LABEL == "Cancelar cita"
    assert cc.CANCEL_PAGE_TITLE == cc.CANCEL_BUTTON_LABEL
    assert cc.EMAIL_CANCEL_LINK_LABEL == cc.CANCEL_BUTTON_LABEL
