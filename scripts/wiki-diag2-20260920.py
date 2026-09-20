"""Diagnose #2: (a) reverse-engineer old int hash format, (b) check git pull
evidence, (c) inspect raw/ structure, (d) find missing tracked file.
Keeps output SMALL — summaries only.
"""
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "wiki-vault-ingest.py"
spec = importlib.util.spec_from_file_location("wvi", str(SCRIPT))
wvi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wvi)

state = wvi.load_state()
ingested = state.get("ingested", {})

# ---------- (a) hash reverse-engineering ----------
def candidates(data: bytes):
    d = hashlib.sha256(data).digest()
    out = {}
    out["sha256_b8_big_signed"] = int.from_bytes(d[:8], "big", signed=True)
    out["sha256_b8_little_signed"] = int.from_bytes(d[:8], "little", signed=True)
    out["sha256_l8_big_signed"] = int.from_bytes(d[-8:], "big", signed=True)
    out["sha256_l8_little_signed"] = int.from_bytes(d[-8:], "little", signed=True)
    out["sha256_b8_big_unsigned"] = int.from_bytes(d[:8], "big", signed=False)
    m = hashlib.md5(data).digest()
    out["md5_b8_big_signed"] = int.from_bytes(m[:8], "big", signed=True)
    b = hashlib.blake2b(data).digest()
    out["blake2b_b8_big_signed"] = int.from_bytes(b[:8], "big", signed=True)
    return out

tested = matched = 0
match_names = set()
for rel, entry in list(ingested.items()):
    stored = entry.get("sha256")
    if not isinstance(stored, int):
        continue
    fp = wvi.VAULT_ROOT / rel
    if not fp.exists():
        continue
    tested += 1
    if tested > 300:
        break
    cands = candidates(fp.read_bytes())
    for name, val in cands.items():
        if val == stored:
            matched += 1
            match_names.add(name)
            break

print(f"HASH_TEST: tested={tested} matched={matched} functions={sorted(match_names)}")

# ---------- (b) git evidence ----------
VAULT = wvi.VAULT_ROOT
def git(*args):
    r = subprocess.run(["git", *args], cwd=VAULT, capture_output=True, text=True)
    return r.stdout.strip()

print("GIT_LOG_3:", git("log", "-3", "--format=%h %ci %s").replace("\n", " || "))
print("GIT_REFLOG_5:", git("reflog", "-5", "--format=%h %gs").replace("\n", " || "))

# Which vault .md files changed in the last 2 commits (upstream sync window)?
changed = git("diff", "HEAD~2", "HEAD", "--name-only", "--", "*.md")
changed_set = set(l for l in changed.splitlines() if l.strip())
print(f"GIT_CHANGED_MD_LAST2COMMITS: {len(changed_set)}")
sample = sorted(changed_set)[:5]
for s in sample:
    print("  ", s)

# Cross-check: how many of the 1242 'mtime-reset' files were in that git change set?
reset_files = []
for rel, entry in ingested.items():
    stored = entry.get("sha256")
    if not isinstance(stored, int):
        continue
    fp = VAULT / rel
    if not fp.exists():
        continue
    lp = str(entry.get("last_processed") or "")
    try:
        from datetime import datetime
        mtime = datetime.fromtimestamp(fp.stat().st_mtime).isoformat(timespec="microseconds")
    except OSError:
        continue
    if mtime > "2026-09-20T00:00" and lp and mtime > lp:
        reset_files.append(rel)
in_git = sum(1 for r in reset_files if r in changed_set)
print(f"MTIME_RESET_FILES: {len(reset_files)} OF_WHICH_IN_GIT_DIFF: {in_git}")

# ---------- (c) raw/ structure ----------
raw = Path("/Users/paulmillsaps/Documents/_Obsidian/wiki/raw")
if raw.exists():
    subdirs = [p.name for p in raw.iterdir() if p.is_dir()]
    print("RAW_SUBDIRS:", subdirs)
    for sd in ["articles", "papers", "transcripts"]:
        p = raw / sd
        if p.is_dir():
            n = sum(1 for _ in p.rglob("*.md"))
            print(f"RAW_{sd.upper()}_MD_COUNT: {n}")
            if n:
                first = next(p.rglob("*.md"), None)
                print(f"RAW_{sd.upper()}_EXAMPLE: {first.relative_to(raw) if first else None}")
else:
    print("RAW_DIR_MISSING")

# ---------- (d) missing tracked file ----------
missing = [rel for rel in ingested if not (VAULT / rel).exists()]
print("MISSING_TRACKED:", missing)

# ---------- (e) scripts dir inventory ----------
sd = Path.home() / ".hermes" / "scripts"
others = sorted(p.name for p in sd.glob("*.py")) + sorted(p.name for p in sd.glob("*.bak*"))
print("SCRIPTS_DIR:", others)
