import os

import psycopg
from psycopg.rows import dict_row


def _connect():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checks (
                id BIGSERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                ok BOOLEAN NOT NULL,
                status_code INT,
                latency_ms DOUBLE PRECISION NOT NULL,
                checked_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )


def save(result: dict) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO checks (url, ok, status_code, latency_ms) "
            "VALUES (%(url)s, %(ok)s, %(status_code)s, %(latency_ms)s)",
            result,
        )


def latest() -> list[dict]:
    with _connect() as conn:
        return conn.execute(
            "SELECT DISTINCT ON (url) url, ok, status_code, latency_ms, checked_at "
            "FROM checks ORDER BY url, checked_at DESC"
        ).fetchall()