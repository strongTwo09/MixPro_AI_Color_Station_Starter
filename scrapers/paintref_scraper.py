# -*- coding: utf-8 -*-
"""
Scraper: PaintRef.com car paint colors
--------------------------------------
ดึงข้อมูลสีรถยนต์ตามยี่ห้อ + ปี
แล้วบันทึกเป็น JSON เพื่อนำไปสร้าง dataset

วิธีใช้:
    python scrapers/paintref_scraper.py
"""

import os, json, time, random
import requests
from bs4 import BeautifulSoup

OUT_PATH = os.path.join(os.path.dirname(__file__), "car_colors.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://paintref.com/",
    "Connection": "keep-alive",
}

BASE_URL = "https://paintref.com/cgi-bin/colorcodedisplay.cgi"

def fetch_colors(make, year, rows=50, max_pages=1):
    """ดึงข้อมูลสีจาก paintref (make=Toyota, year=2020)"""
    colors = []
    for page in range(max_pages):
        offset = page * rows
        url = f"{BASE_URL}?make={make}&year={year}&rows={rows}&firstrow={offset}"
        print(f"Fetching: {url}")

        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                print(f"❌ Failed {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            table = soup.find("table", {"class": "colorstable"})
            if not table:
                print("❌ No table found")
                continue

            for row in table.find_all("tr")[1:]:  # skip header
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue
                color_name = cols[0].get_text(strip=True)
                code = cols[1].get_text(strip=True)
                hex_span = cols[0].find("span")
                hex_value = None
                if hex_span and "style" in hex_span.attrs:
                    style = hex_span["style"]
                    if "background" in style:
                        hex_value = style.split(":")[-1].strip()
                if not hex_value or not hex_value.startswith("#"):
                    continue

                colors.append({
                    "make": make,
                    "year": year,
                    "name": color_name,
                    "code": code,
                    "hex": hex_value.lower()
                })

            time.sleep(random.uniform(1.0, 2.5))  # polite delay

        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    return colors


if __name__ == "__main__":
    MAKES = ["Toyota", "Honda"]
    YEARS = [2019, 2020]
    all_colors = []

    for make in MAKES:
        for year in YEARS:
            cols = fetch_colors(make, year, max_pages=2)
            all_colors.extend(cols)

    print(f"✅ Total colors fetched: {len(all_colors)}")
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_colors, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved to {OUT_PATH}")
