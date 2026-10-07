from flask import Blueprint, render_template

from consultorio.services.home_service import HomeView, get_home_view

bp = Blueprint("home", __name__)


@bp.get("/")
def index() -> str:
    view: HomeView = get_home_view()
    return render_template("home/index.html", view=view)
