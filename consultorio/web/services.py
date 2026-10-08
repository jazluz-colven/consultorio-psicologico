from flask import Blueprint, render_template

from consultorio.services.home_service import get_home_view
from consultorio.services.services_service import get_services_view

bp = Blueprint("services", __name__)


@bp.get("/servicios")
def servicios() -> str:
    return render_template(
        "services/index.html", view=get_home_view(), services=get_services_view()
    )
