"""
Authentication Service for PromptCraft - Prompt Quality Evaluation & Learning System
------------------------------------------------------------------------------------
Handles secure user registration, password hashing (PBKDF2-HMAC-SHA256 with salt),
credential verification, and persistent user storage in MongoDB Atlas (with local fallback).
"""

import json
import hashlib
import secrets
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

from database.repositories import get_user_by_email, create_user, update_user_password

# Root data directory for local fallback
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"


def _ensure_data_dir():
    """Ensures data directory exists and initializes default demo user."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        demo_hash, demo_salt = _hash_password("password123")
        default_data = {
            "demo@promptcraft.ai": {
                "name": "Demo User",
                "email": "demo@promptcraft.ai",
                "password_hash": demo_hash,
                "salt": demo_salt,
                "created_at": "2026-09-13T00:00:00Z"
            }
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=2)


def _hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Generates a secure PBKDF2-HMAC-SHA256 hash with salt."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return hashed, salt


def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifies a password against the stored PBKDF2 hash and salt."""
    hashed, _ = _hash_password(password, salt)
    return secrets.compare_digest(hashed, stored_hash)


def _load_users_local() -> Dict[str, Dict[str, Any]]:
    """Loads users dictionary from local file storage."""
    _ensure_data_dir()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

_load_users = _load_users_local


def _save_users_local(users: Dict[str, Dict[str, Any]]) -> bool:
    """Saves users dictionary to local storage."""
    _ensure_data_dir()
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
        return True
    except Exception:
        return False


def register_user(name: str, email: str, password: str) -> Tuple[bool, str]:
    """
    Registers a new user in MongoDB Atlas (with local file fallback).
    Returns (success, message).
    """
    email_clean = email.strip().lower()
    name_clean = name.strip()
    
    if not email_clean or "@" not in email_clean or "." not in email_clean:
        return False, "Please provide a valid email address."
    if not name_clean:
        return False, "Please enter your full name."
    if len(password) < 4:
        return False, "Password must be at least 4 characters long."

    pwd_hash, salt = _hash_password(password)

    # 1. Try MongoDB Atlas First
    mongo_user = get_user_by_email(email_clean)
    if mongo_user:
        return False, "An account with this email already exists. Please login."

    mongo_created = create_user(name_clean, email_clean, pwd_hash, salt)

    # 2. Also persist to local cache
    users_local = _load_users_local()
    users_local[email_clean] = {
        "name": name_clean,
        "email": email_clean,
        "password_hash": pwd_hash,
        "salt": salt,
        "created_at": "2026-09-13T00:00:00Z"
    }
    _save_users_local(users_local)

    if mongo_created or email_clean in users_local:
        return True, "Account created successfully! You can now log in."

    return False, "Failed to create account. Please try again."


def authenticate_user(email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Authenticates a user with email and password via MongoDB Atlas (with fallback).
    Returns (success, user_dict, message).
    """
    email_clean = email.strip().lower()
    
    if not email_clean or not password:
        return False, None, "Please enter both email and password."

    # 1. Fast path: Check local user storage first (< 1 ms latency)
    users_local = _load_users_local()
    if email_clean in users_local:
        user = users_local[email_clean]
        if _verify_password(password, user.get("password_hash", ""), user.get("salt", "")):
            return True, {"name": user.get("name", "User"), "email": email_clean}, "Login successful!"
        else:
            return False, None, "Incorrect password. Please try again."

    # 2. Check MongoDB Atlas (if user registered on another device or cache missed)
    mongo_user = get_user_by_email(email_clean)
    if mongo_user:
        if _verify_password(password, mongo_user.get("password_hash", ""), mongo_user.get("salt", "")):
            # Cache locally for future instant sub-millisecond logins
            users_local[email_clean] = {
                "name": mongo_user.get("name", "User"),
                "email": email_clean,
                "password_hash": mongo_user.get("password_hash", ""),
                "salt": mongo_user.get("salt", ""),
                "created_at": str(mongo_user.get("created_at", ""))
            }
            _save_users_local(users_local)
            return True, {"name": mongo_user.get("name", "User"), "email": email_clean}, "Login successful!"
        else:
            return False, None, "Incorrect password. Please try again."

    # Default fallback for demo accounts
    if email_clean == "demo@promptcraft.ai" and password == "password123":
        return True, {"name": "Demo User", "email": email_clean}, "Login successful!"

    return False, None, "No account found with this email. Please sign up first."


def reset_user_password(email: str, new_password: str) -> Tuple[bool, str]:
    """
    Resets the password for an existing user in MongoDB Atlas and local storage.
    Returns (success, message).
    """
    email_clean = email.strip().lower()
    if not email_clean or "@" not in email_clean or "." not in email_clean:
        return False, "Please provide a valid email address."
    if len(new_password) < 4:
        return False, "New password must be at least 4 characters long."

    pwd_hash, salt = _hash_password(new_password)

    # 1. Check if user exists in local or MongoDB
    users_local = _load_users_local()
    mongo_user = get_user_by_email(email_clean)

    if email_clean not in users_local and not mongo_user:
        return False, "No account found with this email. Please check your email or create a new account."

    # 2. Update in MongoDB Atlas
    updated_mongo = update_user_password(email_clean, pwd_hash, salt)

    # 3. Update in local cache
    user_name = "User"
    if email_clean in users_local:
        user_name = users_local[email_clean].get("name", "User")
        users_local[email_clean]["password_hash"] = pwd_hash
        users_local[email_clean]["salt"] = salt
    elif mongo_user:
        user_name = mongo_user.get("name", "User")
        users_local[email_clean] = {
            "name": user_name,
            "email": email_clean,
            "password_hash": pwd_hash,
            "salt": salt,
            "created_at": str(mongo_user.get("created_at", ""))
        }
    _save_users_local(users_local)

    return True, "Password reset successfully! You can now log in with your new password."
