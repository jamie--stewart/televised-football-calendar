import json
import re

import httpx
from bs4 import BeautifulSoup

from src.bunkr_ui.models import Album, MediaItem
from src.bunkr_ui.services.crypto import decrypt_url


async def fetch_album(
    client: httpx.AsyncClient,
    viewer_base_url: str,
    cdn_domain: str,
    album_id: str,
) -> Album:
    url = f"{viewer_base_url}/a/{album_id}"
    response = await client.get(url)
    response.raise_for_status()

    html = response.text
    title = _extract_title(html)
    items = _extract_items_from_js(html, cdn_domain)

    if not items:
        items = _extract_items_from_html(html, viewer_base_url, cdn_domain)

    resolved_items = []
    for item in items:
        try:
            resolved = await _resolve_file_url(client, viewer_base_url, item)
            resolved_items.append(resolved)
        except Exception:
            resolved_items.append(item)

    return Album(album_id=album_id, title=title, items=resolved_items)


def _extract_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"]
    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text(strip=True).replace("| Bunkr", "").strip()
    return "Untitled Album"


def _extract_items_from_js(html: str, cdn_domain: str) -> list[MediaItem]:
    match = re.search(r"window\.albumFiles\s*=\s*(\[.*?]);", html, re.DOTALL)
    if not match:
        return []

    try:
        files = json.loads(match.group(1))
    except json.JSONDecodeError:
        return _parse_album_files_loosely(match.group(1), cdn_domain)

    items = []
    for f in files:
        name = f.get("name", "unknown")
        file_type = _guess_file_type(name)
        uuid = f.get("uuid", "")
        thumb = f"https://{cdn_domain}/thumbs/{uuid}.jpg" if uuid else ""
        file_url = f.get("url", "")

        items.append(
            MediaItem(
                filename=name,
                file_type=file_type,
                thumbnail_url=thumb,
                file_url=file_url,
                size=f.get("size"),
            )
        )

    return items


def _parse_album_files_loosely(raw: str, cdn_domain: str) -> list[MediaItem]:
    items = []
    blocks = raw.split("},")
    for block in blocks:
        name_match = re.search(r'"name"\s*:\s*"([^"]*)"', block)
        uuid_match = re.search(r'"uuid"\s*:\s*"([^"]*)"', block)
        url_match = re.search(r'"url"\s*:\s*"([^"]*)"', block)
        size_match = re.search(r'"size"\s*:\s*(\d+)', block)

        name = name_match.group(1) if name_match else "unknown"
        uuid = uuid_match.group(1) if uuid_match else ""
        file_url = url_match.group(1) if url_match else ""
        size = int(size_match.group(1)) if size_match else None

        if name != "unknown" or uuid:
            thumb = f"https://{cdn_domain}/thumbs/{uuid}.jpg" if uuid else ""
            items.append(
                MediaItem(
                    filename=name,
                    file_type=_guess_file_type(name),
                    thumbnail_url=thumb,
                    file_url=file_url,
                    size=size,
                )
            )

    return items


def _extract_items_from_html(html: str, viewer_base_url: str, cdn_domain: str) -> list[MediaItem]:
    soup = BeautifulSoup(html, "html.parser")
    items = []

    for div in soup.select("div.theItem, div.grid-item, div[class*='item']"):
        link = div.find("a", href=True)
        if not link:
            continue

        href = link["href"]
        if not href.startswith("http"):
            href = f"{viewer_base_url}{href}"

        img = div.find("img")
        thumb = ""
        if img and img.get("src"):
            thumb = img["src"]
            if not thumb.startswith("http"):
                thumb = f"https://{cdn_domain}{thumb}"

        filename = href.split("/")[-1]
        items.append(
            MediaItem(
                filename=filename,
                file_type=_guess_file_type(filename),
                thumbnail_url=thumb,
                file_url=href,
            )
        )

    return items


async def _resolve_file_url(
    client: httpx.AsyncClient,
    viewer_base_url: str,
    item: MediaItem,
) -> MediaItem:
    if not item.file_url or "b-cdn.net" in item.file_url:
        return item

    slug_match = re.search(r"/[fvi]/(.+?)$", item.file_url)
    if not slug_match:
        return item

    slug = slug_match.group(1)
    api_url = f"{viewer_base_url}/api/vs"

    try:
        resp = await client.post(api_url, json={"slug": slug})
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return item

    if data.get("encrypted") and data.get("url"):
        resolved_url = decrypt_url(data["url"], data.get("timestamp"))
    elif data.get("url"):
        resolved_url = data["url"]
    else:
        return item

    return item.model_copy(update={"file_url": resolved_url})


def _guess_file_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in ("mp4", "mkv", "avi", "mov", "wmv", "webm", "m4v"):
        return "video"
    return "image"
