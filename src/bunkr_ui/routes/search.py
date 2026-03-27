from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.bunkr_ui.services.query_parser import parse_query
from src.bunkr_ui.services.search_client import search_albums

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "search.html", {"query": "", "results": None})


@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = "", page: int = 1) -> HTMLResponse:
    templates = request.app.state.templates
    settings = request.app.state.settings
    client = request.app.state.http_client

    if not q.strip():
        return templates.TemplateResponse(request, "search.html", {"query": q, "results": None})

    parsed = parse_query(q)

    try:
        response = await search_albums(client, settings.search_base_url, parsed, page)
    except Exception:
        return templates.TemplateResponse(
            request,
            "search.html",
            {"query": q, "results": None, "error": "Search failed. The upstream service may be unavailable."},
        )

    context = {
        "query": q,
        "results": response.results,
        "current_page": response.current_page,
        "total_pages": response.total_pages,
    }

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        return templates.TemplateResponse(request, "search_results_partial.html", context)

    return templates.TemplateResponse(request, "search.html", context)
