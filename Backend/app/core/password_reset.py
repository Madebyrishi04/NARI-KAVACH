
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

RESET_TOKEN_EXPIRE_MINUTES = 15


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def reset_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        minutes=RESET_TOKEN_EXPIRE_MINUTES
    )
