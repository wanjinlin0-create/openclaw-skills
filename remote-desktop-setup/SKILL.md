---
name: remote-desktop-setup
description: "Deploy a headless remote desktop environment on Debian/Ubuntu servers using Xvfb + x11vnc + noVNC. Supports browser-based remote access via Cloudflare Tunnel. Use when: (1) Setting up remote desktop on a headless Linux server, (2) Need browser-based VNC access without client software, (3) Configuring Xfce4 desktop environment for remote work, (4) Setting up secure remote access with tunneling."
---

# Remote Desktop Setup

Complete remote desktop solution for headless Linux servers.

## Architecture

```
┌─────────────┐     ┌──────────┐     ┌──────────┐     ┌──────────────┐
│   Browser   │────▶│ noVNC    │────▶│ x11vnc   │────▶│ Xvfb + Xfce4 │
│   (User)    │◀────│ (Web)    │◀────│ (VNC)    │◀────│ (Desktop)    │
└─────────────┘     └──────────┘     └──────────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Cloudflare   │
                    │ Tunnel       │
                    └──────────────┘
```

## Quick Start

1. **Install dependencies:**
   ```bash
   bash scripts/install.sh
   ```

2. **Configure and start services:**
   ```bash
   bash scripts/setup.sh
   ```

3. **Setup Cloudflare Tunnel (optional, for external access):**
   ```bash
   bash scripts/setup-tunnel.sh
   ```

## What Gets Installed

| Component | Purpose | Port |
|-----------|---------|------|
| Xvfb | Virtual X server | :1 (display) |
| Xfce4 | Lightweight desktop | - |
| x11vnc | VNC server | 5901 |
| noVNC + websockify | Browser VNC client | 6080 |
| cloudflared | Secure tunnel | - |

## Access Methods

### Local Network
```
http://<server-ip>:6080/vnc.html
```

### Via Cloudflare Tunnel (External)
```
https://<tunnel-url>/vnc.html
```

## Default Credentials

- **VNC Password:** `123456` (change in setup)
- **Display:** `:1`
- **VNC Port:** `5901`

## Management Commands

```bash
# Check service status
bash scripts/status.sh

# Restart all services
bash scripts/restart.sh

# Stop all services
bash scripts/stop.sh

# Change VNC password
x11vnc -storepasswd
```

## Troubleshooting

See [references/troubleshooting.md](references/troubleshooting.md) for common issues.

## Desktop Environment Options

| DE | Memory | Use Case |
|----|--------|----------|
| Xfce4 (default) | ~300MB | General use, balance |
| LXDE | ~200MB | Minimal resources |
| MATE | ~400MB | Traditional feel |

To use a different DE, modify `scripts/setup.sh` before running.

## Security Notes

- Default VNC password is weak - **change it immediately**
- Cloudflare Tunnel provides HTTPS encryption
- For production, consider:
  - Strong VNC password
  - Fail2ban for brute force protection
  - VPN instead of direct exposure
