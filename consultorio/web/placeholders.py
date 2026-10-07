from flask import Blueprint, abort, render_template

from consultorio.services.home_service import HomeView, find_nav_item, get_home_view

bp = Blueprint("sections", __name__)


def _render_section(section_url: str) -> str:
    item = find_nav_item(section_url)
    if item is None:
        abort(404)
    view: HomeView = get_home_view()
    return render_template(
        "sections/under_construction.html", view=view, section=item.label
    )


@bp.get("/nosotros")
def nosotros() -> str:
    return _render_section("/nosotros")


@bp.get("/servicios")
def servicios() -> str:
    return _render_section("/servicios")


@bp.get("/articulos")
def articulos() -> str:
    return _render_section("/articulos")


@bp.get("/contacto")
def contacto() -> str:
    return _render_section("/contacto")


@bp.get("/citas")
def citas() -> str:
    return _render_section("/citas")
