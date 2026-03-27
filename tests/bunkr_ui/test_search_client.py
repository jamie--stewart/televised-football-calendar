from src.bunkr_ui.services.search_client import _parse_search_html


class TestParseSearchHtml:
    def test_extracts_album_links(self):
        html = """
        <html><body>
            <a href="/a/abc123"><h2>Test Album</h2></a>
            <a href="/a/def456"><h2>Another Album</h2></a>
        </body></html>
        """
        results, total_pages = _parse_search_html(html, "https://example.com")
        assert len(results) == 2
        assert results[0]["album_id"] == "abc123"
        assert results[0]["title"] == "Test Album"
        assert results[1]["album_id"] == "def456"

    def test_full_url_album_links(self):
        html = """
        <html><body>
            <a href="https://bunkr.cr/a/abc123"><span>Test</span></a>
        </body></html>
        """
        results, _ = _parse_search_html(html, "https://example.com")
        assert len(results) == 1
        assert results[0]["album_url"] == "https://bunkr.cr/a/abc123"

    def test_pagination_extraction(self):
        html = """
        <html><body>
            <a href="/?search=test&page=1">1</a>
            <a href="/?search=test&page=2">2</a>
            <a href="/?search=test&page=5">5</a>
        </body></html>
        """
        _, total_pages = _parse_search_html(html, "https://example.com")
        assert total_pages == 5

    def test_no_results(self):
        html = "<html><body><p>No results</p></body></html>"
        results, total_pages = _parse_search_html(html, "https://example.com")
        assert len(results) == 0
        assert total_pages == 1

    def test_file_count_extraction(self):
        html = """
        <html><body>
            <a href="/a/abc123">
                <h2>Test Album</h2>
                <span class="count">42 files</span>
            </a>
        </body></html>
        """
        results, _ = _parse_search_html(html, "https://example.com")
        assert results[0]["file_count"] == 42

    def test_relative_urls_get_base(self):
        html = '<html><body><a href="/a/test"><span>Album</span></a></body></html>'
        results, _ = _parse_search_html(html, "https://bunkr-albums.io")
        assert results[0]["album_url"] == "https://bunkr-albums.io/a/test"
