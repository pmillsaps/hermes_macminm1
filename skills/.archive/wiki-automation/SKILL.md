---
name: wiki-automation
description: "Automated wiki maintenance with git sync and batch ingest."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wiki, automation, git, cron, batch, ingest]
    category: productivity
    related_skills: [llm-wiki]
---

# Wiki Automation

Automate maintenance of a markdown knowledge base: git synchronization,
incremental ingest with change detection, batch processing via subagents, and
timing analytics for capacity planning.

## When This Skill Activates

Use this skill when the user:
- Sets up cron/scheduled jobs for wiki maintenance
- Wants to ingest many files from a vault or folder into a wiki
- Asks for git sync workflows for a wiki repository
- Needs batch processing of wiki sources with progress tracking
- Asks about timing, throughput, or backlog projections for wiki ingest
- Configures automated delivery of wiki reports (Telegram, Discord, email)

## Git Sync Workflow

If the wiki is a git repository, treat it as the source of truth across machines:

**Session start:**
```bash
cd /path/to/wiki && git pull origin main
```

**After every change:**
```bash
git add -A && git commit -m "<descriptive message>" && git push origin main
```

**Rules:**
- Never leave commits unpushed — the user's preference is always push after changes.
- Pull before pushing if multiple machines write to the repo.
- Include the nature of changes in commit messages.

## Incremental Ingest with Change Detection

When ingesting files from an external source (Obsidian vault, folder of articles), do NOT copy files into `raw/`. The canonical location is the source of truth. Track ingest state with hashes:

**State file:** `~/.hermes/scripts/wiki-vault-ingest-state.json`
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
      {"timestamp": "2026-09-19T05:00:00", "file_count": 100, "duration_seconds": 803}
    ]
  }
}
```

**Workflow:**
1. Walk source files in priority order (highest-value folders first).
2. Compute SHA-256 of each file.
3. Compare to stored hash — skip if unchanged, process if new or changed.
4. After processing, update the state file with new hashes and timing data.

**Why:** Copying duplicates wastes disk and creates two sources of truth that can drift. Hash-based tracking is idempotent — re-running the ingest only processes what changed.

## Batch Processing via Subagents

For large batches (50+ files), spawn a subagent rather than processing inline:

```
delegate_task(
  goal="Process N files into the LLM Wiki...",
  context="Full file list, hashes, wiki conventions, schema rules...",
  output_schema={...}
)
```

**Context must include** (subagents have no conversation history):
- Full file list with paths and hashes
- Wiki path, domain, conventions
- Existing page counts
- Schema rules (frontmatter, tags, thresholds)
- Output expectations (report format)

**Background results return as a new message** — never poll or wait. End your turn after dispatching.

## Timing Analytics

Record duration per batch to enable capacity planning:

```bash
python3 ~/.hermes/scripts/wiki-vault-ingest.py record <duration_seconds> <file_count>
python3 ~/.hermes/scripts/wiki-vault-ingest.py summary
```

**Metrics tracked:**
- Average batch duration
- Min/max batch duration
- Remaining file count
- Projected remaining time (remaining_batches × avg_duration)

**Report to user after each batch:**
```
📊 Vault Ingest Report
- Files ingested today: N
- Duration: Xs
- Avg batch time: Xs (over N batches)
- Remaining: N files (~N batches, ~N min projected)
```

## Automation Setup

### Cron Jobs (Hermes cronjob_manage)

| Job | Schedule | Purpose |
|---|---|---|
| Vault Ingest | Daily 2am | Ingest N files from source |
| Wiki Lint | Weekly Monday 9am | Health check: orphans, broken links, staleness |

**Deliver target grammar:**
- `local` — save only, no delivery
- `telegram:<chat_id>` — direct message
- `telegram:<chat_id>:<thread_id>` — forum topic
- `all` — all connected channels

### Multiple Notification Channels

Track configured channels in memory. When the user adds a new channel (Discord, email), update deliver targets for existing cron jobs.

## Pitfalls

- **Don't copy source files** — read directly from canonical locations, track with hashes.
- **Never leave commits unpushed** — git sync is the durability layer.
- **Always provide full context to subagents** — they know nothing of the conversation.
- **Don't poll subagent transcripts** — end your turn; results arrive as a new message.
- **Hash the file content, not metadata** — frontmatter dates/titles may change without meaningful content change.
- **Keep state files in `~/.hermes/scripts/`** — not in the wiki repo (they're execution tooling, not content).
- **Rotate batch history** — keep last 100 batches to avoid unbounded state file growth.
- **Don't create `raw/` duplicates when source already exists externally** — `raw/` is for sources that have NO canonical home (e.g., scraped web content).
- **Index.md truncates on write_file** — when appending to long files like index.md, use patch tool with unique surrounding context, not write_file.
- **write_file may not persist on first use in subagents** — if file creation appears to succeed but file doesn't exist, fall back to terminal-based writing.