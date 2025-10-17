# -*- coding: utf-8 -*-
"""
Import JSON (car_colors.json) -> SQLite formulas.db
---------------------------------------------------
จะอ่าน car_colors.json ที่ scrape มา
แล้ว import เข้า database/formulas.db

วิธีใช้:
    python scrapers/import_colors_to_db.py
"""

import os, json, sqlite3
import random

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(ROOT_DIR, "database", "formulas.db")
JSON_PATH = os.path.join(os.path.dirname(__file__), "car_colors.json")

def ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS color_formulas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT,
        color_name TEXT,
        hex TEXT,
        r INTEGER, g INTEGER, b INTEGER,
        base_red REAL, base_blue REAL, base_yellow REAL, base_white REAL, base_black REAL,
        UNIQUE(brand, color_name, hex) ON CONFLICT IGNORE
    )""")
    con.commit()
    con.close()

def hex_to_rgb(hexv: str):
    hexv = hexv.lstrip("#")
    return tuple(int(hexv[i:i+2], 16) for i in (0, 2, 4))

def random_formula(rgb):
    """สร้างสูตรผสมแบบสุ่ม (demo)"""
    total = 100.0
    br = random.uniform(0, total*0.4)
    bb = random.uniform(0, total*0.4)
    by = random.uniform(0, total*0.4)
    bw = random.uniform(0, total*0.4)
    bk = max(0, total - (br+bb+by+bw))
    s = br+bb+by+bw+bk
    return br/s*100, bb/s*100, by/s*100, bw/s*100, bk/s*100

def import_colors():
    if not os.path.exists(JSON_PATH):
        print(f"❌ ไม่พบไฟล์ {JSON_PATH}, กรุณา run paintref_scraper.py ก่อน")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    ensure_db()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    added = 0
    for item in data:
        brand = item.get("make","Unknown")
        cname = item.get("name","Unknown")
        hexv = item.get("hex","#808080")
        r,g,b = hex_to_rgb(hexv)
        br,bb,by,bw,bk = random_formula((r,g,b))
        cur.execute("""INSERT OR IGNORE INTO color_formulas
            (brand,color_name,hex,r,g,b,base_red,base_blue,base_yellow,base_white,base_black)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (brand, cname, hexv, r,g,b, br,bb,by,bw,bk))
        added += cur.rowcount

    con.commit()
    con.close()
    print(f"✅ Imported {added} new rows into {DB_PATH}")

if __name__ == "__main__":
    import_colors()
