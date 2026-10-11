"""Confirmation e-mail literals (HU-008); identifiers in English, texts in Spanish.

Contractual copy from spec 008 (amended 2026-10-10); mirrored in
tests/expected_content.py. No logic, no database access here.
"""

from consultorio.content.automation_content import (
    DETAIL_INVALID_RESPONSE_TEMPLATE,
    DETAIL_TIMEOUT,
    DETAIL_UNEXPECTED,
    DETAIL_UNAVAILABLE,
)

# Subject and sender
EMAIL_SUBJECT_TEMPLATE: str = (
    "Confirmación de tu cita — {service_name} · {date_label} · {time}"
)
EMAIL_SENDER_NAME: str = "Carolina Gómez"

# Body (plain-text part; the HTML part uses the same labels)
EMAIL_BODY_HEADER: str = "Tu cita ha sido registrada. Estos son los datos de la reserva:"
EMAIL_LABEL_SERVICE: str = "Servicio"
EMAIL_LABEL_DATE: str = "Fecha"
EMAIL_LABEL_TIME: str = "Hora"
EMAIL_LABEL_STATUS: str = "Estado"
EMAIL_LABEL_REFERENCE: str = "Referencia de la reserva"
EMAIL_FOOTER: str = (
    "Guarda este correo como comprobante de tu reserva. "
    "Si necesitas modificar o cancelar tu cita, "
    "contáctate con el consultorio."
)
EMAIL_GREETING_TEMPLATE: str = "Hola {patient_name}:"

# Readable Spanish dates (RNF: clear and legible delivery)
WEEKDAYS_ES: tuple[str, ...] = (
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
)

MONTHS_ES: tuple[str, ...] = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)

# New failure reasons (Spanish)
MSG_APPOINTMENT_INCOMPLETE: str = "Datos de la cita incompletos."
DETAIL_EMAIL_NOT_CONFIGURED: str = "Envío de correo no configurado."
DETAIL_INVALID_RECIPIENT: str = (
    "Dirección de correo del paciente ausente o no válida."
)

# HTML template (Q1: Serenity Natural palette, inline styles, no remote assets)
EMAIL_HTML_TEMPLATE: str = """<!DOCTYPE html>
<html lang="es">
<body style="margin:0; padding:0; background-color:#F7F3EA; font-family:'Segoe UI', Helvetica, Arial, sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F7F3EA; padding:24px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px; width:100%; background-color:#F7F3EA; border:1px solid #E8D5B5;">
          <tr>
            <td style="background-color:#B8D8CE; color:#30454B; padding:20px 28px; font-size:20px; font-weight:600;">
              {sender_name}
            </td>
          </tr>
          <tr>
            <td style="padding:24px 28px 8px 28px; color:#30454B; font-size:16px;">
              {greeting}
            </td>
          </tr>
          <tr>
            <td style="padding:8px 28px; color:#30454B; font-size:15px;">
              {body_header}
            </td>
          </tr>
          <tr>
            <td style="padding:8px 28px 4px 28px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F7F3EA; border-left:4px solid #D99A7A; border-top:1px solid #E8D5B5; border-right:1px solid #E8D5B5; border-bottom:1px solid #E8D5B5;">
                <tr>
                  <td style="padding:12px 16px; color:#30454B; font-size:14px; border-bottom:1px solid #E8D5B5;">{label_service}</td>
                  <td style="padding:12px 16px; color:#30454B; font-size:15px; font-weight:600; border-bottom:1px solid #E8D5B5;">{service_name}</td>
                </tr>
                <tr>
                  <td style="padding:12px 16px; color:#30454B; font-size:14px; border-bottom:1px solid #E8D5B5;">{label_date}</td>
                  <td style="padding:12px 16px; color:#30454B; font-size:15px; font-weight:600; border-bottom:1px solid #E8D5B5;">{date_label}</td>
                </tr>
                <tr>
                  <td style="padding:12px 16px; color:#30454B; font-size:14px; border-bottom:1px solid #E8D5B5;">{label_time}</td>
                  <td style="padding:12px 16px; color:#30454B; font-size:15px; font-weight:600; border-bottom:1px solid #E8D5B5;">{time}</td>
                </tr>
                <tr>
                  <td style="padding:12px 16px; color:#30454B; font-size:14px; border-bottom:1px solid #E8D5B5;">{label_status}</td>
                  <td style="padding:12px 16px; color:#30454B; font-size:15px; font-weight:600; border-bottom:1px solid #E8D5B5;">{status}</td>
                </tr>
                <tr>
                  <td colspan="2" style="background-color:#E8D5B5; padding:12px 16px; color:#30454B; font-size:14px;">
                    {label_reference}: #{appointment_id}
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 28px 24px 28px; color:#30454B; font-size:14px;">
              {footer}
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
