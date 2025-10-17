# -*- coding: utf-8 -*-
"""
Pexels Car Dataset Downloader
-----------------------------
สคริปต์นี้จะดาวน์โหลดภาพรถยนต์ตามชื่อสีจาก Pexels API
แล้วจัดเก็บเป็น dataset สำหรับ train classifier

วิธีใช้:
    1. สมัคร API key ที่ https://www.pexels.com/api/
    2. แก้ค่า PEXELS_API_KEY ด้านล่าง
    3. รัน: python scrapers/pexels_car_dataset.py
"""

# -*- coding: utf-8 -*-
"""
Pexels Car Dataset Downloader (Legacy Version)
----------------------------------------------
รองรับ Python 2.7 / 3.x — ไม่มีการใช้ f-string

ดาวน์โหลดภาพรถตามสีจาก Pexels API
"""

import os
import sys
import requests
import time
from urllib import urlencode
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x, **k: x  # fallback ถ้า tqdm ไม่มี

# ====== ตั้งค่า ======
PEXELS_API_KEY = "zeCx3h0dJ144BglUNWyA1xJapleadBtq98hubTcK1IbUzPftcawcGpxP"  # 🔑 ใส่คีย์ของคุณตรงนี้
SAVE_DIR = os.path.join(os.path.dirname(__file__), "../dataset")
COLORS = ["Black", "White", "Red", "Blue", "Silver", "Gray"]
IMAGES_PER_COLOR = 100  # ต่อสี

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

HEADERS = {"Authorization": PEXELS_API_KEY}

# ====== ฟังก์ชันหลัก ======
def fetch_images(color, per_page=80, max_pages=5):
    """ดึง URL ของภาพรถจาก Pexels API"""
    urls = []
    query = color + " car"
    for page in range(1, max_pages + 1):
        params = {"query": query, "per_page": per_page, "page": page}
        url = "https://api.pexels.com/v1/search?" + urlencode(params)
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
        except Exception as e:
            print("❌ {} page {} failed: {}".format(color, page, e))
            continue

        if r.status_code != 200:
            print("❌ {} page {} failed ({})".format(color, page, r.status_code))
            continue

        data = r.json()
        photos = data.get("photos", [])
        for photo in photos:
            src = photo.get("src", {}).get("large")
            if src:
                urls.append(src)
        time.sleep(1.0)
    return urls[:IMAGES_PER_COLOR]


def download_image(url, save_path):
    """ดาวน์โหลดภาพเดี่ยว"""
    try:
        r = requests.get(url, stream=True, timeout=10)
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            return True
    except Exception as e:
        print("⚠️ Download failed:", e)
    return False


if __name__ == "__main__":
    print("🚗 Starting Pexels Car Dataset Downloader (Python {})".format(sys.version.split()[0]))
    for color in COLORS:
        out_dir = os.path.join(SAVE_DIR, "train", color)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        urls = fetch_images(color)
        print("🎨 {}: {} images found".format(color, len(urls)))

        i = 0
        for url in tqdm(urls, desc="Downloading {}".format(color)):
            i += 1
            fname = "{}_{:03d}.jpg".format(color.lower(), i)
            fpath = os.path.join(out_dir, fname)
            if not os.path.exists(fpath):
                download_image(url, fpath)

    print("✅ Dataset saved to {}".format(os.path.abspath(SAVE_DIR)))
