#!/usr/bin/env python3
"""Scan Obsidian vault for duplicate files and write results to 0-ToDo/Duplicate File Checks.md"""

import hashlib, difflib, os, re
from pathlib import Path
from datetime import datetime

VAULT_ROOT = Path("/Users/paulmillsaps/Documents/_Obsidian")
EXCLUDE = {".obsidian", ".git", "_archive", "_meta", "wiki"}
OUTPUT_FILE = VAULT_ROOT / "0-ToDo" / "Duplicate File Checks.md"

# Collect all .md files
all_files = []
for root, dirs, files in os.walk(VAULT_ROOT):
    dirs[:] = [d for d in dirs if d not in EXCLUDE and not d.startswith('.')]
    for f in sorted(files):
        if f.endswith('.md'):
            all_files.append(Path(root) / f)

print(f"Found {len(all_files)} markdown files")

# Group by base name
def base_name(path):
    name = path.stem
    name = re.sub(r'\s+\d+$', '', name)
    name = re.sub(r'\s+-\s+Copy$', '', name, flags=re.IGNORECASE)
    return name

groups = {}
for f in all_files:
    key = base_name(f).lower()
    groups.setdefault(key, []).append(f)

print(f"Found {len(groups)} unique base names")

# Compare pairs
matches = []
for key, files in groups.items():
    if len(files) < 2:
        continue
    
    hashes = {}
    for f in files:
        try:
            hashes[f] = hashlib.md5(f.read_bytes()).hexdigest()
        except OSError:
            continue
    
    # Find exact matches first
    seen_hashes = {}
    for f, h in hashes.items():
        if h in seen_hashes:
            # Exact match found
            sim = 100.0
            matches.append(([seen_hashes[h], f], sim))
            continue
        seen_hashes[h] = f
    
    # SequenceMatcher for non-exact pairs
    for i in range(len(files)):
        for j in range(i+1, len(files)):
            if files[i] not in hashes or files[j] not in hashes:
                continue
            if hashes[files[i]] == hashes[files[j]]:
                continue
            try:
                content_i = files[i].read_text()
                content_j = files[j].read_text()
                sim = difflib.SequenceMatcher(None, content_i, content_j).ratio() * 100
                if sim >= 90:
                    matches.append(([files[i], files[j]], sim))
            except:
                continue

print(f"Found {len(matches)} groups with 90%+ similarity")

# Write output
lines = ["# Duplicate File Checks"]
lines.append(f"Found **{len(matches)}** groups of files that are 90%+ identical.")
lines.append(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
lines.append("---")
lines.append("")

# Sort by similarity descending
matches.sort(key=lambda x: x[1], reverse=True)

for file_list, sim in matches:
    lines.append(f"<!-- Similarity: {sim:.2f}% -->")
    for f in sorted(file_list, key=lambda x: str(x)):
        rel = f.relative_to(VAULT_ROOT)
        wiki_path = str(rel).replace('.md', '')
        lines.append(f"[[{wiki_path}]]")
    lines.append("---")
    lines.append("")

content = '\n'.join(lines)
OUTPUT_FILE.write_text(content)
print(f"Wrote {len(content)} chars to {OUTPUT_FILE}")
