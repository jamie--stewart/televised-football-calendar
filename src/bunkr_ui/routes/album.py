from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.bunkr_ui.services.album_client import fetch_album

router = APIRouter()


@router.get("/album/{album_id}", response_class=HTMLResponse)
async def view_album(request: Request, album_id: str) -> HTMLResponse:
    templates = request.app.state.templates
    settings = request.app.state.settings
    client = request.app.state.http_client

    try:
        album = await fetch_album(client, settings.viewer_base_url, settings.cdn_domain, album_id)
    except Exception:
        return templates.TemplateResponse(
            request,
            "album.html",
            {"album": None, "error": "Failed to load album. The upstream service may be unavailable."},
        )

    return templates.TemplateResponse(request, "album.html", {"album": album})
