import hashlib
import hmac
import secrets
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from lottery_sim.user_workspace import normalize_username


PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 260_000
SESSION_TTL_DAYS = 7
SESSION_COOKIE_NAME = "lottery_session"


@dataclass(frozen=True)
class User:
    username: str
    display_name: str
    is_admin: bool
    is_enabled: bool


def hash_password(password: str, salt: Optional[bytes] = None, iterations: int = PASSWORD_ITERATIONS) -> str:
    salt_bytes = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        str(password).encode("utf-8"),
        salt_bytes,
        iterations,
    )
    return f"{PASSWORD_ALGORITHM}${iterations}${salt_bytes.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations_text, salt_hex, digest_hex = str(encoded).split("$", 3)
        if algorithm != PASSWORD_ALGORITHM:
            return False
        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_hex)
    except (TypeError, ValueError):
        return False
    expected = hash_password(password, salt=salt, iterations=iterations)
    return hmac.compare_digest(expected, encoded)


class AuthStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)

    def init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_admin INTEGER NOT NULL,
                    is_enabled INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY(username) REFERENCES users(username)
                )
                """
            )
            conn.commit()

    def bootstrap_admin(self, username: str, password: str) -> User:
        safe_username = normalize_username(username)
        existing = self.get_user(safe_username)
        if existing is not None:
            return existing
        return self.create_user(safe_username, password, display_name=safe_username, is_admin=True)

    def create_user(
        self,
        username: str,
        password: str,
        display_name: str = "",
        is_admin: bool = False,
        is_enabled: bool = True,
    ) -> User:
        safe_username = normalize_username(username)
        self.init_db()
        user = User(
            username=safe_username,
            display_name=display_name or safe_username,
            is_admin=bool(is_admin),
            is_enabled=bool(is_enabled),
        )
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                """
                INSERT INTO users (
                    username, display_name, password_hash, is_admin,
                    is_enabled, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user.username,
                    user.display_name,
                    hash_password(password),
                    int(user.is_admin),
                    int(user.is_enabled),
                    _utc_now().isoformat(),
                ),
            )
            conn.commit()
        return user

    def get_user(self, username: str) -> Optional[User]:
        safe_username = normalize_username(username)
        self.init_db()
        with closing(sqlite3.connect(self.db_path)) as conn:
            row = conn.execute(
                """
                SELECT username, display_name, is_admin, is_enabled
                FROM users
                WHERE username = ?
                """,
                (safe_username,),
            ).fetchone()
        if row is None:
            return None
        return _user_from_row(row)

    def authenticate(self, username: str, password: str) -> Optional[User]:
        safe_username = normalize_username(username)
        self.init_db()
        with closing(sqlite3.connect(self.db_path)) as conn:
            row = conn.execute(
                """
                SELECT username, display_name, password_hash, is_admin, is_enabled
                FROM users
                WHERE username = ?
                """,
                (safe_username,),
            ).fetchone()
        if row is None:
            return None
        if not bool(row[4]):
            return None
        if not verify_password(password, str(row[2])):
            return None
        return User(
            username=str(row[0]),
            display_name=str(row[1]),
            is_admin=bool(row[3]),
            is_enabled=bool(row[4]),
        )

    def create_session(self, username: str, ttl: timedelta = timedelta(days=SESSION_TTL_DAYS)) -> str:
        safe_username = normalize_username(username)
        if self.get_user(safe_username) is None:
            raise ValueError(f"unknown user: {safe_username}")
        token = secrets.token_urlsafe(32)
        now = _utc_now()
        expires_at = now + ttl
        self.init_db()
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                """
                INSERT INTO sessions (token_hash, username, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (_hash_token(token), safe_username, now.isoformat(), expires_at.isoformat()),
            )
            conn.commit()
        return token

    def get_session_user(self, token: str) -> Optional[User]:
        token_hash = _hash_token(token)
        self.init_db()
        with closing(sqlite3.connect(self.db_path)) as conn:
            row = conn.execute(
                """
                SELECT users.username, users.display_name, users.is_admin,
                       users.is_enabled, sessions.expires_at
                FROM sessions
                JOIN users ON users.username = sessions.username
                WHERE sessions.token_hash = ?
                """,
                (token_hash,),
            ).fetchone()
        if row is None:
            return None
        expires_at = datetime.fromisoformat(str(row[4]))
        if expires_at <= _utc_now() or not bool(row[3]):
            self.delete_session(token)
            return None
        return User(
            username=str(row[0]),
            display_name=str(row[1]),
            is_admin=bool(row[2]),
            is_enabled=bool(row[3]),
        )

    def delete_session(self, token: str) -> None:
        self.init_db()
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))
            conn.commit()


def _hash_token(token: str) -> str:
    return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _user_from_row(row) -> User:
    return User(
        username=str(row[0]),
        display_name=str(row[1]),
        is_admin=bool(row[2]),
        is_enabled=bool(row[3]),
    )
