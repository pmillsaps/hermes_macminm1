---
name: obsidian-duplicate-finder
description: "Use when scanning Obsidian vault for duplicate files."
version: 1.2.0
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
6. **Auto-delete for 100% matches**: When files are exactly identical (MD5 match), automatically delete the "copy" file — defined as the file whose name ends with ` 1`, ` 2`, etc. (space followed by number). The "original" is the file without the numbered suffix. If both have numbered suffixes or neither does, keep the lower-numbered or alphabetically-first file. Log each deletion to the report.
7. Write results to `0-ToDo/Duplicate File Checks.md` (in the vault root).
   - Header: `# Duplicate File Checks`
   - Sub-sections: `## Auto-Deleted (100% identical copies)` then `## Remaining Duplicates (90%+ similarity)`
   - Each group separated by `---`
   - HTML comment `<!-- Similarity: XX.XX% -->` above each group
   - Each file as a `[[wikilink]]` with full relative path (no `.md`) for disambiguation
   - Deleted copies shown as `~~[[wikilink]]~~ ✅deleted` in the auto-deleted section
   - Consistent formatting: all links use `[[path/to/filename]]` — full vault-relative path, no `.md`
8. Commit and push the results and deletions:
```bash
cd /Users/paulmillsaps/Documents/_Obsidian && git add -A -- '.obsidian' '.github' '0-ToDo/Duplicate File Checks.md' && git add -A -- '1-Inbox/' '2-Clippings/' 'AI/' 'Agents/' 'Business Ideas/' 'Hermes/' 'Hardware/' 'LLM Comparisons/' 'Money Making/' 'Personal Finance/' 'Programming/' 'Prompts/' 'Research/' 'Social Media/' 'Stock Analysis/' 'Tools/' 'Trading/' 'Video/' 'Writing/' 'PKM/' 'N8N/' 'MCP/' 'RAG/' 'Ollama/' 'DeepSeek/' 'Llama/' 'Kimi/' 'Qwen/' 'Obsidian/' 'SAAS/' 'Software/' 'Skills/' 'Side Hustles/' '0-ToDo/' && git commit -m "Duplicate file check: N groups, M auto-deleted" && git push origin main
```
**Pitfall:** `git add -A` fails on files with special characters in names (Resource deadlock). Stage paths in batches — exclude `.obsidian` with `-- ':.obsidian'` if only the duplicate check needs committing. The `.obsidian` plugin files are untracked noise; they cause lock contention during git operations.

## Key implementation notes

- **Hash-then-diff**: MD5 compare first (fast path for exact matches), then SequenceMatcher.
- **100% match auto-delete**: When MD5 matches exactly, delete the file with the numbered suffix (` 1`, ` 2`, etc.). The unsuffixed file is the original. If both have numbered suffixes, keep the lower number. If neither has a suffix, keep alphabetically first. Log each deletion.
- **Consistent link format**: All entries use `[[path/to/filename]]` — full vault-relative path, no `.md`. This ensures uniform font size in Obsidian (all links render as single-line wikilinks) while preserving location context for processing.
- **Performance**: ~4,500 files takes ~8s for grouping + ~20s for pairwise content comparison on a modern Mac.
- **Script pitfall**: The scan script at `~/.hermes/scripts/obsidian-duplicate-scan.py` may crash on the `deletion_log` output loop if `deletion_log` stores relative paths but line 136 re-calls `.relative_to(VAULT_ROOT)` on them. Fix: use `Path(dl).as_posix().replace('.md', '')` instead of `Path(dl).relative_to(VAULT_ROOT).as_posix().replace('.md', '')`. Also, `git add -A` can fail with "Resource deadlock" on files with spaces/special chars — stage deletions with `git add -u '1-Inbox/'` and the output file separately before committing.

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
[[1-Inbox/Design/How To Get Monetized on YouTube]]
[[Money Making/How To Get Monetized on YouTube]]

---
```

## Vault path

Resolves in this order:
1. `$OBSIDIAN_VAULT_PATH` environment variable
2. `~/Documents/_Obsidian/` (default for this user)
3. Ask the user if neither exists