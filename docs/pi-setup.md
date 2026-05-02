# Raspberry Pi Setup Guide

Full setup from a blank SD card to a running torrent box.

## What You Need

- Raspberry Pi 3 (1GB RAM)
- MicroSD card (16GB+ recommended)
- Another computer to flash the SD card
- Ethernet cable (recommended) or WiFi

---

## Step 1 — Flash the SD Card

1. Download and install **Raspberry Pi Imager**: https://www.raspberrypi.com/software/
2. Insert your microSD card
3. In the Imager:
   - **Device**: Raspberry Pi 3
   - **OS**: Raspberry Pi OS Lite (64-bit) — under "Raspberry Pi OS (other)"
   - **Storage**: your microSD card
4. Click the **gear icon** (Edit Settings) before flashing:
   - Set hostname: `torrent-pi`
   - Enable SSH → Use password authentication
   - Set username: `pi` and a password of your choice
   - Configure WiFi if not using ethernet
5. Click **Save**, then **Write**

---

## Step 2 — Boot and Connect

1. Insert the SD card into the Pi and power it on
2. Wait ~60 seconds for first boot
3. Find the Pi's IP (check your router's DHCP list, or use `ping torrent-pi.local`)
4. SSH in:

```bash
ssh pi@torrent-pi.local
# or
ssh pi@<pi-ip-address>
```

---

## Step 3 — Set Up Swap (important for Pi 3's 1GB RAM)

FlareSolverr launches Chrome which is memory-heavy. Add swap to prevent crashes:

```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE=100 to CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

---

## Step 4 — Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker pi
newgrp docker
```

Verify:

```bash
docker --version
```

---

## Step 5 — Clone and Start Services

```bash
git clone git@github.com:ivan-strogan/pi-torrent-box.git
cd pi-torrent-box
docker compose up -d
```

This starts:
- **FlareSolverr** on port `8191`
- **Jackett** on port `9117`

Check both are running:

```bash
docker ps
curl http://localhost:8191/  # should return {"msg":"FlareSolverr is ready!"}
```

---

## Step 6 — Configure Jackett

1. Open Jackett in a browser: `http://torrent-pi.local:9117`
2. Set an **Admin password** when prompted
3. Go to **FlareSolverr** section and enter: `http://flaresolverr:8191` (uses Docker's internal network)
4. Click **+ Add Indexer**, search for **1337x**, and add it
5. Test the indexer — it should return results

---

## Step 7 — Connect to Synology Download Station

In Jackett, after adding 1337x:

1. Click the **wrench icon** next to 1337x
2. Copy the **Torznab feed URL** — looks like: `http://torrent-pi.local:9117/api/v2.0/indexers/1337x/results/torznab/`
3. Copy the **Jackett API key** (shown at the top of the Jackett UI)

In Synology DSM:
1. Open **Download Station** → Settings → **BT Search**
2. Add a new search module using the Torznab URL and API key
   - Alternatively, search in Jackett and use the **Download** button to send directly to Download Station via its IP: `http://192.168.0.99`

---

## Keeping Services Running

Both services are set to `restart: unless-stopped`, so they'll start automatically on reboot.

To update:

```bash
cd ~/pi-torrent-box
docker compose pull
docker compose up -d
```
