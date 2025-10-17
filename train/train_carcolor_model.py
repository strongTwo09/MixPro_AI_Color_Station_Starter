# -*- coding: utf-8 -*-
"""
Train Car Color Classifier (EfficientNet / MobileNet)
------------------------------------------------------
ใช้ dataset จาก ./dataset/train / test
บันทึก model -> backend/models/model_carcolor.h5
บันทึก log -> train/logs/train_log.txt
"""

import os
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models
from tensorflow.keras.applications import EfficientNetV2S, MobileNetV3Large
from tensorflow.keras.callbacks import ModelCheckpoint, CSVLogger
from datetime import datetime

# ===== CONFIG =====
DATA_DIR = os.path.join(os.path.dirname(__file__), "../dataset")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "../backend/models")
LOG_DIR = os.path.join(os.path.dirname(__file__), "./logs")
IMG_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 15
USE_MODEL = "efficientnet"  # "mobilenet" or "efficientnet"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ===== DATASET =====
train_dir = os.path.join(DATA_DIR, "train")
test_dir = os.path.join(DATA_DIR, "test")

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
print(f"✅ Classes detected: {list(train_gen.class_indices.keys())}")

# ===== MODEL =====
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

base_model.trainable = False  # Freeze base

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

model.summary()

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

# ===== UNFREEZE + Fine-tune =====
print("🔧 Fine-tuning base layers...")
base_model.trainable = True
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)
fine_tune_epochs = 5
model.fit(
    train_gen,
    epochs=fine_tune_epochs,
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
    f.write("Final Accuracy: {:.4f}\n".format(history.history["accuracy"][-1]))
    f.write("Validation Accuracy: {:.4f}\n".format(history.history["val_accuracy"][-1]))
    f.write("="*40 + "\n")

print(f"✅ Model saved at {model_path}")
print(f"📘 Logs saved at {log_path}")
