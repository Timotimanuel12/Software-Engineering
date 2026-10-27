"""
hud.py - draws the detection boxes and the heads-up display panel.
"""

import cv2

# Colours are BGR (OpenCV order)
GREEN, RED, WHITE, BLACK, GREY = (60, 200, 60), (40, 40, 230), (255, 255, 255), (0, 0, 0), (170, 170, 170)


def draw_hud(frame, people, count, limit, crowded, fps, esp32_status, db_status):
    colour = RED if crowded else GREEN

    for x1, y1, x2, y2, conf in people:
        cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2)
        cv2.putText(frame, f"person {conf:.0%}", (x1, max(y1 - 8, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 2)

    # Semi-transparent panel, top-left
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (360, 200), BLACK, -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    cv2.putText(frame, f"PEOPLE: {count}", (25, 55), cv2.FONT_HERSHEY_SIMPLEX, 1.2, WHITE, 3)
    cv2.putText(frame, f"Limit: {limit}   FPS: {fps:.0f}", (25, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)
    status = "CROWDED!" if crowded else "NORMAL"
    cv2.putText(frame, f"Status: {status}", (25, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.9, colour, 2)
    cv2.putText(frame, f"ESP32: {esp32_status}", (25, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, GREY, 1)
    cv2.putText(frame, f"Database: {db_status}", (25, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.5, GREY, 1)