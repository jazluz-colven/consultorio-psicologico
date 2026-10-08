from flask import Blueprint, render_template, request

from consultorio.services.home_service import get_home_view
from consultorio.services.search_service import STATUS_EMPTY, search

bp = Blueprint("search", __name__)


@bp.get("/buscar")
def index() -> str:
    query = (request.args.get("q") or "").strip()
    hits, status = search(query)

    if status == STATUS_EMPTY:
        template_status = "empty"
    elif not hits:
        template_status = "no_results"
    else:
        template_status = "results"

    return render_template(
        "search/index.html",
        view=get_home_view(),
        status=template_status,
        hits=hits,
        q=query,
    )
