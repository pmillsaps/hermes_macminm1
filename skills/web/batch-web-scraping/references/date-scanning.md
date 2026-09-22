# Date-based URL scanning pattern

When scanning URLs that follow a date pattern (e.g., `https://YYYY-MM-DD.example.com`), some dates may redirect to the nearest valid date rather than returning 404.

## Detection

After fetching a page, compare the requested date to the page title or content:
- Requested `2026-08-06` → title says "August 7, 2026" → redirected
- Requested `2026-07-01` → title says "July 3, 2026" → redirected

## Deduplication

Track which dates produced identical content (compare titles or content hashes). In the final output, include only unique content under its actual date — not duplicate entries for the dates that redirected.

## Example: githubshow.codeshiftagent.com

URL format: `https://YYYY-MM-DD.githubshow.codeshiftagent.com`

- Scanned 261 dates from 2026-09-18 back to 2026-01-01
- Only 15 returned valid content (most Jan–May URLs didn't resolve)
- Some dates redirected to the nearest valid date (Aug 06 → Aug 07, Jul 01 → Jul 03)
- These are weekly video episodes, not daily — so most dates have no content