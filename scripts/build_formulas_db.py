# -*- coding: utf-8 -*-
"""
Build SQLite formulas.db from paintref_colors.json and approximate base ratios.
This uses a simple RGB fitting to Red/Blue/Yellow/White/Black bases.
"""
import json, os, sqlite3, math

BASES = {
    "Red":   (220, 40,  40),
    "Blue":  (40,  90, 200),
    "Yellow":(245, 210, 60),
    "White": (255, 255, 255),
    "Black": (0,   0,   0),
}

def rgb_to_linear(c):
    c = [v/255.0 for v in c]
    def f(x): return x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4
    return [f(v) for v in c]

def linear_to_rgb(c):
    def f(x): 
        return int(round(255*(12.92*x if x<=0.0031308 else 1.055*(x**(1/2.4))-0.055)))
    return [max(0,min(255,f(v))) for v in c]

def fit_weights(target_rgb):
    import numpy as np
    A = np.array([rgb_to_linear(BASES[k]) for k in ["Red","Blue","Yellow","White","Black"]]).T  # 3x5
    t = np.array(rgb_to_linear(target_rgb))  # 3
    # non-negative least squares with sum=1 constraint via projected gradient
    w = np.ones(5)/5.0
    alpha = 0.05
    for _ in range(800):
        y = A @ w
        grad = A.T @ (y - t)
        w = w - alpha*grad
        w[w<0]=0
        s = w.sum()
        if s==0: w[:] = 1/5.0
        else: w /= s
    return w

def ensure_db(db_path):
    con = sqlite3.connect(db_path); cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS color_formulas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT, color_name TEXT, hex TEXT,
        r INTEGER, g INTEGER, b INTEGER,
        base_red REAL, base_blue REAL, base_yellow REAL, base_white REAL, base_black REAL,
        UNIQUE(brand, color_name, hex) ON CONFLICT IGNORE
    )""")
    con.commit(); con.close()

def main():
    if not os.path.exists("paintref_colors.json"):
        print("Run scrape_paintref.py first."); return
    rows = json.load(open("paintref_colors.json","r",encoding="utf-8"))
    db_path = os.path.join("database","formulas.db")
    os.makedirs("database", exist_ok=True)
    ensure_db(db_path)
    con = sqlite3.connect(db_path); cur=con.cursor()
    for i, r in enumerate(rows):
        hx = r["hex"].lstrip("#")
        tr, tg, tb = int(hx[0:2],16), int(hx[2:4],16), int(hx[4:6],16)
        w = fit_weights((tr,tg,tb))
        base_red, base_blue, base_yellow, base_white, base_black = [float(f"{x*100:.2f}") for x in w]
        cur.execute("""INSERT OR IGNORE INTO color_formulas
            (brand, color_name, hex, r, g, b, base_red, base_blue, base_yellow, base_white, base_black)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (r["brand"].title(), r.get("name",""), r["hex"].upper(), tr, tg, tb,
             base_red, base_blue, base_yellow, base_white, base_black))
        if i and i % 200 == 0:
            con.commit(); print("Inserted", i)
    con.commit(); con.close()
    print("Built", db_path)

if __name__ == "__main__":
    main()
