"""
main.py - Python Core Script [S].

Crowd Control Monitoring System: counts people with YOLOv8, checks the crowd
limit (FR-02), drives the ESP32 Actuator (INT-01) and logs to Neon (INT-02).

Run:   python main.py
Keys:  q = quit,  + / - = raise or lower the crowd limit
"""

import time

import cv2

import config
from db_logger import DBLogger
from esp32_link import ESP32Link
from hud import draw_hud
from vision import Camera, PersonCounter

WINDOW_NAME = "Crowd Control Monitoring System"


def main():
    camera = Camera()
    counter = PersonCounter()
    esp32 = ESP32Link()
    db = DBLogger()

    limit = config.CROWD_LIMIT
    crowded = False
    esp32.send_state(crowded)       # start the ESP32 in the NORMAL state
    fps, last_time = 0.0, time.time()

    print("Running. Press 'q' to quit, '+' / '-' to change the limit.")
    try:
        while True:
            frame = camera.read()
            if frame is None:
                print("Warning: could not read a frame from the camera.")
                time.sleep(0.1)
                continue

            # 1) Count people (YOLOv8 Engine)
            people, count = counter.detect(frame)

            # 2) Threshold rule (FR-02: alert when count > limit)
            now_crowded = count > limit
            if now_crowded != crowded:
                crowded = now_crowded
                print(f"[{time.strftime('%H:%M:%S')}] State -> "
                      f"{'CROWDED' if crowded else 'NORMAL'} (count {count}, limit {limit})")
            esp32.send_state(crowded)                 # INT-01 (non-blocking)
            db.update(count, limit, crowded)          # INT-02 (non-blocking)

            # 3) FPS + heads-up display
            now = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(now - last_time, 1e-6))
            last_time = now
            draw_hud(frame, people, count, limit, crowded, fps, esp32.status, db.status)
            cv2.imshow(WINDOW_NAME, frame)

            # 4) Keyboard controls
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key in (ord("+"), ord("=")):
                limit += 1
                print(f"Limit set to {limit}")
            elif key == ord("-") and limit > 0:
                limit -= 1
                print(f"Limit set to {limit}")
    finally:
        camera.release()
        esp32.close()
        db.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()