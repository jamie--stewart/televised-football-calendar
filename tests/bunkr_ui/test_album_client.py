import json

from src.bunkr_ui.services.album_client import (
    _extract_items_from_html,
    _extract_items_from_js,
    _extract_title,
    _guess_file_type,
)


class TestExtractTitle:
    def test_og_title(self):
        html = '<html><head><meta property="og:title" content="My Album"></head></html>'
        assert _extract_title(html) == "My Album"

    def test_title_tag_fallback(self):
        html = "<html><head><title>Cool Stuff | Bunkr</title></head></html>"
        assert _extract_title(html) == "Cool Stuff"

    def test_default_title(self):
        html = "<html><head></head></html>"
        assert _extract_title(html) == "Untitled Album"


class TestExtractItemsFromJs:
    def test_parses_album_files(self):
        files = [
            {"name": "video1.mp4", "uuid": "abc-123", "url": "https://cdn/video1.mp4", "size": 1024},
            {"name": "image1.jpg", "uuid": "def-456", "url": "https://cdn/image1.jpg", "size": 512},
        ]
        html = f"<script>window.albumFiles = {json.dumps(files)};</script>"
        items = _extract_items_from_js(html, "bnkr.b-cdn.net")
        assert len(items) == 2
        assert items[0].filename == "video1.mp4"
        assert items[0].file_type == "video"
        assert items[0].thumbnail_url == "https://bnkr.b-cdn.net/thumbs/abc-123.jpg"
        assert items[1].filename == "image1.jpg"
        assert items[1].file_type == "image"

    def test_no_album_files(self):
        html = "<script>var x = 1;</script>"
        items = _extract_items_from_js(html, "bnkr.b-cdn.net")
        assert items == []


class TestExtractItemsFromHtml:
    def test_extracts_items(self):
        html = """
        <html><body>
            <div class="theItem">
                <a href="/f/video1.mp4">
                    <img src="/thumbs/abc.jpg">
                </a>
            </div>
            <div class="theItem">
                <a href="/v/video2.mp4">
                    <img src="/thumbs/def.jpg">
                </a>
            </div>
        </body></html>
        """
        items = _extract_items_from_html(html, "https://bunkr.cr", "bnkr.b-cdn.net")
        assert len(items) == 2
        assert items[0].filename == "video1.mp4"
        assert items[0].file_url == "https://bunkr.cr/f/video1.mp4"

    def test_no_items(self):
        html = "<html><body><p>Empty</p></body></html>"
        items = _extract_items_from_html(html, "https://bunkr.cr", "bnkr.b-cdn.net")
        assert items == []


class TestGuessFileType:
    def test_video_extensions(self):
        for ext in ("mp4", "mkv", "avi", "mov", "wmv", "webm", "m4v"):
            assert _guess_file_type(f"file.{ext}") == "video"

    def test_image_extensions(self):
        for ext in ("jpg", "png", "gif", "bmp"):
            assert _guess_file_type(f"file.{ext}") == "image"

    def test_no_extension(self):
        assert _guess_file_type("noext") == "image"
