#!/usr/bin/env python3
"""Fetch the magnet link for a specific search result."""
import sys
import requests
from html.parser import HTMLParser
from search import search, BASE_URL, FLARESOLVERR


class MagnetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.magnet = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value and value.startswith("magnet:"):
                    self.magnet = value


def get_magnet(href):
    url = BASE_URL + href
    print(f"Fetching: {url}")

    resp = requests.post(FLARESOLVERR, json={
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000
    })
    resp.raise_for_status()

    data = resp.json()
    if data.get("status") != "ok":
        print(f"Error: {data.get('message')}")
        sys.exit(1)

    html = data["solution"]["response"]
    parser = MagnetParser()
    parser.feed(html)
    return parser.magnet


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 magnet.py <result_number> <query> [page]")
        sys.exit(1)

    index = int(sys.argv[1]) - 1
    query = sys.argv[2]
    page = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    results = search(query, page)
    if index < 0 or index >= len(results):
        print(f"Invalid result number. Found {len(results)} results.")
        sys.exit(1)

    result = results[index]
    print(f"\nTitle: {result.get('name')}")
    print(f"Size:  {result.get('size')}  Seeds: {result.get('seeds')}")

    magnet = get_magnet(result["href"])
    if magnet:
        print(f"\nMagnet:\n{magnet}")
    else:
        print("Magnet link not found on page.")


if __name__ == "__main__":
    main()
