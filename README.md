# crawlerai

A simple site crawler that can collect pages from a sitemap or by walking links
starting from a homepage. Each page's text content is stored in a JSON file.
When the optional `--report` flag is supplied the crawler will attempt to
generate a marketing and SEO report for each page using a HuggingFace
`transformers` text-generation pipeline (for example `google/gemma-2b-it`).

## Usage

```bash
python -m crawlerai.crawler https://example.com --limit 10 --output site.json
```

Use the `--sitemap` flag if the URL points directly to a sitemap file. Pass
`--report` to generate a report with a local model. The `transformers` package
and the chosen model weights must be installed separately.
