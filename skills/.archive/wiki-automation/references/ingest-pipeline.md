# Ingest Pipeline Reference

## Script: `~/.hermes/scripts/wiki-vault-ingest.py`

### Commands

| Command | Usage | Output |
|---|---|---|
| `batch [size]` | `python3 wiki-vault-ingest.py batch 100` | `BATCH:N\nSKIPPED_UNCHANGED:N\nSKIPPED_EXCLUDED:N\nFILE:rel/path\|hash` |
| `record <duration> <count> [file:hash ...]` | `python3 wiki-vault-ingest.py record 803 100 AI/file.md:abc123` | JSON timing summary |
| `summary` | `python3 wiki-vault-ingest.py summary` | JSON timing summary |
| `status` | `python3 wiki-vault-ingest.py status` | Human-readable status |

### State Schema

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
      {
        "timestamp": "2026-09-19T05:00:00",
        "file_count": 100,
        "duration_seconds": 803
      }
    ]
  }
}
```

### Timing Summary Output

```json
{
  "total_batches": 5,
  "total_files_ingested": 500,
  "total_duration_minutes": 42.3,
  "avg_batch_seconds": 803.2,
  "min_batch_seconds": 612.0,
  "max_batch_seconds": 1024.5,
  "remaining_files": 1983,
  "remaining_batches": 20,
  "projected_remaining_minutes": 268.0,
  "projected_remaining_hours": 4.47
}
```

## Cron Job Configuration

### Create
```
tool_call(name="cronjob_manage", arguments={
  "action": "create",
  "name": "Wiki Vault Ingest (100/day)",
  "schedule": "0 2 * * *",
  "prompt": "...",
  "deliver": "telegram:<channel_id>",
  "skills": ["llm-wiki"],
  "workdir": "/path/to/wiki"
})
```

### Update deliver target
```
tool_call(name="cronjob_manage", arguments={
  "action": "update",
  "job_id": "<id>",
  "deliver": "telegram:<id>,discord:<id>"
})
```

### List jobs
```
tool_call(name="cronjob_manage", arguments={"action": "list"})
```

## Folder Priority Order

Default priority (highest value first):
1. AI, Programming, Agents, Prompts, Tools, Hardware
2. Hermes, DeepSeek, Llama, Kimi, Qwen, Ollama
3. LLM Comparisons, Money Making, Productivity, AI News
4. N8N, MCP, RAG, Coursiv, Local AI Setup, Automation
5. Trading, Stock Analysis, Personal Finance, Video
6. Business Ideas, Writing, Education, Design, Work
7. OpenClaw, Voice Scribe, OCR, Social Media, AI Apps
8. 0-ToDo, Todo, Research, Software, SAAS, Photography
9. PKM, Obsidian, Models, Financial, Deepseek Harness
10. Hermes Skill Prompts, Skills, Side Hustles

Customize per-user by editing the script.

## Excluded Folders

- `1-Inbox/` — ephemeral, not ready for ingest
- `wiki/` — the wiki itself (avoid recursion)
- `_global/` — Obsidian global assets
- `Clippings/` — raw clippings, not structured content
- `.obsidian/` — Obsidian config
- `.git/` — version control