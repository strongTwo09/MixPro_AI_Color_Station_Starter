# -*- coding: utf-8 -*-
import sqlite3, json, os

DB_PATH = os.path.join("..", "database", "formulas.db")

def ensure_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS color_formulas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT,
        color_name TEXT,
        hex TEXT,
        r INTEGER, g INTEGER, b INTEGER,
        base_red REAL, base_blue REAL, base_yellow REAL, base_white REAL, base_black REAL,
        UNIQUE(brand, color_name, hex) ON CONFLICT IGNORE
    )
    """)
    con.commit(); con.close()

def insert_data():
    with open("car_colors.json","r",encoding="utf-8") as f:
        data = json.load(f)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    for row in data:
        hx = row.get("hex") or "#808080"
        hx = hx.lstrip("#")
        r,g,b = int(hx[0:2],16), int(hx[2:4],16), int(hx[4:6],16)
        cur.execute("""INSERT OR IGNORE INTO color_formulas
            (brand,color_name,hex,r,g,b,base_red,base_blue,base_yellow,base_white,base_black)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (row["make"], row["color_name"], "#"+hx, r,g,b, 0,0,0,0,0)
        )
    con.commit(); con.close()
    print("✅ Seeded database with", len(data), "rows")

if __name__=="__main__":
    ensure_db()
    insert_data()
