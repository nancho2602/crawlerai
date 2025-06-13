# crawlerai

A simple site crawler that can collect pages from a sitemap or by walking links starting from a homepage. Each page's text content is stored in a JSON file. Optionally, the tool can use a local LLM to generate a marketing and SEO report for every page. The LLM part is stubbed out and requires additional packages and model weights.

## Usage

```bash
python -m crawlerai.crawler https://example.com --limit 10 --output site.json
```

Use the `--sitemap` flag if the URL points directly to a sitemap file. Pass `--report` to attempt generating an SEO report with a local model (requires `transformers` and the specified model weights).
