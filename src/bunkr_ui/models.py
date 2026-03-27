from pydantic import BaseModel


class MediaItem(BaseModel):
    filename: str
    file_type: str
    thumbnail_url: str
    file_url: str
    size: int | None = None


class Album(BaseModel):
    album_id: str
    title: str
    items: list[MediaItem]


class SearchResult(BaseModel):
    title: str
    album_url: str
    album_id: str
    file_count: int | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    current_page: int
    total_pages: int
