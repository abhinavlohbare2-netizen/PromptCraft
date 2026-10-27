"""
PromptCraft MongoDB Atlas Connection Manager
--------------------------------------------
Provides singleton client connection, database handle, and index creation.
"""

import os
from typing import Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
import certifi
from dotenv import load_dotenv

load_dotenv()

_client: Optional[MongoClient] = None
_db: Optional[Database] = None
_indexes_created: bool = False


def get_mongo_client() -> Optional[MongoClient]:
    """
    Returns or initializes a cached MongoClient connected to MongoDB Atlas.
    Uses certifi for robust SSL/TLS certificate verification.
    """
    global _client
    if _client is not None:
        return _client

    uri = os.getenv("MONGODB_URI")
    if not uri or "mongodb" not in uri:
        print("[MongoDB] Warning: MONGODB_URI is not configured in .env")
        return None

    try:
        _client = MongoClient(
            uri,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=4000,
            maxPoolSize=20,
            connectTimeoutMS=4000
        )
        return _client
    except Exception as e:
        print(f"[MongoDB] Connection warning: {e}")
        _client = None
        return None


def get_database() -> Optional[Database]:
    """Returns the PromptCraft database instance."""
    global _db, _indexes_created
    if _db is not None:
        return _db

    client = get_mongo_client()
    if client is None:
        return None

    db_name = os.getenv("MONGODB_DB_NAME", "promptcraft_db")
    _db = client[db_name]
    if not _indexes_created:
        _indexes_created = True
        import threading
        threading.Thread(target=_ensure_indexes, args=(_db,), daemon=True).start()
    return _db


def prewarm_mongo_connection():
    """Starts MongoDB Atlas connection and syncs user cache in background on app launch so login is instant."""
    import threading
    def _warmup():
        try:
            db = get_database()
            if db is not None:
                from backend.auth_service import _load_users_local, _save_users_local
                users_cursor = db.users.find({}, {"email": 1, "name": 1, "password_hash": 1, "salt": 1, "created_at": 1})
                users_local = _load_users_local()
                updated = False
                for u in users_cursor:
                    e = u.get("email")
                    if e and e not in users_local:
                        users_local[e] = {
                            "name": u.get("name", "User"),
                            "email": e,
                            "password_hash": u.get("password_hash", ""),
                            "salt": u.get("salt", ""),
                            "created_at": str(u.get("created_at", ""))
                        }
                        updated = True
                if updated:
                    _save_users_local(users_local)
        except Exception:
            pass
    threading.Thread(target=_warmup, daemon=True).start()


def _ensure_indexes(db: Database):
    """Creates essential indexes on collections for fast querying and unique constraints."""
    try:
        # Users: Unique index on email
        db.users.create_index([("email", ASCENDING)], unique=True)

        # Evaluations: Compound index on user_email and timestamp (newest first)
        db.evaluations.create_index([("user_email", ASCENDING), ("created_at", DESCENDING)])

        # Optimizations: Index on evaluation ID and user_email
        db.optimizations.create_index([("eval_id", ASCENDING)])
        db.optimizations.create_index([("user_email", ASCENDING)])

        # Saved Prompts: Index on user_email
        db.saved_prompts.create_index([("user_email", ASCENDING)])

        # RAG Documents: Compound index on user_email and doc_name
        db.rag_documents.create_index([("user_email", ASCENDING), ("doc_name", ASCENDING)], unique=True)

        # RAG Chunks: Compound index on user_email, doc_name, and chunk_index
        db.rag_chunks.create_index([("user_email", ASCENDING), ("doc_name", ASCENDING), ("chunk_index", ASCENDING)])
    except Exception:
        # Index creation failure is non-blocking
        pass
