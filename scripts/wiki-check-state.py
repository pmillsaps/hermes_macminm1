#!/usr/bin/env python3
"""Check wiki state for ingest script debugging."""
import pathlib, json, hashlib, re, sys, os, time
from pathlib import Path
from collections import defaultdict

WIKI_ROOT = pathlib.Path('/Users/paulmillsaps/Documents/_Obsidian/wiki')
VAULT_ROOT = pathlib.Path('/Users/paulmillsaps/Documents/_Obsidian')
STATE_FILE = pathlib.Path('/Users/paulmillsaps/.hermes/scripts/wiki-vault-ingest-state.json')

def main():
    # Check wiki structure
    for subdir in ['entities', 'concepts', 'comparisons', 'queries']:
        d = WIKI_ROOT / subdir
        if d.is_dir():
            files = list(d.glob('*.md'))
            print(f'{subdir}: {len(files)} files')
        else:
            print(f'{subdir}: not found')

    # Check state file
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)
        print(f'State file: {len(state)} entries')
        # Show last 5
        for k, v in list(state.items())[-5:]:
            print(f'  {k}: {v}')
    else:
        print('State file: not found')

if __name__ == '__main__':
    main()
