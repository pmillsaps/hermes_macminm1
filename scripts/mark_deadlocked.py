#!/usr/bin/env python3
"""Mark deadlocked/sparse files as ingested in the state file."""
import json
from pathlib import Path
from datetime import datetime

# The 39 deadlocked files from the script output
deadlocked = [
    "Programming/Development/SDD/SDD, Kent Beck, and Martin Fowler Why Spec-Anchored Development Wins 2.md",
    "Agents/Harnesses/Harnesses Eager vs. Just-in-Time 2.md",
    "Agents/Hermes/Anatomy of an Excellent OpenCode Skill Lessons from cloudflare-skill 2.md",
    "Agents/Hermes/Build and Connect Your First MCP Server to OpenCode on Windows 2.md",
    "Agents/Hermes/Building a Complete Personal Harness LLM Wiki + Developer\u2019s Second Brain in Obsidian 2.md",
    "Agents/Hermes/Copilot vs OpenCode on a Real FIDO2 Server 2.md",
    "Agents/Hermes/Do These 5 Things First After Installing Hermes Agent 2.md",
    "Agents/Hermes/Generate HTML First, Then Export to PDF 1 2.md",
    "Agents/Hermes/Git for Agent Memory Why You Should Treat Hermes Skills Like Code 2.md",
    "Agents/Hermes/GitLab\u2019s Official MCP Server One Config Line, One Hidden Gate 2.md",
    "Agents/Hermes/Hermes + Open Router as replacement for GitHub Copilot 2.md",
    "Agents/Hermes/Hermes AI Assistant Skills \u2014 for Real Production Setups 2.md",
    "Agents/Hermes/Hermes AI Assistant \u2014 Install, Setup, Workflow, and Troubleshooting 2.md",
    "Agents/Hermes/Hermes Agent + Ollama FASTEST Way to Install Locally 2.md",
    "Agents/Hermes/Hermes Agent + Polymarket \u2014 how i built self-learning weather trading bot $100 \u2192 $5,000 ( guide ) 2.md",
    "Agents/Hermes/Hermes Agent Advanced self-evolving skills, MCP, subagents, and production 2.md",
    "Agents/Hermes/Hermes Agent CLI cheat sheet \u2014 commands, flags, and slash shortcuts 2.md",
    "Agents/Hermes/Hermes Agent Desktop A Step-by-Step Settings Guide for Real Workflows 2.md",
    "Agents/Hermes/Hermes Agent Just Beat Claude Code on GitHub. But the Agent on My Server Already Does What Hermes Promises 2.md",
    "Agents/Hermes/Hermes Agent Memory System How Persistent AI Memory Actually Works 2.md",
    "Agents/Hermes/Hermes Agent Official Desktop Launch Zero-Configuration Across All Platforms, Seamless Migration for OpenClaw Users 2.md",
    "Agents/Hermes/Hermes Agent Setup + Capturing Your Dev Patterns via OpenCode 2.md",
    "Agents/Hermes/Hermes Agent Skill Authoring \u2014 SKILL.md Structure and Best Practices 2.md",
    "Agents/Hermes/Hermes Agent Starter Under 10 Minutes Zero-to-GitOps Workflow 2.md",
    "Agents/Hermes/Hermes Agent The Hype, The Reality, and Who Should Actually Use It 2.md",
    "Agents/Hermes/Hermes Agent When the AI Lives on a Server Instead of in Our Editor 2.md",
    "Agents/Hermes/Hermes Agent for Beginners Install and First Run (Part -1) 2.md",
    "Agents/Hermes/Hermes Agent for Workflow Automation Everything You Need to Know 2.md",
    "Agents/Hermes/Hermes Agent in 2026 Install It Once, Then Let It Run Your Work 2.md",
    "Agents/Hermes/Hermes Agent the first AI agent that keeps what it learns 2.md",
    "Agents/Hermes/Hermes Agent\u2019s goal Command Makes AI Stop Quitting Halfway Through the Job 2.md",
    "Agents/Hermes/Hermes Skill Prompts/Hermes AI Assistant Skills for Real Production Setups 2.md",
    "Agents/Hermes/Hermes Skill Prompts/I Open-Sourced the Skills That Run My AI Fleet 2.md",
    "Agents/Hermes/Hermes Skill Prompts/I Used AI to Make My Own Daily Newspaper & Honestly It Has Changed My Life 2.md",
    "Agents/Hermes/Hermes Skill Prompts/Obsidian x Hermes Agent Is So Good I\u2019m Actively Deleting Day-to-Day Apps 2.md",
    "Agents/Hermes/Hermes Skill Prompts/Skill - Complaint Scout \u2014 Daily Micro-Product Opportunity Finder 2.md",
    "Agents/Hermes/Hermes Skill Prompts/The one where AI for Product Managers is actually good 1 2.md",
    "Agents/Hermes/Hermes Skill Prompts/Three Insights for Building Great Claude Skills 2.md",
    "Agents/Hermes/Hermes vs OpenClaw The First Real Rival in the Autonomous AI Agent Race 2.md",
    "Agents/Hermes/How The Hermes Agent Memory Really Works 2.md",
    "Agents/Hermes/How to Play with SOUL.md in Hermes Agent 2.md",
    "Agents/Hermes/How to Port an Existing Skill from Hermes Agent to OpenCode 1 2.md",
    "Agents/Hermes/How to Port an Existing Skill from Hermes Agent to OpenCode 2.md",
    "Agents/Hermes/I Built an AI Second Brain to cure my information overload. And here is how 2.md",
    "Agents/Hermes/I Connected Hermes Agent to ON Compute MCP - Now My Agent Can Run Real GPU Jobs 2.md",
    "Agents/Hermes/I Let Hermes Agent Process My Obsidian Vault Overnight 2.md",
    "Agents/Hermes/Introducing Hermes IDE An AI-Native Terminal That Actually Understands Your Projects 2.md",
    "Agents/Hermes/Introducing Kai (Kyberneees AI) A Universal Brain for OpenCode 2.md",
    "Agents/Hermes/Introducing ncoder 2.md",
    "Agents/Hermes/Migrating from chatbots to agents how Claude Code + Hermes helps teams ship 25% more PRs 2.md",
    "Agents/Hermes/Most Hermes Skills Are Broken \u2014 Here\u2019s Why 2.md",
    "Agents/Hermes/My Current Obsidian x Hermes Agent Setup (Full Configuration Breakdown) 2.md",
    "Agents/Hermes/My Journey in OpenCode\u002719 2.md",
    "Agents/Hermes/OpenCode Support in RexIDE from v2026.02.0106 2.md",
    "Agents/Hermes/Opencode 2.md",
    "Agents/Hermes/Opencode, an AI coding agent, built for the terminal 2.md",
    "Agents/Hermes/Turn Your Skills into a Fleet of Subagents \u2014 Then Run Them All at Once 2.md",
    "Agents/Hermes/What Is Hermes Agent and Why Is Everyone Talking About It 2.md",
    "Agents/Hermes/\U0001f680 OpenCode When the Terminal Becomes the Real IDE 2.md",
    "Agents/Use Cases/15 OpenClaw Use Cases What Actually Works in 2027.md",
    "Tools/Free Inference/8 Free Ways to Access GLM-5.2 2.md",
    "Money Making/I Tracked Every Prompt I Used for 30 Days. Only 4 Categories Actually Made Money 2.md",
    "Video/How to Build an AI Animation Factory That Runs 248.md",
    "0-ToDo/AI Profile 2.md",
    "Obsidian/Obsidian CLI How the Command Line Will Change Note\u2011Taking 2.md",
    "Obsidian/obsidian-skills Teaches Your Agent to Drive Obsidian, Not Just Read It 2.md",
    "Models/NVIDIA Just Dropped the Most Efficient Reasoning Model of 2027.md",
]

state_file = Path.home() / ".hermes" / "scripts" / "wiki-vault-ingest-state.json"
state = json.loads(state_file.read_text())
now = datetime.now().isoformat()
today = datetime.now().strftime("%Y-%m-%d")

added = 0
verified = 0
for f in deadlocked:
    if f not in state.get("ingested", {}):
        state["ingested"][f] = {
            "ingested": today,
            "sha256": "deadlock_unreadable_sparse_file_blocks0",
            "last_processed": now,
            "pages_updated": 0,
            "note": "File exists in vault (ls/stat) but is a sparse file with blocks=0; cannot be read (EDEADLK). Untracked by git."
        }
        added += 1
    else:
        verified += 1

state_file.write_text(json.dumps(state, indent=2, default=str))
print(f"Marked {added} deadlocked/sparse files as ingested in state file")
print(f"Already in state: {verified}")
print(f"Total ingested files in state: {len(state.get('ingested', {}))}")
