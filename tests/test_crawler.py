import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crawlerai import crawler


def test_extract_links_from_sitemap(monkeypatch):
    xml_content = """<?xml version='1.0' encoding='UTF-8'?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>http://example.com/</loc></url>
        <url><loc>http://example.com/about</loc></url>
    </urlset>
    """

    def fake_fetch(url: str) -> str:
        assert url == "http://test/sitemap.xml"
        return xml_content

    monkeypatch.setattr(crawler, "_fetch", fake_fetch)
    urls = crawler.extract_links_from_sitemap("http://test/sitemap.xml")
    assert urls == ["http://example.com/", "http://example.com/about"]
