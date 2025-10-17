# -*- coding: utf-8 -*-
"""
Scrape basic color listings from paintref.com (brand pages) to build a simple CSV/JSON.

NOTE: Run this script on your own machine with internet access.
"""
import re, json, csv, sys, time
from urllib.parse import urljoin
from html.parser import HTMLParser
import urllib.request

BASE = "https://paintref.com/"
BRANDS = ["toyota", "honda", "mazda", "nissan", "ford", "isuzu", "bmw", "mercedes", "hyundai", "kia", "mg"]

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            href = dict(attrs).get("href","")
            if href: self.links.append(href)

def fetch(url):
    with urllib.request.urlopen(url) as r:
        return r.read().decode("utf-8","ignore")

def scrape_brand(brand):
    # very simple approach: find pages containing "color chips" links
    url = f"https://paintref.com/cgi-bin/colors.cgi?manu={brand}"
    html = fetch(url)
    p = LinkParser(); p.feed(html)
    out = []
    # naive color hex finder
    for href in p.links:
        if "colorchip.cgi" in href and "paint=" in href:
            page = urljoin(BASE, href)
            h2 = fetch(page)
            # find hex like #A1B2C3 in style/background
            for m in re.finditer(r"#([0-9A-Fa-f]{6})", h2):
                hx = m.group(0).upper()
                out.append({"brand": brand.title(), "hex": hx, "source": page})
    # deduplicate
    uniq = {}
    for o in out:
        uniq[(o["brand"], o["hex"])] = o
    return list(uniq.values())

def main():
    allrows = []
    for b in BRANDS:
        try:
            rows = scrape_brand(b)
            print(b, "=>", len(rows), "records")
            allrows.extend(rows)
            time.sleep(0.5)
        except Exception as e:
            print("ERR", b, e)
    # save
    with open("paintref_colors.json","w",encoding="utf-8") as f:
        json.dump(allrows, f, ensure_ascii=False, indent=2)
    with open("paintref_colors.csv","w",encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["brand","hex","source"])
        w.writeheader(); w.writerows(allrows)
    print("Saved paintref_colors.json / .csv")

if __name__ == "__main__":
    main()
