# -*- coding: utf-8 -*-
"""
Use YOLOv8n to crop vehicles from images in raw/ into dataset/train & dataset/val by color folders (if labeled).

This is optional helper; if you already have cropped cars, skip this.
"""
import os, glob, shutil
from ultralytics import YOLO
from PIL import Image

RAW_DIR = "raw"
OUT_DIR = "dataset"
model = YOLO("yolov8n.pt")

os.makedirs(OUT_DIR, exist_ok=True)

for split in ["train", "val"]:
    split_dir = os.path.join(RAW_DIR, split)
    if not os.path.exists(split_dir): continue
    for color in os.listdir(split_dir):
        src_dir = os.path.join(split_dir, color)
        if not os.path.isdir(src_dir): continue
        out_dir = os.path.join(OUT_DIR, split, color)
        os.makedirs(out_dir, exist_ok=True)
        for fp in glob.glob(os.path.join(src_dir,"*.*")):
            img = Image.open(fp).convert("RGB")
            res = model.predict(img, verbose=False)[0]
            boxes = res.boxes.xyxy.cpu().numpy() if res.boxes is not None else []
            if len(boxes)==0: continue
            # take largest box
            x1,y1,x2,y2 = map(int, boxes[0])
            crop = img.crop((x1,y1,x2,y2))
            base = os.path.splitext(os.path.basename(fp))[0]
            crop.save(os.path.join(out_dir, base + "_crop.jpg"), quality=92)
print("Cropping done")
