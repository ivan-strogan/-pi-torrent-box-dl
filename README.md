# pi-torrent-box-dl

A self-hosted torrent search and download system integrated with Synology Download Station. Search 1337x.to directly from within Download Station's built-in search UI, with results sent automatically to the download queue.

---

## How It Works

1. You type a search in **Synology Download Station's BT Search**
2. Download Station calls a custom search plugin (`.dlm`) installed on the NAS
3. The plugin sends the query to **Jackett** (running on the Raspberry Pi)
4. Jackett passes the request to **FlareSolverr** (running on the Synology NAS)
5. FlareSolverr launches a headless Chrome browser to bypass Cloudflare protection on 1337x.to
6. Results flow back through Jackett → plugin → Download Station
7. You click a result and it downloads directly in Download Station

```
Synology Download Station
        │
        │ (BT Search via .dlm plugin)
        ▼
Raspberry Pi 3 — 192.168.0.6
└── Jackett (port 9117)
        │
        │ (Torznab API → FlareSolverr)
        ▼
Synology NAS — 192.168.0.99
└── FlareSolverr (port 8191)
        │
        │ (headless Chrome)
        ▼
    1337x.to
```

---

## Network Layout

| Device | IP | Role |
|---|---|---|
| Raspberry Pi 3 | 192.168.0.6 | Runs Jackett |
| Synology DS3615xs | 192.168.0.99 | Runs FlareSolverr + Download Station |
| Pi-hole | 192.168.0.5 | DNS for the network |
| Router/Gateway | 192.168.0.1 | Network gateway |

---

## Components

### FlareSolverr
FlareSolverr is a proxy server that solves Cloudflare challenges using a real headless Chrome browser. Sites like 1337x.to are protected by Cloudflare, which blocks normal HTTP requests. FlareSolverr launches Chrome, solves the JavaScript challenge, and returns the page content and cookies so other tools can access the site.

- **Runs on**: Synology NAS (192.168.0.99)
- **Port**: 8191
- **Docker image**: `ghcr.io/flaresolverr/flaresolverr:latest`
- **Why on NAS and not Pi**: The Raspberry Pi 3 only has 1GB RAM. Chrome requires ~300–500MB+ to launch. During testing, FlareSolverr consistently timed out on the Pi 3 (taking 100+ seconds), which exceeded Jackett's hardcoded 100-second HTTP timeout. The Synology DS3615xs has an Intel Core i3 processor and solves the challenge in ~10–12 seconds.

### Jackett
Jackett is a torrent indexer proxy. It translates search queries into site-specific scraping, handles authentication, pagination, and result formatting. It exposes a standardized Torznab API that other tools (Sonarr, Radarr, Download Station plugins) can query.

- **Runs on**: Raspberry Pi 3 (192.168.0.6)
- **Port**: 9117
- **Docker image**: `lscr.io/linuxserver/jackett:latest`
- **Configured indexer**: 1337x
- **FlareSolverr URL** (set in Jackett UI): `http://192.168.0.99:8191`
- **FlareSolverr Max Timeout** (set in Jackett UI): `120000` ms

### Download Station Plugin (.dlm)
A custom PHP search plugin for Synology Download Station. It queries Jackett's Torznab API and returns results directly in the Download Station search UI.

- **File**: `dlm/1337x-pi-jackett.dlm`
- **Format**: `tar.gz` archive renamed to `.dlm` containing `INFO` (JSON) and `search.php`
- **Jackett API key** is hardcoded in `search.php` — update it if you regenerate the key in Jackett

---

## Hardware Requirements

- Raspberry Pi 3 (1GB RAM) — Pi 4/5 also works, Pi Zero will not
- Synology NAS with Container Manager (Docker) support
- MicroSD card (16GB+) for the Pi

---

## Initial Pi Setup

### 1. Flash the SD Card

Use **Raspberry Pi Imager** (https://www.raspberrypi.com/software/):
- **OS**: Raspberry Pi OS Lite (64-bit) — under "Raspberry Pi OS (other)"
- **Settings** (gear icon before flashing):
  - Hostname: `torrent-pi`
  - Enable SSH with password authentication
  - Set username and password
  - Enter WiFi credentials

> **Important**: In newer Raspberry Pi OS (Bookworm), SSH is **disabled by default** even if you configure it in the Imager. After flashing, mount the boot partition and:
> 1. Create an empty file called `ssh` in the root of the boot partition
> 2. Add the following to the `user-data` cloud-init file:
> ```yaml
> ssh_pwauth: true
> runcmd:
>   - systemctl enable ssh
>   - systemctl start ssh
> ```
> Without both steps, SSH will be refused on first boot.

### 2. First Boot Configuration

The Pi uses cloud-init for first boot. The `user-data` and `network-config` files on the boot partition configure the user, WiFi, and SSH. See `docs/pi-setup.md` for the exact file contents.

### 3. Set a Static IP

After connecting to the Pi, set a static IP using NetworkManager:

```bash
sudo nmcli connection modify 'netplan-wlan0-YOURSSID' \
  ipv4.addresses 192.168.0.6/24 \
  ipv4.gateway 192.168.0.1 \
  ipv4.dns 192.168.0.5 \
  ipv4.method manual
sudo nmcli connection up 'netplan-wlan0-YOURSSID'
```

To find your connection name first: `nmcli connection show`

### 4. Install Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
```

### 5. Start Jackett

```bash
git clone https://github.com/ivan-strogan/-pi-torrent-box-dl.git
cd -- -pi-torrent-box-dl
docker compose up -d
```

---

## FlareSolverr on Synology NAS

### Why Not via the Container Manager UI?

The Container Manager UI does not expose a "host network" option when creating containers. FlareSolverr **must** use host networking on Synology (see networking note below), so it must be created via SSH.

### Install via SSH

SSH into the Synology NAS and run:

```bash
sudo docker run -d \
  --name flaresolverr-flaresolverr1 \
  --network host \
  -e LOG_LEVEL=info \
  -e TZ=America/Toronto \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest
```

Verify it's running:
```bash
curl http://192.168.0.99:8191/
# Should return: {"msg": "FlareSolverr is ready!", ...}
```

> **Why `--network host`**: The Synology DSM iptables configuration blocks outbound internet traffic from Docker bridge networks by default. With bridge networking, Chrome inside the container gets `net::ERR_NAME_NOT_RESOLVED` for every URL — even with `--dns 8.8.8.8` explicitly set. Using host networking gives the container the NAS's full network stack and bypasses this entirely. With host networking, port mapping (`-p`) is not needed — port 8191 is available automatically on the NAS IP.

---

## Jackett Configuration

1. Open Jackett at `http://192.168.0.6:9117`
2. Set an admin password
3. Set **FlareSolverr API URL** to `http://192.168.0.99:8191`
4. Set **FlareSolverr Max Timeout** to `120000`
5. Click **Apply server settings**
6. Click **+ Add Indexer**, find and add **1337x**
7. Test the indexer — it should return results within ~15 seconds

---

## Download Station Plugin Installation

1. Copy `dlm/1337x-pi-jackett.dlm` to your computer
2. In DSM, open **Download Station → Settings → BT Search**
3. Click **Add** and upload the `.dlm` file
4. Enable the plugin in the search settings

To rebuild the `.dlm` after making changes to `search.php` or `INFO`:
```bash
cd dlm
tar -czf 1337x-pi-jackett.dlm INFO search.php
```

---

## What We Tried That Didn't Work

### FlareSolverr on Raspberry Pi 3
FlareSolverr needs to launch a full Chrome browser per request. The Pi 3's 1GB RAM and slower ARM CPU meant Chrome took 100–180 seconds to launch and solve the Cloudflare challenge. Jackett has a hardcoded 100-second HttpClient timeout that cannot be configured from the UI, so every search timed out. Even with a persistent FlareSolverr session (to keep Chrome warm between requests), the Pi 3 was consistently too slow. **Solution**: move FlareSolverr to the Synology NAS (Intel Core i3, x86-64).

### Docker Bridge Networking on Synology
When FlareSolverr ran in a standard Docker container on the Synology using bridge networking, Chrome had no internet access at all — `net::ERR_NAME_NOT_RESOLVED` for every URL. This was true even after setting `--dns 8.8.8.8` explicitly on the container. The DSM iptables rules block outbound traffic from Docker bridge networks by default and this cannot be changed through the Container Manager UI. **Solution**: use `--network host`.

### Pi-hole Suspected of Blocking 1337x.to
The `ERR_NAME_NOT_RESOLVED` error initially suggested Pi-hole (192.168.0.5) was blocking 1337x.to. Pi-hole logs were checked filtered by the NAS IP (192.168.0.99) — no blocks found. The real cause was Docker bridge networking (see above).

### Python-based .dlm Plugin
The first version of the Download Station plugin was written in Python with a `.conf`/`.py` structure packaged as a **zip** file. Synology's plugin format changed across DSM versions:
- **DSM 6**: supported Python plugins packaged as zip with an `[info]` conf format
- **DSM 7**: requires PHP plugins packaged as **tar.gz** with a JSON `INFO` file and a PHP class implementing `prepare()` and `parse()` methods

The Python zip was rejected as "invalid plugin" on DSM 7.1.1. **Solution**: rewrite entirely in PHP as a `tar.gz`.

### Jackett Search Query Not Passing Through
After the PHP plugin was accepted and installed, searches returned 80 generic results regardless of what was searched. Jackett logs showed `Torznab search in 1337x => Found 80 releases` with no query term logged — meaning an empty query was being sent to Jackett, which returned the latest/trending results instead. The URL was using `Query=search_term` as the parameter name. **Solution**: change to `t=search&q=search_term` which is the correct Torznab API specification that Jackett recognises.

---

## Updating

### Update Jackett on Pi
```bash
ssh ivan@192.168.0.6
cd -- -pi-torrent-box-dl
git pull
docker compose pull
docker compose up -d
```

### Update FlareSolverr on Synology
```bash
ssh istrogan@192.168.0.99
sudo docker pull ghcr.io/flaresolverr/flaresolverr:latest
sudo docker stop flaresolverr-flaresolverr1
sudo docker rm flaresolverr-flaresolverr1
sudo docker run -d \
  --name flaresolverr-flaresolverr1 \
  --network host \
  -e LOG_LEVEL=info \
  -e TZ=America/Toronto \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest
```

---

## CLI Search Scripts

For searching without Download Station (requires FlareSolverr running at `192.168.0.99:8191`):

```bash
# Search
python3 search.py "movie name"

# Get magnet link for result #1
python3 magnet.py 1 "movie name"
```

---

## Jackett API Key

The Jackett API key is shown at the top of the Jackett UI at `http://192.168.0.6:9117`. It is hardcoded in `dlm/search.php`. If you regenerate the key in Jackett, update `search.php` and rebuild the `.dlm` file.
