import re

import httpx
from bs4 import BeautifulSoup

from src.bunkr_ui.models import SearchResponse, SearchResult
from src.bunkr_ui.services.query_parser import ParsedQuery, filter_results


async def search_albums(
    client: httpx.AsyncClient,
    base_url: str,
    query: ParsedQuery,
    page: int = 1,
) -> SearchResponse:
    upstream_query = query.to_upstream_query()
    url = f"{base_url}/"
    params = {"search": upstream_query, "page": page}

    response = await client.get(url, params=params)
    response.raise_for_status()

    raw_results, total_pages = _parse_search_html(response.text, base_url)

    if not query.is_empty:
        raw_results = filter_results(raw_results, query)

    results = [
        SearchResult(
            title=r["title"],
            album_url=r["album_url"],
            album_id=r["album_id"],
            file_count=r.get("file_count"),
        )
        for r in raw_results
    ]

    return SearchResponse(
        query=upstream_query,
        results=results,
        current_page=page,
        total_pages=total_pages,
    )


def _parse_search_html(html: str, base_url: str) -> tuple[list[dict], int]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict] = []

    for card in soup.select("a[href*='/a/']"):
        title_el = card.select_one("h2, h3, .title, span")
        title = title_el.get_text(strip=True) if title_el else card.get_text(strip=True)
        album_url = card.get("href", "")

        if not album_url.startswith("http"):
            album_url = f"{base_url}{album_url}"

        album_id_match = re.search(r"/a/([^/?#]+)", album_url)
        album_id = album_id_match.group(1) if album_id_match else ""

        file_count = None
        count_el = card.select_one(".count, .file-count, .files")
        if count_el:
            count_text = count_el.get_text(strip=True)
            count_match = re.search(r"(\d+)", count_text)
            if count_match:
                file_count = int(count_match.group(1))

        if album_id:
            results.append(
                {
                    "title": title,
                    "album_url": album_url,
                    "album_id": album_id,
                    "file_count": file_count,
                }
            )

    total_pages = 1
    pagination = soup.select("a[href*='page=']")
    for link in pagination:
        href = link.get("href", "")
        page_match = re.search(r"page=(\d+)", href)
        if page_match:
            total_pages = max(total_pages, int(page_match.group(1)))

    return results, total_pages
