# Vault Ingest Pipeline — Detailed Reference

## Hash Schema

```json
{
  "ingested": {
    "relative/path/to/file.md": {
      "ingested": "2026-09-19",
      "sha256": "abc123...",
      "last_processed": "2026-09-19T05:30:00",
      "pages_updated": 5
    }
  },
  "timing": {
    "batches": [
      {
        "timestamp": "2026-09-19T05:00:00",
        "file_count": 100,
        "duration_seconds": 1554,
        "pages_updated": 42
      }
    ]
  },
  "last_batch": "2026-09-19T07:00:00"
}
```

## Script Commands

```bash
# Get next batch of files to process
python3 ~/.hermes/scripts/wiki-vault-ingest.py batch [size]

# Record batch timing and update state
python3 ~/.hermes/scripts/wiki-vault-ingest.py record <duration_seconds> <file_count> [file:hash ...]

# Show progress summary
python3 ~/.hermes/scripts/wiki-vault-ingest.py summary

# Show current counts
python3 ~/.hermes/scripts/wiki-vault-ingest.py status
```

## Mechanical vs. LLM Ingest

Two fundamentally different approaches:

| Approach | What it does | Rate | Creates new pages? | Use when |
|---|---|---|---|---|
| **Mechanical** (Python script) | Text-matches vault content against existing wiki slugs, bumps dates, adds source refs | 1,000–60,000/min | No | Updating existing pages after bulk import, adding source references |
| **LLM-based** (file-by-file tool calls) | Reads each file, extracts entities/concepts, reasons about page creation/updates | 3–10/min | Yes | Deep ingest, new page creation, entity extraction |

**Critical distinction:** Mechanical ingest only updates pages that already exist. It cannot create new entity or concept pages. LLM ingest is required for genuine content analysis.

## Realistic Timing

| Method | Realistic Duration (100 files) | Notes |
|---|---|---|
| Mechanical script | 5–30 seconds | Fast but shallow — no new pages |
| LLM file-by-file | 15–30 minutes | Deep but slow — creates new pages |
| Subagent delegation | Variable | Risk of token limit failures |

## State Recovery

If the state file is lost or corrupted:

1. **Rebuild from scratch:** Reset state to `{"ingested": {}, "timing": {"batches": []}}`. Reprocessing is idempotent — existing wiki pages will be updated, not duplicated.
2. **Partial recovery:** If you have the old state file, copy the `ingested` dict into the new state file.
3. **After recovery:** Run `summary` to verify counts match expectations.

## Cron Automation

For ongoing daily ingest:

| Job | Schedule | Delivery |
|---|---|---|
| Vault Ingest | Daily 2am | Telegram (or user preference) |
| Weekly Lint | Monday 9am | Telegram (or user preference) |

**Reporting preference:** Configure the ingest cron to report **only at completion** (after all batches are processed), not per-batch. Per-batch reports flood the user with noise. The prompt should instruct the agent to loop through batches until `NO_FILES` is returned, then send a single summary.

## Common Frontmatter Issues

- **`@url:` wrapper:** Some vault exports wrap URLs as `source: "@url:`https://...`"`. Fix with regex: `re.sub(r'source:\s*"@url:`([^`]+)`"', r'source: "\1"', content, flags=re.MULTILINE)`
- **Missing `sources` field:** Add to frontmatter after `tags:` line.
- **Stale `updated` date:** Always bump to today's date when a page is touched during ingest.
