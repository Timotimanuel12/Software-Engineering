"""
db_logger.py - INT-02: Python Core Script -> Neon Database.

Every 10 seconds, a background thread inserts the latest count into the
crowd_logs table. The video loop never waits for the database. If Neon is
unreachable, rows are kept in memory and sent when the connection returns.
"""

import threading
import time
from collections import deque
from datetime import datetime, timezone

import config

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS crowd_logs (
    id           BIGSERIAL PRIMARY KEY,
    recorded_at  TIMESTAMPTZ NOT NULL,
    person_count INTEGER     NOT NULL,
    crowd_limit  INTEGER     NOT NULL,
    is_crowded   BOOLEAN     NOT NULL
);
"""
INSERT_SQL = """
INSERT INTO crowd_logs (recorded_at, person_count, crowd_limit, is_crowded)
VALUES (%s, %s, %s, %s);
"""


class DBLogger:
    def __init__(self, database_url: str = config.DATABASE_URL):
        self.database_url = database_url
        self.status = "starting"
        self._latest = None                 # (count, limit, crowded)
        self._buffer = deque(maxlen=config.MAX_BUFFERED_ROWS)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._conn = None
        self._thread = threading.Thread(target=self._run, name="db-logger", daemon=True)
        self._thread.start()

    # ---------- called from the main loop (never blocks) ----------
    def update(self, count: int, limit: int, crowded: bool):
        with self._lock:
            self._latest = (count, limit, crowded)

    def close(self):
        self._stop.set()
        self._thread.join(timeout=5)
        if self._conn is not None:
            self._conn.close()

    # ---------- background thread ----------
    def _run(self):
        if not self.database_url:
            self.status = "off (no DATABASE_URL in .env)"
            print("[DB] DATABASE_URL not set - logging disabled.")
            return
        while not self._stop.wait(config.LOG_INTERVAL_S):
            with self._lock:
                latest = self._latest
            if latest is None:
                continue
            self._buffer.append((datetime.now(timezone.utc), *latest))
            self._flush()

    def _connect(self):
        import psycopg2
        self._conn = psycopg2.connect(self.database_url, connect_timeout=5)
        self._conn.autocommit = True
        with self._conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)

    def _flush(self):
        try:
            if self._conn is None or self._conn.closed:
                self._connect()
            with self._conn.cursor() as cur:
                while self._buffer:
                    cur.execute(INSERT_SQL, self._buffer[0])
                    self._buffer.popleft()
            self.status = "logging every 10 s"
        except Exception as err:
            if not self.status.startswith("OFFLINE"):
                print(f"[DB] WARNING: cannot reach Neon ({err}). Buffering rows; video keeps running.")
            self.status = f"OFFLINE - {len(self._buffer)} rows buffered"
            if self._conn is not None:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None