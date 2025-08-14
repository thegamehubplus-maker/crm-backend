import os
import time
import bcrypt
import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "change_me")
JWT_EXPIRES = int(os.getenv("JWT_EXPIRES", "86400"))  # seconds


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plain-text password against a hashed password."""
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(user_id: int, email: str, role: str) -> str:
    """Create a JWT for the given user information."""
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + JWT_EXPIRES,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decode a JWT and return its payload."""
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])