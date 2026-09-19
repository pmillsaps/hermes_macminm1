#!/usr/bin/env bash
# hermes-backup.sh — Daily backup of Hermes config & skills to git
# Excludes all files containing secrets, tokens, passwords, or runtime state.

set -euo pipefail

BACKUP_REPO="$HOME/.hermes-backup-repo"
SRC="$HOME/.hermes"
DATE=$(date '+%Y-%m-%d %H:%M:%S')
HOST=$(scutil --get ComputerName 2>/dev/null || hostname)

# --- Ensure repo exists ---
if [ ! -d "$BACKUP_REPO/.git" ]; then
  echo "ERROR: Backup repo not found at $BACKUP_REPO" >&2
  exit 1
fi

cd "$BACKUP_REPO"

# --- Copy config files (safe ones only) ---
echo "Copying config files..."
cp "$SRC/config.yaml" config.yaml 2>/dev/null || true
cp "$SRC/profile.yaml" profile.yaml 2>/dev/null || true
cp "$SRC/channel_directory.json" channel_directory.json 2>/dev/null || true

# --- Copy skills directory (excluding internal metadata/state) ---
echo "Copying skills..."
rm -rf skills
mkdir -p skills
rsync -a \
  --exclude='.usage.json' \
  --exclude='.usage.json.lock' \
  --exclude='.bundled_manifest' \
  --exclude='.curator_ledger.jsonl' \
  --exclude='.curator_state' \
  --exclude='.locks/' \
  --exclude='index-cache/' \
  "$SRC/skills/" skills/

# --- Copy cron jobs ---
echo "Copying cron jobs..."
mkdir -p cron
cp "$SRC/cron/jobs.json" cron/jobs.json 2>/dev/null || true

# --- Copy custom scripts ---
echo "Copying custom scripts..."
mkdir -p scripts
cp "$SRC/scripts/"* scripts/ 2>/dev/null || true

# --- Copy hooks (if any) ---
if [ -d "$SRC/hooks" ] && [ "$(ls -A "$SRC/hooks")" ]; then
  echo "Copying hooks..."
  mkdir -p hooks
  rsync -a "$SRC/hooks/" hooks/
fi

# --- Copy platforms config (pairing, rate limits — safe) ---
if [ -d "$SRC/platforms" ]; then
  echo "Copying platforms..."
  mkdir -p platforms
  rsync -a "$SRC/platforms/" platforms/
fi

# --- Copy desktop config if present ---
if [ -d "$SRC/desktop" ] && [ -f "$SRC/desktop/interrupted_turns.json" ]; then
  echo "Copying desktop config..."
  mkdir -p desktop
  cp "$SRC/desktop/interrupted_turns.json" desktop/ 2>/dev/null || true
fi

# --- Generate manifest of what was backed up ---
echo "Generating manifest..."
cat > MANIFEST.md <<EOF
# Hermes Backup Manifest

**Generated:** $DATE
**Host:** $HOST
**Source:** \`$SRC\`

## Included

| Path | Description |
|------|-------------|
| \`config.yaml\` | Main Hermes configuration (models, display, compression, etc.) |
| \`profile.yaml\` | UI profile settings |
| \`channel_directory.json\` | Notification channel registry |
| \`skills/\` | All skill definitions (SKILL.md, references, templates, scripts) |
| \`cron/jobs.json\` | Scheduled cron job definitions |
| \`scripts/\` | Custom scripts (e.g., wiki-vault-ingest) |
| \`hooks/\` | Hook definitions (if any) |
| \`platforms/\` | Platform pairing & rate limit state |
| \`desktop/interrupted_turns.json\` | Interrupted turn recovery state |

## Excluded (secrets/runtime)

- \`auth.json\` — authentication tokens
- \`shared/nous_auth.json\` — OAuth credentials
- \`vault/\` — vault files
- \`state.db\`, \`kanban.db\`, \`projects.db\` — runtime databases
- \`sessions/\` — active session data
- \`logs/\` — log files
- \`cache/\` — model/tool caches
- \`models_dev_cache.json\` — large model catalog cache
- \`gateway_state.json\`, \`processes.json\` — runtime state
- \`spawn-ledger.json\` — spawn tracking
- \`hermes-agent/\` — bundled Hermes Agent source
- \`node_modules/\` — bundled dependencies
- \`bin/\` — runtime binaries
- \`backups/\`, \`sandboxes/\` — internal backup/sandbox dirs
EOF

# --- Git commit & push ---
echo "Committing..."
git add -A
if git diff --cached --quiet; then
  echo "No changes to backup."
else
  git commit -m "Backup: $DATE [$HOST]"
  git push origin main 2>/dev/null || echo "WARN: Push failed (network?)" >&2
fi

echo "Done. Backup committed."
