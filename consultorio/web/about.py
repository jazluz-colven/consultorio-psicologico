from flask import Blueprint, render_template

from consultorio.services.about_service import get_about_view
from consultorio.services.home_service import get_home_view

bp = Blueprint("about", __name__)


@bp.get("/nosotros")
def nosotros() -> str:
    return render_template(
        "about/index.html", view=get_home_view(), about=get_about_view()
    )
