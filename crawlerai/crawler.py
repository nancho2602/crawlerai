import argparse
import json
from collections import deque
from html.parser import HTMLParser
from typing import Dict, Iterable, List, Set
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)

    def get_text(self) -> str:
        return " ".join(self.parts)


def _fetch(url: str) -> str:
    """Retrieve the raw HTML for ``url`` using a browser-like user agent."""
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 crawlerai"})
    with urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def extract_links_from_sitemap(url: str) -> List[str]:
    xml_content = _fetch(url)
    root = ET.fromstring(xml_content)
    return [loc.text.strip() for loc in root.findall(".//{*}loc") if loc.text]


def crawl(start_url: str, limit: int = 100) -> Dict[str, str]:
    visited: Set[str] = set()
    to_visit: deque[str] = deque([start_url])
    pages: Dict[str, str] = {}
    domain = urlparse(start_url).netloc
    while to_visit and len(visited) < limit:
        url = to_visit.popleft()
        if url in visited:
            continue
        try:
            html = _fetch(url)
        except Exception:
            continue
        visited.add(url)
        parser = TextExtractor()
        parser.feed(html)
        pages[url] = parser.get_text()
        parser.close()
        for link in _extract_links(html, url):
            parsed = urlparse(link)
            if parsed.netloc == domain and link not in visited:
                to_visit.append(link)
    return pages


def _extract_links(html: str, base: str) -> List[str]:
    class LinkExtractor(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.links: List[str] = []

        def handle_starttag(
            self, tag: str, attrs: List[tuple[str, str | None]]
        ) -> None:
            if tag == "a":
                for k, v in attrs:
                    if k == "href":
                        self.links.append(urljoin(base, v))

    parser = LinkExtractor()
    parser.feed(html)
    parser.close()
    return parser.links


PROMPT_TEMPLATE = (
    "You are an expert SEO assistant. Provide marketing and SEO recommendations\n"
    "for the following web page.\n\n{content}\n"
)


def generate_report(text: str, model_name: str = "google/gemma-2b-it") -> str:
    """Generate an SEO report for ``text`` using a HuggingFace text-generation model."""
    try:
        from transformers import pipeline  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - depends on optional package
        raise RuntimeError(
            "transformers package is required for report generation"
        ) from exc

    generator = pipeline("text-generation", model=model_name)
    prompt = PROMPT_TEMPLATE.format(content=text)
    result = generator(prompt, max_new_tokens=200, do_sample=False)
    return result[0]["generated_text"]


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Crawl a website and optionally run an LLM report."
    )
    parser.add_argument("url", help="Homepage or sitemap URL")
    parser.add_argument("--sitemap", action="store_true", help="URL is a sitemap")
    parser.add_argument(
        "--limit", type=int, default=20, help="Maximum number of pages to crawl"
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate SEO report using a local LLM"
    )
    parser.add_argument(
        "--output", default="results.json", help="Path to save crawl results"
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.sitemap:
        urls = extract_links_from_sitemap(args.url)[: args.limit]
        texts = {url: _fetch(url) for url in urls}
    else:
        texts = crawl(args.url, limit=args.limit)

    results: Dict[str, Dict[str, str]] = {}
    for url, html in texts.items():
        extractor = TextExtractor()
        extractor.feed(html)
        content = extractor.get_text()
        extractor.close()
        entry = {"content": content}
        if args.report:
            entry["report"] = generate_report(content)
        results[url] = entry

    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)


if __name__ == "__main__":
    main()
