---
name: obsidian-duplicate-finder
description: "Use when scanning Obsidian vault for duplicate files."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Obsidian, duplicate, markdown, vault, maintenance]
---

# Obsidian Duplicate File Finder

Scans the Obsidian vault for markdown files that are 90%+ identical in content,
regardless of where they live in the folder tree. Writes the results to
`0-ToDo/Duplicate File Checks.md` with wikilinks grouped by similarity.

## When to use

- User asks to find duplicates in their Obsidian vault
- Scheduled daily maintenance (cron) to keep the duplicate list fresh
- After large imports or reorganizations

## Workflow

1. **Pull the latest from git first**:
```bash
cd /Users/paulmillsaps/Documents/_Obsidian && git pull origin main
```
2. Walk the vault (`~/Documents/_Obsidian/` or `$OBSIDIAN_VAULT_PATH`) for all `.md` files.
3. Group by base name, stripping common suffixes: ` 1`, ` 2`, ` - Copy`.
4. For groups with 2+ files, compare content using MD5 first, then `difflib.SequenceMatcher`.
5. Record groups where the best pair has ≥90% similarity.
6. Write results to `0-ToDo/Duplicate File Checks.md` (in the vault root).
   - Header: `# Duplicate File Checks`
   - Each group separated by `---`
   - HTML comment `<!-- Similarity: XX.XX% -->` above each group
   - Each file as a `[[wikilink]]` with path (no `.md`) for disambiguation
   - Blank line between entries within a group
7. Commit and push the results:
```bash
cd /Users/paulmillsaps/Documents/_Obsidian && git add -A && git commit -m "Duplicate file check: N duplicate groups found" && git push origin main
```

## Key implementation notes

- **Hash-then-diff**: MD5 compare first (fast path for exact matches), then SequenceMatcher.
- **Path-based wikilinks**: `[[Folder/Subfolder/Note Name]]` — includes path so Obsidian can disambiguate same-named files.
- **Performance**: ~4,500 files takes ~8s for grouping + ~20s for pairwise content comparison on a modern Mac.

## Output format example

```markdown
# Duplicate File Checks

Found **289** groups of files that are 90%+ identical.

---

<!-- Similarity: 100.00% -->
[[1-Inbox/Obsidian/Give OpenCode the Ability to Read Your Documents]]
[[1-Inbox/Obsidian/Give OpenCode the Ability to Read Your Documents 1]]

---

<!-- Similarity: 99.76% -->
[[1-Inbox/Design/How To Get Monetized on YouTube (I made $627 in my first 50 days)]]
[[Money Making/How To Get Monetized on YouTube (I made $627 in my first 50 days)]]

---
```

## Vault path

Resolves in this order:
1. `$OBSIDIAN_VAULT_PATH` environment variable
2. `~/Documents/_Obsidian/` (default for this user)
3. Ask the user if neither exists