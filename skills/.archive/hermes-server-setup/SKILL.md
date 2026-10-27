---
name: hermes-server-setup
description: "Use when starting or exposing hermes dashboard."
version: 1.0.0
author: Hermes Agent User
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [hermes, dashboard, serve, port, auth, network, server]
    homepage: https://github.com/NousResearch/hermes-agent
---

# Hermes Server / Dashboard Setup

Procedures for starting `hermes dashboard` or `hermes serve` with explicit host/port binding, enabling remote access, and troubleshooting common bind failures.

## Defaults & Port Quirks

- `hermes dashboard` defaults to `127.0.0.1:9119` (loopback only).
- `hermes serve` (the headless backend) also defaults to `127.0.0.1:9119`.
- **The Hermes Desktop app spawns its own backend with `--port 0`** (random ephemeral port) — hardcoded in the Electron source and NOT user-configurable. You cannot make the Desktop app's bundled backend listen on 9119.
- To get a persistent, port-fixed, network-exposed backend, run `hermes dashboard --host 0.0.0.0 --port 9119 --no-open` yourself.

## Procedure: Expose Dashboard on All Interfaces (Port 9119)

### Step 1 — Generate a password hash

Hermes refuses to bind to a non-loopback address without an auth provider. Username/password is the simplest for LAN use:

```bash
cd ~/.hermes/hermes-agent
venv/bin/python -c "from plugins.dashboard_auth.basic import hash_password; print(hash_password('your-password'))"
```

Outputs a scrypt hash string like `scrypt$16384$8$1$...$...`.

### Step 2 — Add auth config to ~/.hermes/config.yaml

`hermes config set` will refuse to write security-sensitive keys. Edit directly:

```bash
cat >> ~/.hermes/config.yaml << 'EOF'

dashboard:
  basic_auth:
    username: admin
    password_hash: <paste-scrypt-hash-here>
EOF
```

Verify: `tail -5 ~/.hermes/config.yaml` should show the new block.

### Step 3 — Start the server in background

```bash
hermes dashboard --host 0.0.0.0 --port 9119 --no-open
```

**IMPORTANT:** Run this as a background process — `terminal(background=true)` — or it will block the session. The dashboard is a long-running server.

### Step 4 — Verify

```bash
lsof -i :9119 -n -P
```

You should see `TCP *:9119 (LISTEN)` (the `*` means all interfaces). If you only see outbound connections to `100.69.163.14:9119`, those are NOT the dashboard — they're outbound from the Hermes GPU process. A working dashboard shows `LISTEN`.

## Making It Survive

The background process started by `terminal(background=true)` dies when the session ends. For a persistent dashboard:

- **tmux**: `tmux new-session -d -s hermes-dashboard 'hermes dashboard --host 0.0.0.0 --port 9119 --no-open'`
- **systemd** (user unit): bind to 0.0.0.0, use `EnvironmentFile=%h/.hermes/.env` if you need `.env` vars loaded.

## Pitfalls

1. **"No auth providers registered" bind refusal** — If you try `--host 0.0.0.0` without configuring `dashboard.basic_auth` or OAuth, Hermes refuses to start. The error message explicitly names the missing provider.

2. **Confusing outbound connections for a listening server** — `lsof -i :9119` may show outbound TCP connections (state ESTABLISHED or CLOSE_WAIT) to `100.69.163.14:9119` from the Hermes GPU/renderer processes. These are NOT the dashboard. A real dashboard listener shows `TCP *:9119 (LISTEN)`. Look for the `LISTEN` keyword.

3. **`hermes config set` refuses security keys** — Don't use `hermes config set dashboard.basic_auth.username ...`. It will be rejected. Edit `~/.hermes/config.yaml` directly.

4. **Stale password hash in config** — If you regenerate the hash and the dashboard was already running, restart it. The in-memory hash only loads at boot.

5. **Desktop app ignores port 9119** — If you launch `hermes desktop`, it spawns its own backend on a random port regardless of what's in config.yaml. The desktop app is not a way to serve the dashboard on a fixed port.

6. **Use `--no-open`** — Without this flag, `hermes dashboard` opens a browser window. On a headless server or background process, this fails or wastes resources.