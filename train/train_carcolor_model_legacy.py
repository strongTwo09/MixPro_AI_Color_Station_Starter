# -*- coding: utf-8 -*-
"""
Train Car Color Classifier (Legacy Compatible)
----------------------------------------------
รองรับ Python 2.7 / 3.x
ใช้ EfficientNetV2S หรือ MobileNetV3Large
บันทึกผลลง backend/models/model_carcolor.h5
และ logs/train_log.txt
"""

import os
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import ModelCheckpoint, CSVLogger
from datetime import datetime
from tensorflow.keras.optimizers import Adam

# ===== CONFIG =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../dataset")
MODEL_DIR = os.path.join(BASE_DIR, "../backend/models")
LOG_DIR = os.path.join(BASE_DIR, "./logs")

IMG_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 15
USE_MODEL = "mobilenet"   # "mobilenet" หรือ "efficientnet"

# ===== Prepare directories =====
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

train_dir = os.path.join(DATA_DIR, "train")
test_dir = os.path.join(DATA_DIR, "test")

# ===== DATASET =====
train_datagen = ImageDataGenerator(
    rescale=1.0/255,
    rotation_range=10,
    width_shift_range=0.1,
    height_shift_range=0.1,
    shear_range=0.1,
    zoom_range=0.1,
    horizontal_flip=True
)
test_datagen = ImageDataGenerator(rescale=1.0/255)

train_gen = train_datagen.flow_from_directory(
    train_dir,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical"
)
test_gen = test_datagen.flow_from_directory(
    test_dir,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical"
)

NUM_CLASSES = len(train_gen.class_indices)
print("✅ Classes detected: {}".format(list(train_gen.class_indices.keys())))

# ===== MODEL SELECTION =====
from tensorflow.keras.applications import EfficientNetV2S, MobileNetV3Large

if USE_MODEL == "efficientnet":
    base_model = EfficientNetV2S(
        include_top=False,
        weights="imagenet",
        input_shape=IMG_SIZE + (3,)
    )
else:
    base_model = MobileNetV3Large(
        include_top=False,
        weights="imagenet",
        input_shape=IMG_SIZE + (3,)
    )

base_model.trainable = False

model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dropout(0.3),
    layers.Dense(NUM_CLASSES, activation="softmax")
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)


# ===== CALLBACKS =====
model_path = os.path.join(MODEL_DIR, "model_carcolor.h5")
log_path = os.path.join(LOG_DIR, "train_log.txt")
csv_logger = CSVLogger(os.path.join(LOG_DIR, "train_history.csv"))

checkpoint = ModelCheckpoint(
    model_path,
    monitor="val_accuracy",
    save_best_only=True,
    mode="max",
    verbose=1
)

# ===== TRAIN =====
print("🚀 Starting training...")
history = model.fit(
    train_gen,
    epochs=EPOCHS,
    validation_data=test_gen,
    callbacks=[checkpoint, csv_logger],
    verbose=1
)

# ===== DATASET =====
train_datagen = ImageDataGenerator(
    rescale=1.0/255,
    rotation_range=10,
    width_shift_range=0.1,
    height_shift_range=0.1,
    shear_range=0.1,
    zoom_range=0.1,
    horizontal_flip=True
)
test_datagen = ImageDataGenerator(rescale=1.0/255)

train_gen = train_datagen.flow_from_directory(
    train_dir,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical"
)
test_gen = test_datagen.flow_from_directory(
    test_dir,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical"
)

NUM_CLASSES = len(train_gen.class_indices)
print("✅ Classes detected: {}".format(list(train_gen.class_indices.keys())))

# ===== บันทึก mapping class → index =====
import json
class_map_path = os.path.join(MODEL_DIR, "class_indices.json")
with open(class_map_path, "w") as f:
    json.dump(train_gen.class_indices, f, indent=2)
print("🗂️ Saved class mapping to:", class_map_path)


# ===== FINE-TUNE =====
print("🔧 Fine-tuning base layers...")
base_model.trainable = True
model.compile(
    optimizer=Adam(learning_rate=1e-4),
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)
model.fit(
    train_gen,
    epochs=5,
    validation_data=test_gen,
    verbose=1
)

# ===== SAVE & LOG =====
model.save(model_path)

with open(log_path, "a") as f:
    f.write("==== Training completed ====\n")
    f.write("Date: {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    f.write("Model: {}\n".format(USE_MODEL))
    f.write("Classes: {}\n".format(", ".join(train_gen.class_indices.keys())))
    f.write("Train samples: {}\n".format(train_gen.samples))
    f.write("Test samples: {}\n".format(test_gen.samples))
    f.write("Final Acc: {:.4f}\n".format(history.history["accuracy"][-1]))
    f.write("Val Acc: {:.4f}\n".format(history.history["val_accuracy"][-1]))
    f.write("="*40 + "\n")

print("✅ Model saved at {}".format(model_path))
print("📘 Logs saved at {}".format(log_path))
