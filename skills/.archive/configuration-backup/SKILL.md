---
name: configuration-backup
description: "Back up config to git. Excludes secrets and schedules runs."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [backup, git, config, secrets, cron, automation]
    category: productivity
---

# Configuration Backup

Back up configuration files to a git repository with secrets exclusion,
manifest generation, and scheduled automated runs.

## When This Skill Activates

Use this skill when the user:
- Wants to back up config files to git (Hermes, dotfiles, app settings)
- Needs automated daily/weekly backups with secrets exclusion
- Sets up a backup repo with .gitignore-based secret filtering
- Schedules backup scripts via cron
- Asks for a manifest showing what is and isn't backed up

## Procedure

### 1. Identify Source & Destination

**Source:** The directory containing config files (e.g., `~/.hermes`, `~/.config`).
**Destination:** A dedicated git repo cloned to a local working directory (e.g., `~/.config-backup-repo`).

### 2. Create the Backup Repository

```bash
gh repo create <username>/<repo-name> --description "..." --public  # or --private
git clone https://github.com/<username>/<repo-name>.git ~/.backup-repo
```

**Rules:**
- Use a descriptive repo name that identifies the machine/purpose.
- Prefer `--private` unless the user explicitly wants public.
- Clone to a stable path outside the source directory (e.g., `~/.backup-repo`).

### 3. Write .gitignore FIRST — Safety Net

Create `.gitignore` in the backup repo before the first backup run. List
all files/patterns that contain secrets or runtime state:

```gitignore
# Secrets / tokens
auth.json
*.auth.json
*.lock
nous_auth.json
vault/

# Runtime state (regenerated on start)
state.db*
kanban.db*
projects.db
processes.json
gateway_state.json
spawn-ledger.json

# Logs & cache
logs/
cache/
*.log

# Build artifacts
node_modules/
*.pyc
__pycache__/

# OS files
.DS_Store

# Large binary caches
models_dev_cache.json
```

**Rule:** The .gitignore is a defense-in-depth safety net. The backup script
itself should also exclude secrets — never rely on .gitignore alone.

### 4. Write the Backup Script

Create a shell script at `~/.backup-repo/backup.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_REPO="$HOME/.backup-repo"
SRC="$HOME/.hermes"
DATE=$(date '+%Y-%m-%d %H:%M:%S')
HOST=$(scutil --get ComputerName 2>/dev/null || hostname)

cd "$BACKUP_REPO"

# Copy config files (explicit allowlist, NOT auth files)
cp "$SRC/config.yaml" config.yaml 2>/dev/null || true
cp "$SRC/profile.yaml" profile.yaml 2>/dev/null || true

# Copy subdirectories (excluding internal metadata)
rsync -a \
  --exclude='.usage.json' \
  --exclude='.bundled_manifest' \
  --exclude='.curator_ledger.jsonl' \
  --exclude='.locks/' \
  "$SRC/skills/" skills/

# Copy runtime configs
mkdir -p cron
cp "$SRC/cron/jobs.json" cron/jobs.json 2>/dev/null || true

mkdir -p scripts
cp "$SRC/scripts/"* scripts/ 2>/dev/null || true

# Generate manifest
cat > MANIFEST.md <<EOF
# Backup Manifest

**Generated:** $DATE
**Host:** $HOST
**Source:** \`$SRC\`

## Included
- config.yaml, profile.yaml
- skills/ (excluding internal metadata)
- cron/jobs.json
- scripts/

## Excluded (secrets/runtime)
- auth.json, nous_auth.json, vault/
- state.db, kanban.db, projects.db
- logs/, cache/, hermes-agent/
EOF

# Commit & push
git add -A
if git diff --cached --quiet; then
  echo "No changes to backup."
else
  git commit -m "Backup: $DATE [$HOST]"
  git push origin main 2>/dev/null || echo "WARN: Push failed" >&2
fi
```

**Rules:**
- Use explicit file allowlists (cp specific files), never rsync the whole source.
- Exclude internal skill metadata (`.usage.json`, `.bundled_manifest`, `.curator_ledger.jsonl`).
- Always generate a MANIFEST.md showing what's included/excluded.
- Handle the "no changes" case gracefully — don't create empty commits.
- Use `set -euo pipefail` to fail fast on errors.

### 5. Schedule via Hermes Cron

Copy the script to `~/.hermes/scripts/backup.sh` (required for cron discovery):

```bash
cp ~/.backup-repo/backup.sh ~/.hermes/scripts/backup.sh
chmod +x ~/.hermes/scripts/backup.sh
```

Create the cron job with `cronjob_manage`:

```
tool_call(
  name="cronjob_manage",
  arguments={
    "action": "create",
    "name": "Config Backup",
    "script": "backup.sh",
    "schedule": "0 3 * * *",
    "no_agent": true,
    "deliver": "local",
    "workdir": "/Users/<user>/.backup-repo"
  }
)
```

**Why `no_agent: true`:** The backup is a deterministic script — no LLM reasoning needed.
Using no_agent avoids burning tokens on every run. The script's stdout is delivered
if non-empty; empty stdout sends nothing (watchdog pattern).

**Schedule:** `0 3 * * *` (3 AM daily) is a good default — off-peak, after typical
config changes, before the user needs the machine.

### 6. Verify First Run

Run the script manually before relying on the cron schedule:

```bash
bash ~/.backup-repo/backup.sh
```

Verify:
- No secrets in the git history (`git log --all -p | grep -i 'api_key\|token\|password'`).
- All expected files are present.
- The commit message is descriptive.

## Pitfalls

- **Don't rsync the whole source directory** — it will copy secrets, caches, and
gigantic runtime files. Use explicit allowlists.
- **Don't rely on .gitignore alone for secrets exclusion** — the script should
never copy them in the first place. .gitignore is a safety net.
- **Don't use `no_agent: false` for scheduled backups** — the backup is
deterministic and doesn't need LLM reasoning. Save tokens.
- **Don't put the backup repo inside the source directory** — recursive
copy loops and the backup itself gets backed up.
- **Don't skip the manifest** — future you needs to know what's included
without reverse-engineering the script.
- **Don't commit with empty changes** — `git diff --queued --quiet` check
prevents noise in the history.
- **Cron scripts must live in `~/.hermes/scripts/`** — the cron runner
resolves relative paths there, not from arbitrary locations.