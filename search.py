#!/usr/bin/env python3
import sys
import requests
from html.parser import HTMLParser

FLARESOLVERR = "http://localhost:8191/v1"
BASE_URL = "https://1337x.to"


class ResultParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self._current = {}
        self._capture = None   # which field we're collecting text for
        self._skip_span = False

    def _classes(self, attrs):
        return dict(attrs).get("class", "")

    def handle_starttag(self, tag, attrs):
        classes = self._classes(attrs)
        attrs_dict = dict(attrs)

        if tag == "tr":
            self._current = {}
            self._capture = None

        elif tag == "td":
            if "coll-2 seeds" in classes:
                self._capture = "seeds"
            elif "coll-3 leeches" in classes:
                self._capture = "leeches"
            elif "coll-4 size" in classes:
                self._capture = "size"
                self._skip_span = False
            else:
                self._capture = None

        elif tag == "a" and "href" in attrs_dict:
            href = attrs_dict["href"]
            if href.startswith("/torrent/") and "href" not in self._current:
                self._current["href"] = href
                self._capture = "name"

        elif tag == "span" and self._capture == "size":
            # skip the <span class="seeds"> inside the size cell
            self._skip_span = True

    def handle_endtag(self, tag):
        if tag == "a" and self._capture == "name":
            self._capture = None
        if tag == "td":
            self._capture = None
            self._skip_span = False
        if tag == "span":
            self._skip_span = False
        if tag == "tr" and "href" in self._current and "name" in self._current:
            self.results.append(dict(self._current))

    def handle_data(self, data):
        data = data.strip()
        if not data or not self._capture or self._skip_span:
            return
        if self._capture not in self._current:
            self._current[self._capture] = data


def search(query, page=1):
    url = f"{BASE_URL}/search/{requests.utils.quote(query)}/{page}/"
    print(f"Searching: {url}")

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
    parser = ResultParser()
    parser.feed(html)
    return parser.results


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 search.py <query> [page]")
        sys.exit(1)

    query = sys.argv[1]
    page = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    results = search(query, page)

    if not results:
        print("No results found.")
        return

    print(f"\n{'#':<4} {'Seeds':<7} {'Size':<12} Name")
    print("-" * 80)
    for i, r in enumerate(results, 1):
        name = r.get("name", "?")[:55]
        seeds = r.get("seeds", "?")
        size = r.get("size", "?")
        print(f"{i:<4} {seeds:<7} {size:<12} {name}")

    print(f"\n{len(results)} results on page {page}")
    print("\nTo get the magnet link for result #N:")
    print(f"  python3 magnet.py <N> '{query}' [page]")


if __name__ == "__main__":
    main()
