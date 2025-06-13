import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crawlerai.api import crawl_sitemap, SitemapPayload
import asyncio


def test_crawl_sitemap(monkeypatch):
    class DummyCrawler:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def arun_many(self, urls, config, dispatcher):
            class Result:
                def __init__(self, url: str) -> None:
                    self.url = url
                    self.status_code = 200
                    self.success = True
                    self.markdown = "content"
                    self.links = {"internal": [], "external": []}
                    self.metadata = {}

            return [Result(u) for u in urls]

    monkeypatch.setattr("crawlerai.api.AsyncWebCrawler", DummyCrawler)
    monkeypatch.setattr("crawlerai.api.BrowserConfig", lambda **kw: None)
    monkeypatch.setattr("crawlerai.api.CrawlerRunConfig", lambda **kw: None)
    monkeypatch.setattr("crawlerai.api.MemoryAdaptiveDispatcher", lambda **kw: None)
    monkeypatch.setattr("crawlerai.api.CrawlerMonitor", lambda: None)
    monkeypatch.setattr("crawlerai.api.CacheMode", type("CacheMode", (), {"BYPASS": 0}))

    class DummyModel:
        async def generate_content_async(self, prompt: str):
            class Resp:
                text = "summary"

            return Resp()

    monkeypatch.setattr(
        "crawlerai.api.genai",
        type("genai", (), {"GenerativeModel": lambda name: DummyModel()}),
    )

    payload = SitemapPayload(
        sitemap_xml="""<urlset><url><loc>http://a</loc></url></urlset>"""
    )
    responses = asyncio.run(crawl_sitemap(payload))
    assert responses[0].url == "http://a"
    assert responses[0].llm_summary == "summary"
