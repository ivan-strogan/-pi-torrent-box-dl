# pi-torrent-box

A self-hosted torrent search box running on a Raspberry Pi 3, using FlareSolverr to bypass Cloudflare and Jackett as the search indexer — integrated with Synology Download Station.

## Architecture

```
Raspberry Pi 3
├── FlareSolverr  (port 8191) — bypasses Cloudflare on torrent sites
└── Jackett       (port 9117) — search UI + indexer, talks to FlareSolverr

Synology NAS (Download Station) — receives torrents from Jackett
```

## Requirements

- Raspberry Pi 3 (or newer) running Raspberry Pi OS Lite 64-bit
- Docker + Docker Compose installed on the Pi
- Synology NAS with Download Station

## Setup

See [docs/pi-setup.md](docs/pi-setup.md) for full step-by-step instructions covering:
1. Flashing the Pi
2. Installing Docker
3. Running FlareSolverr + Jackett
4. Configuring Jackett with FlareSolverr and 1337x
5. Wiring up Synology Download Station

## Quick Start

Once the Pi is set up and on your network:

```bash
# SSH into the Pi
ssh pi@<pi-ip>

# Clone this repo
git clone git@github.com:ivan-strogan/pi-torrent-box.git
cd pi-torrent-box

# Start services
docker compose up -d
```

Then open Jackett at `http://<pi-ip>:9117` to search and push to Download Station.

## CLI Search Scripts

For searching 1337x directly from the command line (requires FlareSolverr running):

```bash
# Search
python3 search.py "movie name"

# Get magnet link for result #1
python3 magnet.py 1 "movie name"
```
