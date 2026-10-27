"""
vision.py - USB Webcam [E] + YOLOv8 Engine [S].

Opens the camera and counts people in each frame.
"""

import platform
from collections import deque
from statistics import median

import cv2
from ultralytics import YOLO

import config


class Camera:
    """Wraps the USB webcam."""

    def __init__(self, index: int = config.CAMERA_INDEX):
        # On Windows, the DirectShow backend opens USB webcams much faster
        backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
        self.cap = cv2.VideoCapture(index, backend)
        if not self.cap.isOpened():
            raise SystemExit(f"Could not open camera {index}. Try another CAMERA_INDEX in config.py.")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    def read(self):
        """Return a frame, or None if the camera did not deliver one."""
        ok, frame = self.cap.read()
        return frame if ok else None

    def release(self):
        self.cap.release()


class PersonCounter:
    """Runs YOLOv8 locked to the 'person' class and smooths the count."""

    def __init__(self):
        print("Loading YOLOv8 model (first run downloads it)...")
        self.model = YOLO(config.MODEL_FILE)
        self.recent_counts = deque(maxlen=config.SMOOTHING_FRAMES)

    def detect(self, frame):
        """Return (people, smoothed_count). people = list of (x1, y1, x2, y2, confidence)."""
        result = self.model(frame, classes=[config.PERSON_CLASS_ID],
                            conf=config.CONFIDENCE, verbose=False)[0]
        people = [
            (*map(int, box), conf)
            for box, conf in zip(result.boxes.xyxy.tolist(), result.boxes.conf.tolist())
        ]
        self.recent_counts.append(len(people))
        return people, int(median(self.recent_counts))