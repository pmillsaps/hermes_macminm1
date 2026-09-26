#!/usr/bin/env python3
"""
Mechanical vault re-ingest: reads each vault file, finds which existing wiki
pages are mentioned, bumps their `updated` date and adds the source to their
`sources` frontmatter. No LLM reasoning per file — pure text matching.

Reports realistic wall-clock timing.
"""

import json, os, re, sys, time
from pathlib import Path
from datetime import datetime

VAULT_ROOT = Path("/Users/paulmillsaps/Documents/_Obsidian")
WIKI_ROOT = Path("/Users/paulmillsaps/Documents/_Obsidian/wiki")
STATE_FILE = Path.home() / ".hermes" / "scripts" / "wiki-vault-ingest-state.json"
LOG_FILE = WIKI_ROOT / "log.md"
INDEX_FILE = WIKI_ROOT / "index.md"

FOLDER_PRIORITY = [
    "AI", "Programming", "Agents", "Prompts", "Tools", "Hardware",
    "Hermes", "DeepSeek", "Llama", "Kimi", "Qwen", "Ollama",
    "LLM Comparisons", "Money Making", "Productivity", "AI News",
    "N8N", "MCP", "RAG", "Coursiv", "Local AI Setup", "Automation",
    "Trading", "Stock Analysis", "Personal Finance", "Video",
    "Business Ideas", "Writing", "Education", "Design", "Work",
    "OpenClaw", "Voice Scribe", "OCR", "Social Media", "AI Apps",
    "0-ToDo", "Todo", "Research", "Software", "SAAS", "Photography",
    "PKM", "Obsidian", "Models", "Financial", "Deepseek Harness",
    "Hermes Skill Prompts", "Skills", "Side Hustles"
]

EXCLUDE = {"wiki", "1-Inbox", "_global", "Clippings", ".obsidian", ".git"}

# Slugs to skip because they match too broadly as substrings
SKIP_SLUGS = {
    "ai", "api", "ml", "nlp", "rag", "llm", "gpt", "gpu", "cpu",
    "ram", "ssd", "usb", "url", "html", "css", "js", "py",
    "go", "rs", "ts", "sql", "xml", "json", "yaml", "csv",
    "pdf", "png", "jpg", "mp4", "gif", "zip", "git",
    "mac", "ios", "app", "web", "bot", "cli", "sdk", "ide",
    "aws", "gcp", "vpn", "dns", "http", "ssh", "ftp",
    "os", "ui", "ux", "qa", "pm", "hr", "pr", "ir",
    "fed", "sec", "irs", "nsa", "fbi", "cia", "usa", "eu",
    "uk", "eu", "un", "nato", "oecd", "imf", "wto",
    "ceo", "cto", "cfo", "coo", "vp", "svp", "dir", "mgr",
    "jr", "sr", "dr", "mr", "mrs", "ms", "prof", "dept", "est",
    "inc", "llc", "corp", "ltd", "plc", "gmbh", "sa", "as",
    "at", "by", "to", "up", "in", "on", "is", "it", "be",
    "do", "go", "no", "so", "we", "me", "my", "us", "vs",
    "am", "pm", "et", "pt", "ct", "mt", "ak", "hi", "nh",
    "mt", "id", "sd", "nd", "ne", "ia", "ks", "ok", "tx",
    "la", "ar", "ms", "al", "ga", "fl", "sc", "nc", "va",
    "wv", "oh", "mi", "in", "il", "wi", "mn", "or", "wa",
    "ca", "nv", "az", "ut", "co", "wy", "mt", "nm", "ak",
}

def load_state():
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        if "timing" not in state:
            state["timing"] = {"batches": []}
        return state
    return {"ingested": {}, "timing": {"batches": []}}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))

def get_all_wiki_pages():
    """Return dict of slug -> (filepath, full_content) — read in batches to avoid deadlock"""
    pages = {}
    for subdir in ["entities", "concepts", "comparisons", "queries"]:
        d = WIKI_ROOT / subdir
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            try:
                content = f.read_text()
            except OSError:
                # On deadlock, skip this file and try the rest
                continue
            pages[f.stem] = (f, content)
    return pages

def slugify(text):
    """Convert text to wiki slug format."""
    s = text.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s

def find_matching_pages(titles, wiki_pages, content_lower):
    """Find which wiki pages are genuinely mentioned in content."""
    matches = set()
    
    for title in titles:
        slug = slugify(title)
        if len(slug) < 3:
            continue
        if slug in SKIP_SLUGS:
            continue
        if slug in wiki_pages:
            # Verify it's a genuine match by checking word boundaries
            phrase = slug.replace('-', ' ')
            pattern = r'(?<![a-z])' + re.escape(phrase) + r'(?![a-z])'
            if re.search(pattern, content_lower):
                matches.add(slug)
    
    return matches

def update_page_source_refs(page_path, vault_rel_path, content):
    """Add source reference to page frontmatter if not present. Returns True if modified."""
    source_entry = f"raw/articles/{vault_rel_path}"
    
    if source_entry in content:
        return False  # already present
    
    lines = content.split('\n')
    in_frontmatter = False
    sources_line_idx = None
    second_dash = 0
    
    for i, line in enumerate(lines):
        if line.strip() == '---':
            second_dash += 1
            if second_dash == 2:
                in_frontmatter = False
                break
            in_frontmatter = True
            continue
        if in_frontmatter and line.strip().startswith('sources:'):
            sources_line_idx = i
    
    modified = False
    
    if sources_line_idx is not None:
        line = lines[sources_line_idx]
        if '[]' in line:
            lines[sources_line_idx] = line.replace('[]', f'["{source_entry}"]')
            modified = True
        elif line.strip() == 'sources:':
            lines.insert(sources_line_idx + 1, f'  - "{source_entry}"')
            modified = True
        else:
            for j in range(sources_line_idx + 1, len(lines)):
                if ']' in lines[j]:
                    lines[j] = lines[j].replace(']', f', "{source_entry}"]')
                    modified = True
                    break
    
    if not modified:
        for i, line in enumerate(lines):
            if line.strip().startswith('tags:'):
                lines.insert(i + 1, f'sources: ["{source_entry}"]')
                modified = True
                break
    
    now = datetime.now().strftime("%Y-%m-%d")
    for i, line in enumerate(lines):
        if line.strip().startswith('updated:'):
            lines[i] = f"updated: {now}"
            modified = True
            break
    
    if modified:
        new_content = '\n'.join(lines)
        page_path.write_text(new_content)
        return True
    return False

def get_vault_files():
    """Yield (rel_path, abs_path) in priority order."""
    for folder_name in FOLDER_PRIORITY:
        folder = VAULT_ROOT / folder_name
        if not folder.is_dir():
            continue
        for md_file in sorted(folder.rglob("*.md")):
            rel = str(md_file.relative_to(VAULT_ROOT))
            if any(rel.startswith(f"{ex}/") or rel.startswith(f"{ex}") for ex in EXCLUDE):
                continue
            yield rel, md_file

def main():
    state = load_state()
    wiki_pages = get_all_wiki_pages()
    print(f"Loaded {len(wiki_pages)} wiki pages")
    
    total_files = 0
    total_pages_updated = 0
    skipped = 0
    errors = 0
    start_time = time.time()
    
    batch_size = 100
    batch_files = []
    
    for rel, filepath in get_vault_files():
        if rel in state.get("ingested", {}):
            skipped += 1
            continue
        
        batch_files.append((rel, filepath))
        
        if len(batch_files) >= batch_size:
            batch_start_time = time.time()
            batch_pages = process_batch(batch_files, wiki_pages, state)
            batch_duration = time.time() - batch_start_time
            
            total_files += len(batch_files)
            total_pages_updated += batch_pages
            
            save_state(state)
            
            elapsed = time.time() - start_time
            remaining = 2157 - total_files
            rate = total_files / elapsed * 60 if elapsed > 0 else 0
            eta_min = remaining / (total_files / elapsed) / 60 if total_files > 0 and elapsed > 0 else 0
            print(f"Batch: {len(batch_files)} files in {batch_duration:.1f}s, {batch_pages} pages updated | Total: {total_files} files, {elapsed:.0f}s elapsed, ~{eta_min:.0f}min remaining")
            batch_files = []
    
    if batch_files:
        batch_pages = process_batch(batch_files, wiki_pages, state)
        total_files += len(batch_files)
        total_pages_updated += batch_pages
        save_state(state)
    
    total_duration = time.time() - start_time
    print(f"\n=== COMPLETE ===")
    print(f"Total files processed: {total_files}")
    print(f"Pages updated: {total_pages_updated}")
    print(f"Total duration: {total_duration:.1f}s ({total_duration/60:.1f} min)")
    if total_duration > 0:
        print(f"Rate: {total_files/total_duration*60:.1f} files/min")

def batch_files_processed(batch):
    return len(batch)

def process_batch(batch, wiki_pages, state):
    """Process a batch of vault files, updating wiki pages."""
    pages_updated = 0
    for rel, filepath in batch:
        try:
            content = filepath.read_text()
            content_lower = content.lower()
            
            titles = set()
            for m in re.finditer(r'^#{1,3}\s+(.+)$', content, re.MULTILINE):
                titles.add(m.group(1).strip())
            for m in re.finditer(r'\[\[([^\]]+)\]\]', content):
                titles.add(m.group(1).strip())
            for m in re.finditer(r'\*\*([^*]+)\*\*', content):
                titles.add(m.group(1).strip())
            
            matching = find_matching_pages(titles, wiki_pages, content_lower)
            
            batch_updated = 0
            for slug in matching:
                page_path, page_content = wiki_pages[slug]
                if update_page_source_refs(page_path, rel, page_content):
                    batch_updated += 1
                    wiki_pages[slug] = (page_path, page_path.read_text())
            
            pages_updated += batch_updated
            
            state["ingested"][rel] = {
                "ingested": datetime.now().strftime("%Y-%m-%d"),
                "sha256": hash(content),
                "last_processed": datetime.now().isoformat(),
                "pages_updated": len(matching)
            }
        except Exception as e:
            print(f"  Error processing {rel}: {e}")
    
    return pages_updated

if __name__ == "__main__":
    main()
