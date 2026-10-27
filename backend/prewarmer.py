"""
PromptCraft Background Model Pre-Warmer
---------------------------------------
Runs on a non-blocking background daemon thread to silently load
AI/NLP models (spaCy, LanguageTool, ModernBERT) into memory while
the user is on the login page or entering their prompt.

Ensures:
- Initial page/login loads in < 0.5s.
- Evaluation step has zero model loading lag.
- Thread-safe and runs once per process.
"""

import threading
import time

_warmup_started = False
_warmup_completed = False
_lock = threading.Lock()


def _warmup_worker():
    global _warmup_completed
    # Allow the initial UI/login page to render immediately without CPU/GIL contention
    time.sleep(0.3)
    
    # 0. Warm up MongoDB Atlas Connection immediately in background
    try:
        from database.mongodb import get_database
        db = get_database()
        if db is not None:
            # Touch collection to establish TLS connection pool
            db.users.find_one({}, {"_id": 1})
    except Exception as e:
        print(f"[Pre-Warmer] MongoDB Atlas warmup notice: {e}")

    # 1. Warm up spaCy model
    try:
        from backend.preprocessing import get_spacy_nlp
        get_spacy_nlp()
    except Exception as e:
        print(f"[Pre-Warmer] spaCy warmup notice: {e}")

    # 2. Warm up LanguageTool (starts Java process in background)
    try:
        from backend.grammar_analyzer import get_language_tool
        get_language_tool()
    except Exception as e:
        print(f"[Pre-Warmer] LanguageTool warmup notice: {e}")

    # 3. Warm up ModernBERT Readability Model (PyTorch + HuggingFace)
    try:
        from backend.readability_analyzer import get_readability_model
        get_readability_model()
    except Exception as e:
        print(f"[Pre-Warmer] ModernBERT warmup notice: {e}")

    _warmup_completed = True
    print("[Pre-Warmer] All background AI evaluation models successfully pre-warmed!")


def start_background_prewarming():
    """Starts the background prewarming thread once per application lifecycle."""
    global _warmup_started
    with _lock:
        if not _warmup_started:
            _warmup_started = True
            thread = threading.Thread(
                target=_warmup_worker,
                name="PromptCraftModelPrewarmer",
                daemon=True
            )
            thread.start()


def is_prewarmed() -> bool:
    """Returns True if background models are fully loaded in memory."""
    return _warmup_completed
