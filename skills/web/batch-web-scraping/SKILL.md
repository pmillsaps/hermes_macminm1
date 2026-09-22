---
name: batch-web-scraping
description: Scanning many URLs, especially JS-rendered SPAs.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [web, scraping, batch, browser]
    related_skills: [blocked-page-recovery]
---

# Batch Web Scraping

Use this skill when you need to scan many URLs for structured data extraction, especially when:
- The target pages are JS-rendered single-page apps (SPAs) that curl can only see the shell of
- You need to rate-limit requests to avoid bot detection or IP blocks
- URLs follow a predictable pattern (e.g., date-based) and you need to discover which ones resolve
- You need to consolidate extracted data into a single combined output file

## Procedure

### 1. Pre-check with curl (fast, no rendering)

For batch scanning, first use curl with a short timeout and `-o /dev/null -w '%{http_code}'` to identify which URLs resolve before committing to browser rendering:

```
curl -sL --max-time 5 -o /dev/null -w '%{http_code}' 'https://example.com/path'
```

- HTTP 200 → page exists
- HTTP 000 → DNS failure or connection refused (page doesn't exist)
- HTTP 301/302 → follows redirects automatically with `-L`; check final URL to detect date-redirect patterns

### 2. Rate limiting

Always insert a delay between requests when scanning multiple URLs:
- 5 seconds minimum for the same domain (avoid bot detection)
- Use `time.sleep(5)` in a Python loop or shell `sleep 5` between curl calls
- Longer delays (10-30s) if the site shows any signs of rate-limiting

### 3. Render JS-rendered pages with the browser tool

When curl returns a page but the content is in `<script>` tags or the body is empty, the page is JS-rendered. Use the browser tool:

```python
browser_exec("new_tab('https://example.com/page')")
```

Then extract text content:

```python
browser_exec("print(js('document.body.innerText'))")
```

### 4. Recover from stale tabs

If you get a `WebSocket connection closed` or `Runtime.evaluate timed out` error:

```python
browser_exec("ensure_real_tab()")
```

Then retry the navigation. This recovers from crashed or stale browser tabs without restarting the session.

### 5. Extract structured data from rendered text

After getting `document.body.innerText`, parse the text content for the structured data you need. The text is plain rendered DOM text — use regex or string matching to extract:
- URLs (look for patterns like `https://github.com/owner/repo`)
- Stats (look for patterns like `★ 12.3k` or `Language · Python`)
- Descriptions (usually in predictable positions relative to headings or "View on GitHub" markers)

### 6. Handle redirect-to-nearest patterns

Some date-based URLs redirect to the nearest valid date rather than returning 404. Check the page title or content against the requested date:
- If you request `2026-08-06` but the title says "August 7, 2026", the page redirected
- Deduplicate in your final output — don't include the same content twice under different dates

### 7. Consolidate into a single file

When the user asks for results from multiple pages in one document:
- Build the markdown programmatically in Python (string concatenation or list joining)
- Write once with `write_file` rather than appending repeatedly
- Use a consistent section separator (e.g., `---` between dates)
- Include a header with metadata (scan range, source, date format)

## Pitfalls

- **Curl sees only the shell of JS-rendered pages.** Always verify that curl output contains actual content, not just `<html><head>` and script tags. If `document.body.innerText` is what you need, you must use the browser.
- **Assuming non-resolving URLs means "no content."** Some domains don't resolve at all (DNS failure, HTTP 000) for dates where no episode was published. This is different from a 404. Treat HTTP 000 as "skip" rather than "retry."
- **Running many browser tabs without cleanup.** Each `new_tab()` opens a new tab. For batches of 10+, the browser can become sluggish. If you hit timeouts, add a small delay between tab openings or reuse tabs with `goto_url()`.
- **Forgetting to deduplicate redirects.** If Aug 06 redirects to Aug 07, scanning both produces identical content. Always compare titles or content hashes before adding to your output.
- Not rate-limiting on the user's behalf. The user said "wait about 5 seconds between each page attempt" — honor this precisely. Bot detection on content sites can result in IP blocks or CAPTCHAs that waste more time than the delay.

## See also

- `references/date-scanning.md` — date-based URL scanning, redirect-to-nearest patterns, and deduplication
