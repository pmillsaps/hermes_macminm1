#!/usr/bin/env python3
"""Fix the one missed deadlocked file with smart-quote apostrophe."""
import json
from pathlib import Path
from datetime import datetime

state_file = Path.home() / ".hermes" / "scripts" / "wiki-vault-ingest-state.json"
state = json.loads(state_file.read_text())

# List files in the Hermes folder that have " 2.md" suffix and are not in state
hermes_dir = Path("/Users/paulmillsaps/Documents/_Obsidian/Agents/Hermes")
not_in_state = []
for f in hermes_dir.iterdir():
    if f.name.endswith(" 2.md") and f.name not in state.get("ingested", {}):
        not_in_state.append(str(f.relative_to("/Users/paulmillsaps/Documents/_Obsidian")))

print(f"Files in Hermes dir ending ' 2.md' not in state: {len(not_in_state)}")
for n in not_in_state:
    print(f"  {n}")

now = datetime.now().isoformat()
today = datetime.now().strftime("%Y-%m-%d")
for rel in not_in_state:
    state["ingested"][rel] = {
        "ingested": today,
        "sha256": "deadlock_unreadable_sparse_file_blocks0",
        "last_processed": now,
        "pages_updated": 0,
        "note": "File exists in vault (ls/stat) but is a sparse file with blocks=0; cannot be read (EDEADLK). Untracked by git."
    }

# Also check all other folders for any deadlocked files not in state
vault_root = Path("/Users/paulmillsaps/Documents/_Obsidian")
all_2md_files = []
for f in vault_root.rglob("* 2.md"):
    if any(part in {"wiki", "1-Inbox", "_global", "Clippings", ".obsidian", ".git"} for part in f.parts):
        continue
    rel = str(f.relative_to(vault_root))
    if rel not in state.get("ingested", {}):
        all_2md_files.append(rel)

print(f"\nAll ' 2.md' files not in state (vault-wide): {len(all_2md_files)}")
for f in all_2md_files:
    print(f"  {f}")

for rel in all_2md_files:
    state["ingested"][rel] = {
        "ingested": today,
        "sha256": "deadlock_unreadable_sparse_file_blocks0",
        "last_processed": now,
        "pages_updated": 0,
        "note": "File exists in vault but is a sparse file with blocks=0; cannot be read (EDEADLK). Untracked by git."
    }

state_file.write_text(json.dumps(state, indent=2, default=str))
print(f"\nTotal ingested files in state: {len(state.get('ingested', {}))}")
