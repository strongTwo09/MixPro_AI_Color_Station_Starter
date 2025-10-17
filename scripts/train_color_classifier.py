# -*- coding: utf-8 -*-
"""
Train a simple color classifier using MobileNetV3 or EfficientNetV2 on cropped car images.

Dataset should be arranged as:
dataset/
  train/
    Black/...
    Blue/...
    Gray/...
    Red/...
    Silver/...
    White/...
  val/
    Black/...
    ...

Optionally run `yolo_crop.py` first to crop vehicles from raw images.
"""
import os, sys, json
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV3Large, EfficientNetV2S
from tensorflow.keras.applications.mobilenet_v3 import preprocess_input as mb_pre
from tensorflow.keras.applications.efficientnet_v2 import preprocess_input as ef_pre

DATA_DIR = sys.argv[1] if len(sys.argv)>1 else "dataset"
MODEL_OUT = sys.argv[2] if len(sys.argv)>2 else "backend/models/color_classifier.h5"
BACKBONE = os.environ.get("BACKBONE","mbv3")  # "mbv3" or "effv2s"
IMG = 224
BATCH = 16
EPOCHS = 5

autotune = tf.data.AUTOTUNE
train_ds = tf.keras.utils.image_dataset_from_directory(
    os.path.join(DATA_DIR,"train"), labels='inferred', label_mode='categorical',
    image_size=(IMG,IMG), batch_size=BATCH, shuffle=True
)
val_ds = tf.keras.utils.image_dataset_from_directory(
    os.path.join(DATA_DIR,"val"), labels='inferred', label_mode='categorical',
    image_size=(IMG,IMG), batch_size=BATCH, shuffle=False
)

class_names = train_ds.class_names
print("Classes:", class_names)

train_ds = train_ds.cache().shuffle(512).prefetch(autotune)
val_ds = val_ds.cache().prefetch(autotune)

if BACKBONE == "effv2s":
    base = EfficientNetV2S(weights="imagenet", include_top=False, input_shape=(IMG,IMG,3))
    pre = ef_pre
else:
    base = MobileNetV3Large(weights="imagenet", include_top=False, input_shape=(IMG,IMG,3))
    pre = mb_pre

base.trainable = False

inp = layers.Input(shape=(IMG,IMG,3))
x = layers.Lambda(pre)(inp)
x = base(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dropout(0.2)(x)
out = layers.Dense(len(class_names), activation="softmax")(x)
model = models.Model(inp, out)
model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS)
os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
model.save(MODEL_OUT)
print("Saved model to", MODEL_OUT)
