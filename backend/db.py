"""Shared MySQL connection pool and transaction helpers."""

from contextlib import contextmanager
import os
from pathlib import Path

from mysql.connector.pooling import MySQLConnectionPool


def _load_project_env():
    """Load local project settings from the git-ignored .env file, if present."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and value and key not in os.environ:
            os.environ[key] = value


_load_project_env()


_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = MySQLConnectionPool(
            pool_name="exoplanet_pool",
            pool_size=int(os.environ.get("DB_POOL_SIZE", "5")),
            host=os.environ.get("DB_HOST", "localhost"),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
            database=os.environ.get("DB_NAME", "exoplanets_db"),
        )
    return _pool


@contextmanager
def transaction():
    """Yield a pooled connection; commit on success, roll back on failure."""
    connection = _get_pool().get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()  # Returns the connection to the pool.


def fetch_all(sql, params=()):
    with transaction() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            return cursor.fetchall()
        finally:
            cursor.close()


def fetch_one(sql, params=()):
    with transaction() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            return cursor.fetchone()
        finally:
            cursor.close()


def execute(sql, params=()):
    """Run a write statement and return its affected-row count and ID."""
    with transaction() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(sql, params)
            return cursor.rowcount, cursor.lastrowid
        finally:
            cursor.close()


def call_procedure(sql, params=()):
    """Return the first result set from a stored procedure, closing all sets."""
    with transaction() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            result = cursor.fetchall()
            while cursor.nextset():
                pass
            return result
        finally:
            cursor.close()
