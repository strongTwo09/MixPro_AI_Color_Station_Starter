# MixPro AI Color Station (Starter)

ฟูลสแตกเดโมสำหรับ:
- ✅ Flask Backend (อัปโหลดภาพ → วิเคราะห์ YOLO + จำแนกสี → จับคู่สูตรสีจากฐานข้อมูล)
- ✅ UI หน้าเว็บ 3 โหมด (กล้อง/ไฟล์/กล้องภายนอก ESP32)
- ✅ สคริปต์รวบรวมข้อมูลสีจาก paintref.com + สร้างฐานข้อมูลสูตรสี (SQLite)
- ✅ เทรนโมเดลจำแนกสีรถ (MobileNetV3 / EfficientNetV2-S)
- ✅ โค้ด ESP32 รับคำสั่งผสมสีผ่าน HTTP

## โครงสร้างโฟลเดอร์
```
backend/            # Flask app
  app.py
  requirements.txt
  templates/
    index.html
    app.html
  static/
    css/style.css
    js/app.js
    uploads/
database/
  formulas.db       # ฐานข้อมูลตัวอย่าง (seed)
scripts/
  scrape_paintref.py
  build_formulas_db.py
  train_color_classifier.py
  yolo_crop.py
esp32/
  esp32_mixer.ino
frontend/
  index.html        # static info
```

## วิธีรัน (Backend)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
# เปิด http://localhost:5000
```

> **หมายเหตุ**: ถ้าติดตั้ง TensorFlow/ultralytics ไม่ได้ ให้คอมเมนต์ส่วนที่เกี่ยวข้องชั่วคราว ระบบยังวิเคราะห์สีแบบ heuristic ได้

## การใช้งาน UI
- หน้าแรก `/` มี 3 เมนู → เข้าหน้า `/app`
- โหมดกล้อง: เปิดสิทธิ์กล้อง → ถ่าย → ยืนยัน เพื่อส่งขึ้นเซิร์ฟเวอร์วิเคราะห์
- โหมดไฟล์: เลือกไฟล์ → แสดงพรีวิว → กดยืนยันอัปโหลด
- โหมดกล้องภายนอก: ใส่ URL สแนปช็อต (ESP32-CAM) แล้วกดดึงภาพ

## เติมฐานข้อมูลสูตรสีจาก paintref
1) รันสคริปต์เก็บข้อมูล (ต้องมีอินเทอร์เน็ต)
```bash
python scripts/scrape_paintref.py
```
จะได้ `paintref_colors.json`

2) สร้าง `database/formulas.db`
```bash
python scripts/build_formulas_db.py
```

## เทรนโมเดลจำแนกสี
เตรียมโฟลเดอร์ `dataset/train` และ `dataset/val` โดยมีคลาสย่อย 6 สี: Black, Blue, Gray, Red, Silver, White

```bash
python scripts/train_color_classifier.py dataset backend/models/color_classifier.h5
```
ตั้งค่าสิ่งแวดล้อมเพื่อเปลี่ยน backbone:
```bash
BACKBONE=effv2s python scripts/train_color_classifier.py
```

## ใช้ YOLO ครอปรถก่อนเทรน (ทางเลือก)
วางรูปดิบใน `raw/train/<Color>/` และ `raw/val/<Color>/` แล้วรัน:
```bash
python scripts/yolo_crop.py
```

## เชื่อมต่อ ESP32
1) อัปโหลด `esp32/esp32_mixer.ino` → ใส่ SSID/PASS → ดู IP ใน Serial Monitor
2) ตั้งค่าตัวแปรแวดล้อมก่อนรัน Flask:
```bash
export ESP32_URL=http://<esp32-ip>
python backend/app.py
```
ตอนกด “ยืนยันสูตรและสั่งผสม” ในหน้า `/app` ระบบจะส่ง JSON ไปที่ `ESP32_URL/mix`

## ขยายผล (ทำ Make/Model/Year)
- ปัจจุบันฝั่ง backend ใส่ค่า `TBD` ไว้เป็นที่ว่าง
- แนวทางเพิ่ม:
  - ใช้โมเดล vehicle make-model (เช่น CompCars, BoxCars) หรือบริการ API ภายนอก
  - เฉพาะไทย: ฝึกโมเดลเองจาก dataset ที่ถ่ายเก็บ

## Disclaimer
- แบบจำลองผสมสีในฐานข้อมูลนี้เป็นการประมาณจาก RGB เบื้องต้น ใช้เพื่อเดโม/สาธิต workflow เท่านั้น
- งานจริงควรใช้สเปกโตรโฟโตมิเตอร์และโมเดลเชิงแสง (Kubelka–Munk)
