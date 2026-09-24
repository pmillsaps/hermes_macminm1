# Hermes Backup Manifest

**Generated:** 2026-09-24 03:00:18
**Host:** Vera
**Source:** `/Users/paulmillsaps/.hermes`

## Included

| Path | Description |
|------|-------------|
| `config.yaml` | Main Hermes configuration (models, display, compression, etc.) |
| `profile.yaml` | UI profile settings |
| `channel_directory.json` | Notification channel registry |
| `skills/` | All skill definitions (SKILL.md, references, templates, scripts) |
| `cron/jobs.json` | Scheduled cron job definitions |
| `scripts/` | Custom scripts (e.g., wiki-vault-ingest) |
| `hooks/` | Hook definitions (if any) |
| `platforms/` | Platform pairing & rate limit state |
| `desktop/interrupted_turns.json` | Interrupted turn recovery state |

## Excluded (secrets/runtime)

- `auth.json` — authentication tokens
- `shared/nous_auth.json` — OAuth credentials
- `vault/` — vault files
- `state.db`, `kanban.db`, `projects.db` — runtime databases
- `sessions/` — active session data
- `logs/` — log files
- `cache/` — model/tool caches
- `models_dev_cache.json` — large model catalog cache
- `gateway_state.json`, `processes.json` — runtime state
- `spawn-ledger.json` — spawn tracking
- `hermes-agent/` — bundled Hermes Agent source
- `node_modules/` — bundled dependencies
- `bin/` — runtime binaries
- `backups/`, `sandboxes/` — internal backup/sandbox dirs
