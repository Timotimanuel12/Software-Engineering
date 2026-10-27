"""
esp32_link.py - INT-01: Python Core Script -> ESP32 Actuator.

Sends '1' (crowded) or '0' (normal). Runs on its own thread, so a slow or
missing ESP32 never freezes the video loop. If the ESP32 is unreachable, it
logs a warning, keeps running, and retries (Workshop 3 exception scenario).

Modes (config.ESP32_MODE):
  "serial" - USB cable, 115200 baud            (step 4)
  "wifi"   - HTTP GET http://<ESP32_HOST>/state?v=1   (step 5, needs the Wi-Fi ESP32 sketch)
  "off"    - no hardware, just prints
"""

import threading
import time
import urllib.request

import config


class ESP32Link:
    def __init__(self, mode: str = config.ESP32_MODE):
        self.mode = mode
        self.status = "starting"
        self._desired = None          # '1' or '0' that should be shown on the ESP32
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._serial = None
        self._thread = threading.Thread(target=self._run, name="esp32-link", daemon=True)
        self._thread.start()

    # ---------- called from the main loop (never blocks) ----------
    def send_state(self, crowded: bool):
        with self._lock:
            self._desired = "1" if crowded else "0"
        self._wake.set()

    def close(self):
        self._stop.set()
        self._wake.set()
        self._thread.join(timeout=2)
        if self._serial is not None:
            self._serial.close()

    # ---------- background thread ----------
    def _run(self):
        if self.mode == "off":
            self.status = "off"
            return
        last_sent, last_sent_at = None, 0.0
        while not self._stop.is_set():
            self._wake.wait(timeout=config.RESEND_EVERY_S)
            self._wake.clear()
            with self._lock:
                value = self._desired
            if value is None:
                continue
            # Send when the state changes, and re-send regularly as a heartbeat
            if value == last_sent and time.time() - last_sent_at < config.RESEND_EVERY_S:
                continue
            try:
                self._send(value)
                if value != last_sent:
                    print(f"[ESP32] sent '{value}'")
                last_sent, last_sent_at = value, time.time()
                self.status = f"connected ({self.mode})"
            except Exception as err:  # SerialException, URLError, timeout, OSError...
                if not self.status.startswith("UNREACHABLE"):
                    print(f"[ESP32] WARNING: cannot reach ESP32 ({err}). Retrying; video keeps running.")
                self.status = "UNREACHABLE - retrying"
                last_sent = None
                self._close_serial()
                self._stop.wait(config.RECONNECT_EVERY_S)

    def _send(self, value: str):
        if self.mode == "serial":
            if self._serial is None:
                import serial  # pyserial
                self._serial = serial.Serial(config.SERIAL_PORT, config.SERIAL_BAUD, timeout=1)
                time.sleep(2)  # opening the port resets the board; wait for it to boot
            self._serial.write(value.encode())
        elif self.mode == "wifi":
            url = f"http://{config.ESP32_HOST}:{config.ESP32_PORT}/state?v={value}"
            with urllib.request.urlopen(url, timeout=config.ESP32_TIMEOUT_S) as resp:
                if resp.status != 200:
                    raise OSError(f"ESP32 replied HTTP {resp.status}")
        else:
            raise ValueError(f"Unknown ESP32_MODE '{self.mode}'")

    def _close_serial(self):
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None