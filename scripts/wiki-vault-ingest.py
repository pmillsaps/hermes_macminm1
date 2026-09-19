"""
Vault ingest tracker — manages incremental ingestion of Obsidian vault files into the LLM Wiki.

State file: ~/.hermes/scripts/wiki-vault-ingest-state.json
{
  "ingested": {
    "relative/path/to/file.md": {
      "ingested": "2026-09-19",
      "sha256": "abc123...",
      "last_processed": "2026-09-19T05:30:00"
    }
  },
  "timing": {
    "batches": [
      {"timestamp": "2026-09-19T05:00:00", "file_count": 100, "duration_seconds": 803}
    ]
  }
}

Folders are processed in FOLDER_PRIORITY order (highest value first).
"""

import json, hashlib, os, re, sys, time
from pathlib import Path
from datetime import datetime

VAULT_ROOT = Path("/Users/paulmillsaps/Documents/_Obsidian")
STATE_FILE = Path.home() / ".hermes" / "scripts" / "wiki-vault-ingest-state.json"

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


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"ingested": {}, "timing": {"batches": []}}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def file_hash(filepath):
    """Compute SHA-256 of file content."""
    return hashlib.sha256(filepath.read_bytes()).hexdigest()


def vault_files_by_priority():
    """Yield (relative_path, absolute_path) in priority order, skipping excluded folders."""
    for folder_name in FOLDER_PRIORITY:
        folder = VAULT_ROOT / folder_name
        if not folder.is_dir():
            continue
        for md_file in sorted(folder.rglob("*.md")):
            rel = str(md_file.relative_to(VAULT_ROOT))
            yield rel, md_file


def next_batch(batch_size=100, skip_unchanged=True):
    """Get next batch of files that need processing.
    
    Returns files that are:
    - Never been ingested, OR
    - Have changed since last ingest (different sha256)
    """
    state = load_state()
    ingested = state.get("ingested", {})
    
    batch = []
    skipped_unchanged = 0
    skipped_excluded = 0
    
    for rel, filepath in vault_files_by_priority():
        if any(rel.startswith(f"{ex}/") or rel.startswith(f"{ex}") for ex in EXCLUDE):
            skipped_excluded += 1
            continue
        
        current_hash = file_hash(filepath)
        
        if rel in ingested:
            if skip_unchanged and ingested[rel].get("sha256") == current_hash:
                skipped_unchanged += 1
                continue
        
        batch.append((rel, filepath, current_hash))
        if len(batch) >= batch_size:
            break
    
    return batch, skipped_unchanged, skipped_excluded


def get_timing_summary(state=None):
    """Return human-readable timing summary from batch history."""
    if state is None:
        state = load_state()
    
    batches = state.get("timing", {}).get("batches", [])
    if not batches:
        return {"total_batches": 0, "total_files": 0, "avg_batch_seconds": 0}
    
    durations = [b["duration_seconds"] for b in batches if b.get("duration_seconds", 0) > 0]
    total = sum(durations) if durations else 0
    avg = total / len(durations) if durations else 0
    
    # Count remaining files
    batch, _, _ = next_batch(batch_size=99999, skip_unchanged=True)
    remaining_files = len(batch)
    remaining_batches = max((remaining_files + 99) // 100, 0)
    projected_seconds = remaining_batches * avg
    
    return {
        "total_batches": len(batches),
        "total_files_ingested": sum(b.get("file_count", 0) for b in batches),
        "total_duration_minutes": round(total / 60, 1),
        "avg_batch_seconds": round(avg, 1),
        "min_batch_seconds": round(min(durations), 1) if durations else 0,
        "max_batch_seconds": round(max(durations), 1) if durations else 0,
        "remaining_files": remaining_files,
        "remaining_batches": remaining_batches,
        "projected_remaining_minutes": round(projected_seconds / 60, 1),
        "projected_remaining_hours": round(projected_seconds / 3600, 2),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  wiki-vault-ingest.py batch [size]     - Get next batch of files to process")
        print("  wiki-vault-ingest.py record <duration_seconds> <file_count> [file:hash ...]  - Record batch")
        print("  wiki-vault-ingest.py summary          - Show timing/progress report")
        print("  wiki-vault-ingest.py status           - Show current ingest state counts")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "batch":
        size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        batch, skipped_unchanged, skipped_excluded = next_batch(size)
        
        if not batch:
            print("NO_FILES")
            sys.exit(0)
        
        print(f"BATCH:{len(batch)}")
        print(f"SKIPPED_UNCHANGED:{skipped_unchanged}")
        print(f"SKIPPED_EXCLUDED:{skipped_excluded}")
        for rel, filepath, file_hash in batch:
            print(f"FILE:{rel}|{file_hash}")
    
    elif cmd == "record":
        if len(sys.argv) < 4:
            print("Usage: wiki-vault-ingest.py record <duration_seconds> <file_count> [file:hash ...]")
            sys.exit(1)
        
        duration = float(sys.argv[2])
        file_count = int(sys.argv[3])
        file_hashes = {}
        
        # Parse file:hash pairs from remaining args if provided
        for arg in sys.argv[4:]:
            if '|' in arg:
                rel, fh = arg.split('|', 1)
                file_hashes[rel] = fh
        
        state = load_state()
        
        # Record batch timing
        if "timing" not in state:
            state["timing"] = {"batches": []}
        
        state["timing"]["batches"].append({
            "timestamp": datetime.now().isoformat(),
            "file_count": file_count,
            "duration_seconds": duration,
        })
        
        # Keep only last 100 batches to avoid unbounded growth
        if len(state["timing"]["batches"]) > 100:
            state["timing"]["batches"] = state["timing"]["batches"][-100:]
        
        # Update ingested hashes for this batch
        for rel, fh in file_hashes.items():
            if rel not in state["ingested"]:
                state["ingested"][rel] = {}
            state["ingested"][rel]["sha256"] = fh
            state["ingested"][rel]["last_processed"] = datetime.now().isoformat()
            if "ingested" not in state["ingested"][rel]:
                state["ingested"][rel]["ingested"] = datetime.now().strftime("%Y-%m-%d")
        
        save_state(state)
        
        # Print summary for delivery
        summary = get_timing_summary(state)
        print(json.dumps(summary, indent=2))
    
    elif cmd == "summary":
        summary = get_timing_summary()
        print(json.dumps(summary, indent=2))
    
    elif cmd == "status":
        state = load_state()
        ingested = state.get("ingested", {})
        batch, remaining, _ = next_batch(batch_size=99999)
        
        print(f"Files tracked: {len(ingested)}")
        print(f"Files remaining to process: {len(batch)}")
        print(f"Batch history: {len(state.get('timing', {}).get('batches', []))} batches")
        
        # Show last 5 ingested
        recent = sorted(
            ingested.items(),
            key=lambda x: x[1].get("last_processed", ""),
            reverse=True
        )[:5]
        if recent:
            print("\nRecently processed:")
            for rel, info in recent:
                print(f"  {rel[:60]}... ({info.get('ingested', '?')})")
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
