from flask import Blueprint, render_template

from consultorio.services.contact_service import get_contact_view
from consultorio.services.home_service import get_home_view

bp = Blueprint("contact", __name__)


@bp.get("/contacto")
def contacto() -> str:
    return render_template(
        "contact/index.html", view=get_home_view(), contact=get_contact_view()
    )
