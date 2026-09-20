"""One-time repair for wiki-vault-ingest-state.json hash format drift.

Problem: state file stores Python int hashes (written by an older tracker
version); the current wiki-vault-ingest.py computes hex sha256 digests.
Every tracked file therefore looks 'changed' and `batch` never returns
NO_FILES (2157 tracked, 2159 perpetually 'remaining').

This script reconciles:
  - NEW: vault files never tracked -> genuinely new, need ingestion
  - CHANGED: tracked files whose content differs AND mtime is newer than
    last_processed (or hash format was already hex) -> need re-ingestion
  - REPAIRED: tracked files with stale int hashes whose mtime is NOT newer
    than last_processed -> content already ingested, fix hash format only

Dry-run by default. Pass 'apply' to write the repaired state (backs up the
original first).
"""
import importlib.util
import shutil
import sys
from datetime import datetime
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "wiki-vault-ingest.py"
spec = importlib.util.spec_from_file_location("wvi", str(SCRIPT))
wvi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wvi)

RAW_ARTICLES = Path("/Users/paulmillsaps/Documents/_Obsidian/wiki/raw/articles")

state = wvi.load_state()
ingested = state.get("ingested", {})

new_files = []        # (rel, digest) never tracked
changed_files = []    # (rel, digest, reason) need real processing
repaired_rels = []    # stale int hashes, content unchanged since last_processed

for rel, fp in wvi.vault_files_by_priority():
    digest = wvi.file_hash(fp)
    entry = ingested.get(rel)
    if entry is None:
        new_files.append((rel, digest))
        continue
    stored = entry.get("sha256")
    if stored == digest:
        continue  # healthy entry
    lp = str(entry.get("last_processed") or "")
    try:
        mtime = datetime.fromtimestamp(fp.stat().st_mtime).isoformat(timespec="microseconds")
    except OSError:
        mtime = ""
    if isinstance(stored, int) and lp and mtime and mtime <= lp:
        # Stale format, file untouched since it was last processed.
        entry["sha256"] = digest
        repaired_rels.append(rel)
    else:
        reason = f"stored={'int' if isinstance(stored, int) else 'hex'} lp={lp} mtime={mtime}"
        changed_files.append((rel, digest, reason))

missing_on_disk = [rel for rel in ingested if not (wvi.VAULT_ROOT / rel).exists()]

print(f"TRACKED:{len(ingested)}")
print(f"NEW:{len(new_files)}")
for rel, digest in new_files:
    print(f"NEWFILE|{rel}|{digest}")
print(f"CHANGED:{len(changed_files)}")
for rel, digest, reason in changed_files:
    print(f"CHANGEDFILE|{rel}|{digest}|{reason}")
print(f"REPAIRED:{len(repaired_rels)}")
print(f"MISSING_ON_DISK:{len(missing_on_disk)}")

# Spot-check: do raw/ copies exist for a sample of repaired files?
sample = repaired_rels[:5] + new_files[:5]
for rel in sample:
    print(f"RAWCOPY|{rel}|{(RAW_ARTICLES / rel).exists()}")

if len(sys.argv) > 1 and sys.argv[1] == "apply":
    backup = SCRIPT.parent / "wiki-vault-ingest-state.json.bak-20260920"
    if not backup.exists():
        shutil.copy2(SCRIPT.parent / "wiki-vault-ingest-state.json", backup)
        print(f"BACKUP:{backup}")
    wvi.save_state(state)
    print("STATE_SAVED")
else:
    print("DRY_RUN_ONLY")
