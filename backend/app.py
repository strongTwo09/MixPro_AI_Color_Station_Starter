# -*- coding: utf-8 -*-
import os, io, time, json, math, sqlite3
from datetime import datetime
from uuid import uuid4

from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from flask import Flask, render_template
from PIL import Image
import numpy as np
import cv2

# Lazy imports for heavy libs
try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
except Exception as e:
    tf = None

try:
    from ultralytics import YOLO
except Exception as e:
    YOLO = None

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(APP_DIR)
UPLOAD_DIR = os.path.join(APP_DIR, "static", "uploads")
DB_PATH = os.path.join(ROOT_DIR, "database", "formulas.db")
MODEL_DIR = os.path.join(APP_DIR, "models")
CLF_PATH = os.path.join(MODEL_DIR, "color_classifier.h5")
YOLO_PATH = os.path.join(MODEL_DIR, "yolov8n.pt")  # user can replace

# ===== Load class mapping (from training) =====
CLASS_MAP = None
CLASS_MAP_PATH = os.path.join(MODEL_DIR, "class_indices.json")

def load_class_map():
    """โหลด mapping class → index จากไฟล์เทรน เพื่อให้โมเดลทำนายชื่อสีได้ตรง"""
    global CLASS_MAP
    if os.path.exists(CLASS_MAP_PATH):
        with open(CLASS_MAP_PATH, "r") as f:
            CLASS_MAP = json.load(f)
    else:
        CLASS_MAP = None

load_class_map()

# ถ้ามี mapping จากไฟล์ ให้แปลงเป็นลิสต์ตาม index
if CLASS_MAP:
    inv = [None] * len(CLASS_MAP)
    for k, v in CLASS_MAP.items():
        inv[v] = k
    COLOR_LABELS = inv
else:
    COLOR_LABELS = ["Black", "Blue", "Gray", "Red", "Silver", "White"]


os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates") #ยืนยันว่า Flask มองเห็นโฟลเดอร์ templates
CORS(app)

# ------------ Utilities --------------
#COLOR_LABELS = ["Black","Blue","Gray","Red","Silver","White"]

def allowed_file(fn):
    return "." in fn and fn.rsplit(".",1)[1].lower() in ["jpg","jpeg","png","webp"]

def save_upload(file_storage):
    ext = file_storage.filename.rsplit(".",1)[1].lower()
    name = "{}_{}.{}".format(datetime.now().strftime("%Y%m%d_%H%M%S"), uuid4().hex[:6], ext)
    path = os.path.join(UPLOAD_DIR, name)
    file_storage.save(path)
    return name, path

def load_image_rgb(path, max_size=1024):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    scale = min(1.0, float(max_size)/max(w,h))
    if scale < 1.0:
        img = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    return np.array(img)

def detect_car_boxes(img_rgb):
    """Return car bounding boxes using YOLO if available, else empty list"""
    if YOLO is None:
        return []
    model = YOLO(YOLO_PATH)  # will download if not present
    res = model.predict(img_rgb, verbose=False)[0]
    boxes = []
    for b in res.boxes:
        cls = int(b.cls.item())
        # COCO class 2 = car, 3 = motorcycle, 5 = bus, 7 = truck
        if cls in [2,3,5,7]:
            x1,y1,x2,y2 = map(int, b.xyxy[0].tolist())
            conf = float(b.conf.item())
            boxes.append((x1,y1,x2,y2,cls,conf))
    return boxes

def crop_to_main_car(img_rgb, boxes):
    if not boxes:
        return None, None
    # pick the largest box by area
    H,W,_ = img_rgb.shape
    boxes_sorted = sorted(boxes, key=lambda b:(b[2]-b[0])*(b[3]-b[1]), reverse=True)
    x1,y1,x2,y2,cls,conf = boxes_sorted[0]
    crop = img_rgb[max(0,y1):min(H,y2), max(0,x1):min(W,x2)]
    # heuristic: if box occupies > 25% of image area => likely full car
    full_ratio = ((x2-x1)*(y2-y1)) / float(W*H + 1e-9)
    is_full = full_ratio >= 0.25
    return crop, is_full

def color_histogram_dominant(img_rgb, k=3):
    # simple k-means to get dominant color
    data = img_rgb.reshape(-1,3).astype(np.float32)
    # random sample for speed
    if data.shape[0] > 50000:
        idx = np.random.choice(data.shape[0], 50000, replace=False)
        data = data[idx]
    # kmeans
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(data, k, None, criteria, 2, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.flatten())
    dom = centers[np.argmax(counts)].astype(int).tolist()
    return dom  # [R,G,B]

def refine_color_region(img_rgb):
    """
    กรองส่วนที่เป็นแสงสะท้อน/สว่างเกินออก
    เพื่อให้เหลือเฉพาะบริเวณที่เป็นสีแท้ของตัวถังรถ
    """
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    h, s, v = cv2.split(hsv)
    
    # mask เฉพาะส่วนที่มีความอิ่มสีสูง (saturation) และไม่สว่างเกิน
    mask = (v < 240) & (s > 40)
    
    filtered = img_rgb.copy()
    filtered[~mask] = [255, 255, 255]  # เปลี่ยนส่วนสะท้อนให้ขาว (ไม่ให้มีผล)
    return filtered


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % (rgb[0], rgb[1], rgb[2])


def load_class_map():
    """โหลด mapping class → index จากไฟล์เทรน เพื่อให้โมเดลทำนายชื่อสีได้ตรง"""
    global CLASS_MAP
    if os.path.exists(CLASS_MAP_PATH):
        with open(CLASS_MAP_PATH, "r") as f:
            CLASS_MAP = json.load(f)
    else:
        CLASS_MAP = None


def auto_white_balance(img):
    """ปรับ white balance ด้วย Gray World Algorithm"""
    result = img.copy().astype(np.float32)
    mean_r = np.mean(result[:,:,0])
    mean_g = np.mean(result[:,:,1])
    mean_b = np.mean(result[:,:,2])
    mean_gray = (mean_r + mean_g + mean_b) / 3
    result[:,:,0] = np.clip(result[:,:,0] * (mean_gray / mean_r), 0, 255)
    result[:,:,1] = np.clip(result[:,:,1] * (mean_gray / mean_g), 0, 255)
    result[:,:,2] = np.clip(result[:,:,2] * (mean_gray / mean_b), 0, 255)
    return result.astype(np.uint8)



clf_model = load_classifier()

def load_classifier():
    """โหลดโมเดลจำแนกสี (TensorFlow)"""
    if tf is None:
        print("⚠️ TensorFlow not available, skipping classifier load.")
        return None
    if not os.path.exists(CLF_PATH):
        print(f"⚠️ Model file not found: {CLF_PATH}")
        return None
    try:
        model = tf.keras.models.load_model(CLF_PATH, compile=False)
        print("✅ Loaded color classifier model successfully.")
        return model
    except Exception as e:
        print("❌ Error loading classifier:", e)
        return None

def predict_color_label(img_rgb):
    """
    คืนค่า (label, confidence 0..1)
    - ถ้ามีโมเดล: ใช้ softmax ที่โมเดลทำนาย
    - ถ้าไม่มี: ใช้ heuristic + ตั้ง confidence แบบคร่าว ๆ
    """
    if YOLO is not None:
        boxes = detect_car_boxes(img_rgb)
    crop, _ = crop_to_main_car(img_rgb, boxes)
    if crop is not None:
        img_rgb = crop


    if clf_model is None or tf is None:
        # fallback: dominant color heuristic
        rgb = color_histogram_dominant(img_rgb, k=3)
        r,g,b = rgb
        if max(rgb) < 60: 
            return "Black", 0.9
        if abs(r-g)<20 and abs(g-b)<20 and max(rgb)>200: 
            return "White", 0.9
        if b>r and b>g: 
            return "Blue", 0.7
        if r>g and r>b: 
            return "Red", 0.7
        if abs(r-g)<20 and b<120: 
            return "Gray", 0.6
        return "Silver", 0.6

    # มีโมเดล → resize + predict
    im = cv2.resize(img_rgb, (224,224))
    im = im.astype("float32")/255.0
    im = np.expand_dims(im,0)
    pred = clf_model.predict(im, verbose=0)[0]
    idx = int(np.argmax(pred))
    conf = float(pred[idx])
    # ถ้า CLASSES ของโมเดลคุณต่างจาก COLOR_LABELS ให้ปรับตรงนี้ให้ตรงกัน
    label = COLOR_LABELS[idx] if idx < len(COLOR_LABELS) else "Unknown"
    return label, conf


# ---------- Database (Color Formula) helpers ----------
def db_conn():
    return sqlite3.connect(DB_PATH)

def ensure_db():
    con = db_conn(); cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS color_formulas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT,
        color_name TEXT,
        hex TEXT,
        r INTEGER, g INTEGER, b INTEGER,
        base_red REAL, base_blue REAL, base_yellow REAL, base_white REAL, base_black REAL,
        UNIQUE(brand, color_name, hex) ON CONFLICT IGNORE
    )""")
    con.commit(); con.close()

ensure_db()

def query_best_match(hex_value):
    """Nearest color in DB by Euclidean RGB distance."""
    con = db_conn(); cur = con.cursor()
    cur.execute("SELECT id, brand, color_name, hex, r, g, b, base_red, base_blue, base_yellow, base_white, base_black FROM color_formulas")
    rows = cur.fetchall(); con.close()
    if not rows:
        return None
    import math
    # parse target
    hex_value = hex_value.lstrip("#")
    tr = int(hex_value[0:2],16); tg=int(hex_value[2:4],16); tb=int(hex_value[4:6],16)
    best = None; bestd=1e9
    for row in rows:
        _, brand, cname, hx, r,g,b, br,bb,by,bw,bk = row
        d = math.sqrt((tr-r)**2 + (tg-g)**2 + (tb-b)**2)
        if d < bestd:
            bestd = d
            best = dict(brand=brand, color_name=cname, hex=hx,
                        r=r,g=g,b=b,
                        base_red=br, base_blue=bb, base_yellow=by, base_white=bw, base_black=bk,
                        delta_rgb=round(bestd,2))
    return best

# ------------- Routes -----------------
@app.route("/")
def home():
    # ✅ default เปิดหน้าเว็บหลัก app.html
    return render_template("app.html")


@app.route("/api/upload", methods=["POST"])
def api_upload():
    f = request.files.get("file")
    if not f or not allowed_file(f.filename):
        return jsonify({"ok":False, "error":"no file"}), 400
    name, path = save_upload(f)
    img = load_image_rgb(path)           # ✅ โหลดภาพก่อนใช้
    img = auto_white_balance(img)        # ✅ ใช้ฟังก์ชัน WB ได้แล้ว
    # detect car
    boxes = detect_car_boxes(img) if YOLO is not None else []
    crop, is_full = crop_to_main_car(img, boxes) if boxes else (None, False)

    result = {
        "ok": True,
        "file": name,
        "url": f"/static/uploads/{name}",
        "analysis": {}
    }

    if crop is not None:
        # 🔧 ปรับภาพให้สะอาดก่อนวิเคราะห์
        refined_crop = refine_color_region(crop)
    
    # 🔍 วิเคราะห์สีจากภาพที่กรองแล้ว
        label, conf = predict_color_label(refined_crop)

    # คำนวณสีเฉลี่ย
        dom = color_histogram_dominant(refined_crop, k=3)
        hexv = rgb_to_hex(dom)

        # full-car branch: (placeholders for make/model/year; can extend later)
        result["analysis"]["type"] = "full_car" if is_full else "partial"
        result["analysis"]["dominant_hex"] = hexv
        result["analysis"]["color_label"] = label
        result["analysis"]["confidence"] = conf
    else:
        # no car detected: return dominant color of entire image

        refined_img = refine_color_region(img)
        dom = color_histogram_dominant(refined_img, k=3)
        hexv = rgb_to_hex(dom)
        label, conf = predict_color_label(refined_img)
        result["analysis"]["type"] = "partial"
        result["analysis"]["dominant_hex"] = hexv
        result["analysis"]["color_label"] = label
        result["analysis"]["confidence"] = conf

    # match formula
    best = query_best_match(result["analysis"].get("dominant_hex","#808080"))
    result["formula_match"] = best
    return jsonify(result)

@app.route("/api/formulas", methods=["GET","POST"])
def formulas():
    if request.method == "POST":
        data = request.json or {}
        need = ["brand","color_name","hex","base_red","base_blue","base_yellow","base_white","base_black"]
        if not all(k in data for k in need):
            return jsonify({"ok":False,"error":"missing fields"}), 400
        hx = data["hex"].lstrip("#")
        r,g,b = int(hx[0:2],16), int(hx[2:4],16), int(hx[4:6],16)
        con = db_conn(); cur=con.cursor()
        cur.execute("""INSERT OR IGNORE INTO color_formulas(brand,color_name,hex,r,g,b,base_red,base_blue,base_yellow,base_white,base_black)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (data["brand"], data["color_name"], "#"+hx, r,g,b,
                     float(data["base_red"]), float(data["base_blue"]), float(data["base_yellow"]), float(data["base_white"]), float(data["base_black"])
                    ))
        con.commit(); con.close()
        return jsonify({"ok":True})
    else:
        # list
        con = db_conn(); cur = con.cursor()
        cur.execute("SELECT brand, color_name, hex, base_red, base_blue, base_yellow, base_white, base_black FROM color_formulas ORDER BY brand, color_name")
        rows = cur.fetchall(); con.close()
        items = [dict(brand=r[0], color_name=r[1], hex=r[2], base_red=r[3], base_blue=r[4], base_yellow=r[5], base_white=r[6], base_black=r[7]) for r in rows]
        return jsonify({"ok":True, "items":items})

@app.route("/api/mix", methods=["POST"])
def api_mix():
    """Forward mix command to ESP32 HTTP endpoint if provided."""
    data = request.json or {}
    target = os.environ.get("ESP32_URL", "").strip()
    if not target:
        # simulate success
        return jsonify({"ok":True, "message":"Simulated mix (set ESP32_URL env to enable real device).", "payload": data})
    import requests
    try:
        r = requests.post(target.rstrip("/") + "/mix", json=data, timeout=5)
        return jsonify({"ok":True, "esp32_status": r.json()})
    except Exception as e:
        return jsonify({"ok":False, "error": str(e)})

# --------------- Frontend ---------------
@app.route("/app")
def app_page():
    return render_template("app.html")

@app.route("/demo")
def demo_page():
    return render_template("demo.html")

#----ส่ง “สีเฉลี่ยของกรอบที่ผู้ใช้เลือก” ให้ backend แมตช์สูตร
@app.route("/api/analyze_hex", methods=["POST"])
def analyze_hex():
      #  """รับค่าสี (hex) จาก ROI ในหน้าเว็บ แล้วหา formula ใก ล้สุด + label/ความมั่นใจแบบ heuristic"""
    data = request.get_json(silent=True) or {}
    hx = (data.get("hex") or "#808080").strip()

    # map hex -> label แบบง่าย (HSV/threshold)
    def hex_to_label(hexv):
        h = hexv.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        mx, mn = max(r,g,b), min(r,g,b)
        v = mx/255.0
        s = 0 if mx==0 else (mx-mn)/float(mx)
        # เบสิค rule
        if v < 0.2: return "Black", 0.95
        if s < 0.08 and v > 0.85: return "White", 0.9
        if s < 0.15 and 0.5 < v < 0.9: return "Silver", 0.7
        if r > g and r > b: return "Red", 0.7
        if b > r and b > g: return "Blue", 0.7
        if g > r and g > b: return "Green", 0.6
        return "Gray", 0.6

    label, conf = hex_to_label(hx)

    # หา formula ใกล้สุด
    best = query_best_match(hx)  # ใช้ฟังก์ชันเดิม
    return jsonify({
        "ok": True,
        "analysis": {
            "type": "roi",
            "dominant_hex": hx,
            "color_label": label,
            "confidence": conf
        },
        "formula_match": best
    })


if __name__ == "__main__":
    # Ensure a tiny sample DB exists
    from pathlib import Path
    if not Path(DB_PATH).exists():
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS color_formulas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT, color_name TEXT, hex TEXT, r INTEGER, g INTEGER, b INTEGER,
            base_red REAL, base_blue REAL, base_yellow REAL, base_white REAL, base_black REAL,
            UNIQUE(brand, color_name, hex) ON CONFLICT IGNORE
        )""")
        # seed few sample formulas (dummy)
        samples = [
            ("Toyota","Super White","#ffffff",255,255,255, 0,0,0,90,10),
            ("Toyota","Attitude Black","#000000",0,0,0, 0,0,0,0,100),
            ("Mazda","Soul Red","#b71c1c",183,28,28, 55,10,5,20,10),
            ("Ford","Performance Blue","#1565c0",21,101,192, 10,60,5,20,5),
            ("Nissan","Brilliant Silver","#c0c0c0",192,192,192, 0,0,0,70,30),
        ]
        cur.executemany("""INSERT INTO color_formulas
           (brand,color_name,hex,r,g,b,base_red,base_blue,base_yellow,base_white,base_black)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""", samples)
        con.commit(); con.close()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
    
    
    
    

