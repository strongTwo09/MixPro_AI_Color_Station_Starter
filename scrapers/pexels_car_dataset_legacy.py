# -*- coding: utf-8 -*-
"""
สร้าง dataset รถยนต์ตามสี (ใช้ Pexels API)
รองรับ Python 2.7 / 3.x
- ดาวน์โหลดภาพจาก Pexels
- Resize เป็น 224x224
- แบ่ง train/test (80/20)
- ✅ ข้ามการดาวน์โหลดซ้ำ (skip existing)
"""

import os
import sys
import json
import random
import shutil
import requests
from PIL import Image
from io import BytesIO

# ===== CONFIG =====
PEXELS_API_KEY = "zeCx3h0dJ144BglUNWyA1xJapleadBtq98hubTcK1IbUzPftcawcGpxP"
SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../dataset")
COLORS = ["Red", "Blue", "Black", "White", "Silver", "Gray"]
IMAGES_PER_COLOR = 150  # จำนวนภาพต่อสี
IMG_SIZE = (224, 224)
TRAIN_RATIO = 0.8

# ===== Helper =====
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def download_image(url, save_path):
    """ดาวน์โหลดภาพจาก URL → resize → บันทึก"""
    try:
        if os.path.exists(save_path):
            # skip ถ้ามีอยู่แล้ว
            print("⏭️  Skip existing:", os.path.basename(save_path))
            return True
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            print("❌ Failed:", url)
            return False
        im = Image.open(BytesIO(r.content)).convert("RGB")
        im = im.resize(IMG_SIZE)
        im.save(save_path, "JPEG", quality=90)
        return True
    except Exception as e:
        print("⚠️ Error downloading {}: {}".format(url, e))
        return False

def fetch_pexels_images(query, per_page=50, pages=3):
    """ดึงลิงก์ภาพจาก Pexels"""
    headers = {"Authorization": PEXELS_API_KEY}
    results = []
    for page in range(1, pages+1):
        url = "https://api.pexels.com/v1/search?query={}&per_page={}&page={}".format(query, per_page, page)
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print("❌ Request failed:", r.status_code)
            continue
        data = r.json()
        for photo in data.get("photos", []):
            if "src" in photo:
                results.append(photo["src"]["medium"])
    return results

# ===== Main =====
def build_dataset():
    ensure_dir(SAVE_DIR)
    tmp_dir = os.path.join(SAVE_DIR, "_temp")
    ensure_dir(tmp_dir)

    all_records = []

    for color in COLORS:
        print("\n🎨 Downloading color:", color)
        urls = fetch_pexels_images("{} car".format(color.lower()), per_page=50, pages=3)
        random.shuffle(urls)
        urls = urls[:IMAGES_PER_COLOR]

        color_dir = os.path.join(tmp_dir, color)
        ensure_dir(color_dir)

        existing = set(os.listdir(color_dir))
        count = 0
        for i, url in enumerate(urls):
            fname = "{}_{:03d}.jpg".format(color.lower(), i + 1)
            save_path = os.path.join(color_dir, fname)
            ok = download_image(url, save_path)
            if ok:
                count += 1
        print("✅ Saved/Kept {} images for color {}".format(count, color))
        all_records.append({"color": color, "count": count})

    # ===== Split train/test =====
    print("\n📂 Splitting train/test ({}%)...".format(int(TRAIN_RATIO * 100)))
    train_dir = os.path.join(SAVE_DIR, "train")
    test_dir = os.path.join(SAVE_DIR, "test")
    ensure_dir(train_dir)
    ensure_dir(test_dir)

    for color in COLORS:
        color_tmp = os.path.join(tmp_dir, color)
        if not os.path.isdir(color_tmp):
            continue
        files = [f for f in os.listdir(color_tmp) if f.endswith(".jpg")]
        random.shuffle(files)
        n_train = int(len(files) * TRAIN_RATIO)

        train_color_dir = os.path.join(train_dir, color)
        test_color_dir = os.path.join(test_dir, color)
        ensure_dir(train_color_dir)
        ensure_dir(test_color_dir)

        for i, f in enumerate(files):
            src = os.path.join(color_tmp, f)
            if i < n_train:
                dst = os.path.join(train_color_dir, f)
            else:
                dst = os.path.join(test_color_dir, f)

            # ✅ skip move ถ้าไฟล์นั้นอยู่แล้ว
            if not os.path.exists(dst):
                shutil.copy2(src, dst)

        print("📸 {} → train: {} | test: {}".format(color, n_train, len(files) - n_train))

    # ===== Save metadata =====
    meta_path = os.path.join(SAVE_DIR, "dataset_info.json")
    with open(meta_path, "w") as f:
        json.dump(all_records, f, indent=2)

    print("\n✅ Dataset ready at: {}".format(SAVE_DIR))
    print("📊 Metadata saved as dataset_info.json")
    print("🧠 Skip enabled: Existing files were kept!")

# ===== Run =====
if __name__ == "__main__":
    build_dataset()
