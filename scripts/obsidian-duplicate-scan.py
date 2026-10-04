#!/usr/bin/env python3
"""Scan Obsidian vault for duplicate files, auto-delete 100% identical copies,
and write remaining results to 0-ToDo/Duplicate File Checks.md"""

import hashlib, difflib, os, re, shutil
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
    name = re.sub(r'\s+Copy$', '', name, flags=re.IGNORECASE)
    return name

groups = {}
for f in all_files:
    key = base_name(f).lower()
    groups.setdefault(key, []).append(f)

print(f"Found {len(groups)} unique base names")

# Compare pairs
matches = []
deleted = 0
deletion_log = []

for key, files in groups.items():
    if len(files) < 2:
        continue
    
    hashes = {}
    for f in files:
        try:
            hashes[f] = hashlib.md5(f.read_bytes()).hexdigest()
        except OSError:
            continue
    
    # Find exact matches
    seen_hashes = {}
    for f, h in hashes.items():
        if h in seen_hashes:
            # Exact match found — 100% duplicate
            sim = 100.0
            original = seen_hashes[h]
            copy = f
            
            # Determine which to delete: the one with " 1", " 2" suffix
            # The "original" is the one WITHOUT a numbered suffix
            copy_stem = copy.stem
            has_number_suffix = bool(re.search(r'\s+\d+$', copy_stem))
            original_has_number_suffix = bool(re.search(r'\s+\d+$', original.stem))
            
            if has_number_suffix and not original_has_number_suffix:
                # Delete the suffixed copy
                deleted_file = copy
                kept_file = original
            elif original_has_number_suffix and not has_number_suffix:
                # The "original" in our dict is the suffixed one
                deleted_file = original
                kept_file = copy
            elif has_number_suffix and original_has_number_suffix:
                # Both have suffixes — keep the lower number (e.g., " 1" over " 2")
                num_copy = int(re.search(r'\s+(\d+)$', copy_stem).group(1))
                num_original = int(re.search(r'\s+(\d+)$', original.stem).group(1))
                if num_copy < num_original:
                    deleted_file = copy
                    kept_file = original
                else:
                    deleted_file = original
                    kept_file = copy
            else:
                # Neither has a number suffix — keep the first alphabetically
                if str(copy) < str(original):
                    deleted_file = copy
                    kept_file = original
                else:
                    deleted_file = original
                    kept_file = copy
            
            try:
                deleted_file.unlink()
                deleted += 1
                deletion_log.append(str(deleted_file.relative_to(VAULT_ROOT)))
                # Keep the original in matches for reporting
                matches.append(([kept_file], 100.0))
            except OSError as e:
                print(f"  Could not delete {copy}: {e}")
                # Still report it as a match
                matches.append(([original, copy], sim))
            continue
        seen_hashes[h] = f
    
    # SequenceMatcher for non-exact pairs
    for i in range(len(files)):
        for j in range(i+1, len(files)):
            if files[i] not in hashes or files[j] not in hashes:
                continue
            if hashes[files[i]] == hashes[files[j]]:
                continue  # already handled above
            try:
                content_i = files[i].read_text()
                content_j = files[j].read_text()
                sim = difflib.SequenceMatcher(None, content_i, content_j).ratio() * 100
                if sim >= 90:
                    matches.append(([files[i], files[j]], sim))
            except:
                continue

print(f"Deleted {deleted} 100%-identical copies")
print(f"Remaining duplicate groups (90%+): {len(matches)} groups, {len([m for m in matches if len(m[0]) > 1])} multi-file")

# Write output
lines = ["# Duplicate File Checks"]
lines.append(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
lines.append("")
lines.append(f"## Auto-Deleted (100% identical copies)")
lines.append(f"**{deleted}** copies were deleted (name ended with ` 1`, ` 2`, etc.):")
lines.append("")
for dl in deletion_log:
    rel = Path(dl).as_posix().replace('.md', '')
    lines.append(f"~~[[{rel}]]~~ ✅deleted")
lines.append("")
lines.append("---")
lines.append("")

# Filter out single-file groups (deleted copies now have no pair)
remaining = [(fl, s) for fl, s in matches if len(fl) > 1]
remaining.sort(key=lambda x: x[1], reverse=True)

lines.append(f"## Remaining Duplicates (90%+ similarity)")
lines.append(f"Found **{len(remaining)}** groups of files that are 90%+ identical.")
lines.append("")
lines.append("---")
lines.append("")

for file_list, sim in remaining:
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
