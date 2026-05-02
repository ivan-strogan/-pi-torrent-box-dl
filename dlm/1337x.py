#!/usr/bin/python3
# -*- coding: utf-8 -*-

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

JACKETT_URL = "http://192.168.0.6:9117"
JACKETT_API_KEY = "0dhutx0dofdrjcscx29ni6xt8cne5c5t"
INDEXER = "1337x"

TORZNAB_NS = "http://torznab.com/schemas/2015/feed"


def search(keyword, category=None):
    results = []

    url = (
        f"{JACKETT_URL}/api/v2.0/indexers/{INDEXER}/results/torznab/"
        f"?apikey={JACKETT_API_KEY}&Query={urllib.parse.quote(keyword)}"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        response = urllib.request.urlopen(req, timeout=30)
        content = response.read()

        root = ET.fromstring(content)
        channel = root.find("channel")
        if channel is None:
            return results

        for item in channel.findall("item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            size = item.findtext("size", "0")

            seeds = "0"
            leechs = "0"
            magnet = ""

            for attr in item.findall(f"{{{TORZNAB_NS}}}attr"):
                name = attr.get("name", "")
                value = attr.get("value", "")
                if name == "seeders":
                    seeds = value
                elif name == "leechers":
                    leechs = value
                elif name == "magneturl":
                    magnet = value

            download_link = magnet if magnet else link

            if title and download_link:
                results.append({
                    "title": title,
                    "link": download_link,
                    "size": int(size) if size.isdigit() else 0,
                    "seeds": int(seeds) if seeds.isdigit() else 0,
                    "leechs": int(leechs) if leechs.isdigit() else 0,
                })

    except Exception:
        pass

    return results
