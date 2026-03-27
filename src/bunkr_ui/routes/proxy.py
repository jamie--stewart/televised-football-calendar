from urllib.parse import urlparse

from fastapi import APIRouter, Request
from fastapi.responses import Response, StreamingResponse

router = APIRouter()

ALLOWED_DOMAINS = {
    "bnkr.b-cdn.net",
    "cdn.bunkr.cr",
    "cdn.bunkr.si",
    "cdn.bunkr.ph",
    "cdn.bunkr.sk",
    "i.bunkr.cr",
    "i-burger.bunkr.cr",
    "burger.bunkr.cr",
    "pizza.bunkr.cr",
    "milkshake.bunkr.cr",
}


def _is_allowed_domain(url: str, extra_domain: str | None = None) -> bool:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
    except Exception:
        return False

    allowed = ALLOWED_DOMAINS.copy()
    if extra_domain:
        allowed.add(extra_domain)

    return any(hostname == d or hostname.endswith(f".{d}") for d in allowed)


@router.get("/proxy/thumb")
async def proxy_thumbnail(request: Request, url: str) -> Response:
    settings = request.app.state.settings
    client = request.app.state.http_client

    if not _is_allowed_domain(url, settings.cdn_domain):
        return Response(status_code=403, content="Domain not allowed")

    try:
        resp = await client.get(url)
        resp.raise_for_status()
    except Exception:
        return Response(status_code=502, content="Failed to fetch thumbnail")

    content_type = resp.headers.get("content-type", "image/jpeg")

    return Response(
        content=resp.content,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/proxy/media")
async def proxy_media(request: Request, url: str) -> StreamingResponse:
    settings = request.app.state.settings
    client = request.app.state.http_client

    if not _is_allowed_domain(url, settings.cdn_domain):
        return Response(status_code=403, content="Domain not allowed")

    try:
        resp = await client.stream("GET", url)
        content_type = resp.headers.get("content-type", "application/octet-stream")
    except Exception:
        return Response(status_code=502, content="Failed to fetch media")

    async def stream_response():
        try:
            async for chunk in resp.aiter_bytes(chunk_size=8192):
                yield chunk
        finally:
            await resp.aclose()

    return StreamingResponse(
        stream_response(),
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
