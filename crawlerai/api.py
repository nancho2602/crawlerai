import asyncio
import re
from typing import Any, List

try:  # optional dependency
    from fastapi import FastAPI, HTTPException  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional
    FastAPI = None  # type: ignore

    class HTTPException(Exception):  # type: ignore[no-redef]
        def __init__(self, status_code: int, detail: str) -> None:
            super().__init__(detail)
            self.status_code = status_code


try:  # optional dependency
    from pydantic import BaseModel  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional

    class BaseModel:  # type: ignore[no-redef]
        def __init__(self, **data: Any) -> None:
            for key, value in data.items():
                setattr(self, key, value)


try:  # optional dependency
    from dotenv import load_dotenv  # type: ignore[import-not-found]

    load_dotenv()
except Exception:  # pragma: no cover - optional
    pass

try:  # optional dependency
    import google.generativeai as genai  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional
    genai = None  # type: ignore

try:  # optional dependency
    from crawl4ai import (  # type: ignore[import-not-found]
        AsyncWebCrawler,
        BrowserConfig,
        CacheMode,
        CrawlerMonitor,
        CrawlerRunConfig,
        MemoryAdaptiveDispatcher,
    )
except Exception:  # pragma: no cover - optional
    AsyncWebCrawler = None  # type: ignore
    BrowserConfig = CacheMode = CrawlerMonitor = CrawlerRunConfig = MemoryAdaptiveDispatcher = None  # type: ignore


class SitemapPayload(BaseModel):
    """Request payload containing raw sitemap XML."""

    sitemap_xml: str


class CrawlResponse(BaseModel):
    """Response model for each crawled page."""

    url: str
    status_code: int
    content_preview: str | None = None
    llm_summary: str | None = None
    metadata: dict[str, Any] | None = None
    internal_links_count: int | None = None
    external_links_count: int | None = None


if FastAPI is not None:
    app = FastAPI()
else:  # pragma: no cover - optional

    class DummyApp:
        def post(self, *args: Any, **kwargs: Any):
            def decorator(func):
                return func

            return decorator

    app = DummyApp()


@app.post("/crawl", response_model=list[CrawlResponse])
async def crawl_sitemap(payload: SitemapPayload) -> List[CrawlResponse]:
    if AsyncWebCrawler is None:
        raise HTTPException(500, "crawl4ai is not installed")

    urls = re.findall(r"<loc>(.*?)</loc>", payload.sitemap_xml)
    if not urls:
        raise HTTPException(400, "No URLs found in sitemap")

    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, check_robots_txt=True, stream=False
    )
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=10,
        monitor=CrawlerMonitor(),
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(
            urls=urls, config=run_config, dispatcher=dispatcher
        )

    if not results:
        raise HTTPException(400, "Failed to crawl URLs")

    tasks = [process_result_with_llm(r) for r in results if r.success]
    return await asyncio.gather(*tasks)


async def process_result_with_llm(result: Any) -> CrawlResponse:
    """Generate a summary for ``result`` using a local LLM when available."""

    content_preview: str | None = None
    llm_summary: str | None = None

    if getattr(result, "markdown", None):
        clean_text = " ".join(result.markdown.split())
        content_preview = (
            clean_text[:150] + "..." if len(clean_text) > 150 else clean_text
        )
        if genai is not None:
            try:
                model = genai.GenerativeModel("gemma-2b-it")  # type: ignore[attr-defined]
                prompt = (
                    "Please summarize the following webpage content in 2-3 sentences, "
                    "focusing on its main purpose and key information. Here is the content:\n\n---\n\n"
                    + clean_text[:4000]
                )
                response = await model.generate_content_async(prompt)
                llm_summary = response.text  # type: ignore[assignment]
            except Exception as exc:  # pragma: no cover - runtime only
                llm_summary = f"Could not generate summary: {exc}"

    internal_links_count = (
        len(result.links.get("internal", []))
        if getattr(result, "links", None)
        else None
    )
    external_links_count = (
        len(result.links.get("external", []))
        if getattr(result, "links", None)
        else None
    )

    return CrawlResponse(
        url=result.url,
        status_code=result.status_code,
        content_preview=content_preview,
        llm_summary=llm_summary,
        metadata=getattr(result, "metadata", None),
        internal_links_count=internal_links_count,
        external_links_count=external_links_count,
    )


__all__ = ["app", "crawl_sitemap", "process_result_with_llm", "CrawlResponse"]
