---
name: wiki-vault-ingest
description: "Sync Obsidian vault markdown to LLM Wiki with hash tracking."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wiki, obsidian, vault, ingest, hash, sync]
    category: research
    related_skills: [llm-wiki, obsidian]
---

# Wiki Vault Ingest Pipeline

Sync an Obsidian vault (or any markdown source directory) into an LLM Wiki using hash-based change detection. No file duplication — source files stay in their canonical locations.

## When This Skill Activates

Use when:
- The wiki sources live in an Obsidian vault or existing directory
- You need to batch-process many markdown files into wiki pages
- You want to track which files have been ingested and skip unchanged ones
- Setting up cron automation for ongoing wiki maintenance

## Core Concept: Hash-Based Tracking

Instead of copying source files into `raw/`, track ingest state with SHA-256 hashes:

```json
{
  "ingested": {
    "relative/path/to/file.md": {
      "ingested": "2026-09-19",
      "sha256": "abc123...",
      "last_processed": "2026-09-19T05:30:00"
    }
  },
  "timing": {
    "batches": [
      {"timestamp": "2026-09-19T05:00:00", "file_count": 100, "duration_seconds": 1554}
    ]
  }
}
```

**Why:** Copying duplicates storage and creates drift risk. Hash tracking gives skip-if-unchanged behavior without duplication.

## Workflow

### 1. Get Next Batch
```bash
python3 ~/.hermes/scripts/wiki-vault-ingest.py batch 100
```

Output:
```
BATCH:100
SKIPPED_UNCHANGED:93
SKIPPED_EXCLUDED:0
FILE:path/to/file.md|sha256hash
...
```

### 2. Process Each File
- Read the vault file from its canonical location
- Extract entities and concepts
- Search existing wiki pages (search_files across entities/ and concepts/)
- Create new pages only if they meet Page Thresholds (2+ source mentions, or central to one source)
- Update existing pages with new information (bump `updated` date)
- Ensure bidirectional links (min 2 outbound links per page)

### 3. Record State
```bash
END=$(date +%s); DURATION=$((END - START))
python3 ~/.hermes/scripts/wiki-vault-ingest.py record $DURATION 100 'file1:hash1' 'file2:hash2' ...
```

### 4. Update Wiki Navigation
- Add new pages to `index.md` under correct section (use `patch`, not `write_file` — see pitfalls)
- Update `log.md` with batch entry
- Git commit and push if the wiki is a repo

### 5. Verify State
```bash
python3 ~/.hermes/scripts/wiki-vault-ingest.py status
python3 ~/.hermes/scripts/wiki-vault-ingest.py summary
```

## Folder Priority

Process high-value folders first. Example order for AI/ML domain:

```
AI, Programming, Agents, Prompts, Tools, Hardware, Hermes, DeepSeek, Llama, Kimi, Qwen, Ollama,
LLM Comparisons, Money Making, Productivity, AI News, N8N, MCP, RAG, Coursiv, Local AI Setup,
Automation, Trading, Stock Analysis, Personal Finance, Video, Business Ideas, Writing, Education,
Design, Work, OpenClaw, Voice Scribe, OCR, Social Media, AI Apps, 0-ToDo, Todo, Research, Software,
SAAS, Photography, PKM, Obsidian, Models, Financial, Deepseek Harness, Hermes Skill Prompts, Skills
```

## Excluded Folders

```
1-Inbox, wiki, _global, Clippings, .obsidian, .git
```

## Cron Automation

Set up two cron jobs for ongoing maintenance:

| Job | Schedule | Purpose |
|---|---|---|
| Vault Ingest | Daily 2am | Process new/changed sources in batches (e.g., 100 files) |
| Weekly Lint | Monday 9am | Health check: orphans, broken links, stale pages, index gaps |

**Delivery:** Use `deliver: "telegram:<channel_id>"` to send reports to messaging platforms.

**Git sync:** Every session starts with `git pull`. After changes, `git add -A && git commit -m "..." && git push origin main`.

## Pitfalls

- **Verify state after subagent runs** — check that `ingested` dict is populated and `duration_seconds` is reasonable (1000-2000s per 100 files). Subagents may skip state recording or corrupt timing with timestamps (values in the millions indicate a timestamp was stored as duration).
- **Filename Unicode normalization** — vault files often contain smart quotes (`'`), em-dashes (`—`), or hair spaces (`\u200a`). Normalize filenames before matching against hash lists, or use case-insensitive fallback.
- **Index.md truncation risk** — when inserting into large index files, use `patch` for targeted insertions rather than `write_file` (which can truncate). If write_file truncates, restore via `git checkout` and retry with patch.
- **Duplicate detection across slug variants** — entities like `perplexity` vs `perplexity-ai` or `codex` vs `codex-cli` may already exist under different slugs. Always search before creating.
- **Subagent template markers** — when delegating to subagents, never pass template markers like `<duration_seconds>`. Substitute real values before dispatch.

## Timing Benchmarks

| Batch Size | Avg Duration | Notes |
|---|---|---|
| 100 files | ~26 min | First batch includes setup overhead |
| 100 files | ~27 min | Steady state (hash-based, no copying) |

## State Recovery

If the state file is lost or corrupted:

1. Rebuild hashes: `find /vault/root -name "*.md" -exec sha256sum {} \;`
2. Reprocess all files (idempotent — existing wiki pages will be updated, not duplicated)
3. The `ingested` dict will repopulate on the next `record` call

If `duration_seconds` is unreasonably large (millions), the subagent likely stored a timestamp instead of a duration. Edit the state file directly to correct it.

## References

- **`references/vault-ingest-pipeline.md`** — Hash schema, script commands, timing benchmarks, and recovery procedures. Load when setting up or troubleshooting the ingest pipeline.