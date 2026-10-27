"""
config.py - all settings in one place.

Secrets (the Neon database URL) are read from the .env file, never written here.
"""

import os

from dotenv import load_dotenv

load_dotenv()  # reads .env in the project folder, if it exists

# ---------------- Camera / vision (YOLOv8 Engine) ----------------
CAMERA_INDEX = 0            # 0 = default webcam; try 1 or 2 for an external USB webcam
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
MODEL_FILE = "yolov8n.pt"   # 'n' = nano, fastest; downloads automatically on first run
CONFIDENCE = 0.40           # ignore detections below 40% confidence
SMOOTHING_FRAMES = 5        # median of the last N counts to stop flickering
PERSON_CLASS_ID = 0         # COCO class 0 = "person"

# ---------------- Threshold rule (FR-02) ----------------
CROWD_LIMIT = 10            # alert when count is GREATER than this

# ---------------- ESP32 link (INT-01) ----------------
# "serial" = USB cable (step 4), "wifi" = over the network (step 5), "off" = no hardware
ESP32_MODE = os.getenv("ESP32_MODE", "serial")
SERIAL_PORT = os.getenv("SERIAL_PORT", "COM3")      # Windows: COM3, COM4...  Mac: /dev/cu.usbserial-XXXX
SERIAL_BAUD = 115200                                # must match the ESP32 sketch
ESP32_HOST = os.getenv("ESP32_HOST", "192.168.1.50")  # ESP32 IP address (shown in its Serial Monitor)
ESP32_PORT = 80
ESP32_TIMEOUT_S = 0.5       # give up on one send after this long
RESEND_EVERY_S = 2.0        # re-send the current state regularly so the ESP32 recovers after a reconnect
RECONNECT_EVERY_S = 3.0     # how often to retry when the ESP32 is unreachable

# ---------------- Database logging (INT-02) ----------------
DATABASE_URL = os.getenv("DATABASE_URL", "")  # Neon connection string, from .env
LOG_INTERVAL_S = 10         # insert one row every 10 seconds
MAX_BUFFERED_ROWS = 360     # keep up to 1 hour of rows in memory if Neon is unreachable