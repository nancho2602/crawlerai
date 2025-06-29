# crawlerai

A FastAPI service that crawls a site's pages from a provided sitemap and
summarises each page using a local LLM when available. The crawling logic uses
`crawl4ai` while text summaries are generated with `google.generativeai`.

## Running

Install the optional dependencies and run the server with `uvicorn`:

```bash
pip install crawl4ai google-generativeai python-dotenv fastapi uvicorn
uvicorn crawlerai.api:app --reload
```

Send a POST request to `/crawl` with a raw sitemap XML in the body:

```bash
curl -X POST http://localhost:8000/crawl \
     -H 'Content-Type: application/json' \
     -d '{"sitemap_xml": "<urlset>...</urlset>"}'
```

The response contains a list of pages with an optional LLM summary.
