"""
PromptCraft Configuration & Settings Module
-------------------------------------------
Centralizes all application configurations, environment variables,
scoring parameter definitions, file paths, and AI model parameters.
"""

import os
from pathlib import Path
from typing import Dict, List, Any

# Project Metadata
PROJECT_NAME = "PromptCraft - Prompt Quality Evaluation & Learning System"

# Root & Subdirectory Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
BACKEND_DIR = BASE_DIR / "backend"
DATABASE_DIR = BASE_DIR / "database"
PAGES_DIR = BASE_DIR / "pages"
UTILS_DIR = BASE_DIR / "utils"

# Ensure required directories exist
for directory in [CONFIG_DIR, DATA_DIR, BACKEND_DIR, DATABASE_DIR, PAGES_DIR, UTILS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Data File Paths
VAGUE_WORDS_FILE = DATA_DIR / "vague_words.json"
PROMPT_TEMPLATES_FILE = DATA_DIR / "prompt_templates.json"
LEARNING_CONTENT_FILE = DATA_DIR / "learning_content.json"

import re

# Load environment variables manually from .env if present
def _load_env_file():
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip("'\"")

_load_env_file()

def _get_secret_or_env(key_name: str, default: str = "") -> str:
    """Retrieves config from environment variables or Streamlit secrets."""
    val = os.getenv(key_name, "")
    if val:
        return val.strip().strip("'\"")
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key_name in st.secrets:
            return str(st.secrets[key_name]).strip().strip("'\"")
    except Exception:
        pass
    return default


# Environment Credentials - Multi-Key Pool Support
def _extract_gemini_keys() -> List[str]:
    raw_keys = []
    # Check GEMINI_API_KEY (supports comma/semicolon separation)
    k1 = _get_secret_or_env("GEMINI_API_KEY", "")
    if k1:
        raw_keys.extend(re.split(r"[,;]+", k1))
        
    # Check GEMINI_API_KEYS
    k_all = _get_secret_or_env("GEMINI_API_KEYS", "")
    if k_all:
        raw_keys.extend(re.split(r"[,;]+", k_all))
        
    # Check numbered keys GEMINI_API_KEY_1 to GEMINI_API_KEY_10
    for i in range(1, 11):
        ki = _get_secret_or_env(f"GEMINI_API_KEY_{i}", "")
        if ki:
            raw_keys.extend(re.split(r"[,;]+", ki))
            
    # Clean, strip, and de-duplicate while preserving order
    clean_keys = []
    seen = set()
    for k in raw_keys:
        stripped = k.strip().strip("'\"")
        if stripped and stripped not in seen:
            seen.add(stripped)
            clean_keys.append(stripped)
    return clean_keys

GEMINI_API_KEYS = _extract_gemini_keys()
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""
MONGODB_URI = _get_secret_or_env("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = _get_secret_or_env("DATABASE_NAME", "promptcraft_db")


# MongoDB Collections
COLLECTION_EVALUATIONS = "evaluations"
COLLECTION_TEMPLATES = "templates"
COLLECTION_LEARNING = "learning_progress"
COLLECTION_DOCUMENTS = "reference_documents"

# NLP & AI Model Settings
SPACY_MODEL = "en_core_web_sm"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_EMBEDDING_MODEL = "models/gemini-embedding-001"
WHISPER_MODEL = "base"

# Input Length Constraints
MIN_PROMPT_LENGTH = 3
MAX_PROMPT_LENGTH = 10000

# The 7 Evaluation Quality Parameters
EVALUATION_PARAMETERS: List[str] = [
    "grammar",
    "readability",
    "specificity",
    "context",
    "completeness",
    "ambiguity",
    "constraints"
]

# Tiered Parameter Weights (Sum = 10.0x for Direct 100-Point Scale)
PARAMETER_WEIGHTS: Dict[str, float] = {
    "specificity": 2.0,    # Tier 1 (20%): Micro-Technical Depth & Precision
    "completeness": 2.0,   # Tier 1 (20%): Macro-Structural Architecture
    "constraints": 1.5,    # Tier 2 (15%): Boundary Limits & Negative Rules
    "context": 1.5,        # Tier 2 (15%): Operational Domain & Scenario
    "ambiguity": 1.0,      # Tier 3 (10%): Lexical Precision & Vagueness Deductions
    "readability": 1.0,    # Tier 3 (10%): ModernBERT Linguistic Flow & Cognitive Ease
    "grammar": 1.0         # Tier 3 (10%): LanguageTool Syntax & Spelling Hygiene
}

# Parameter Display Metadata
PARAMETER_METADATA: Dict[str, Dict[str, Any]] = {
    "grammar": {
        "label": "Grammar & Syntax",
        "description": "Checks structural correctness, typos, and grammatical errors using LanguageTool.",
        "max_score": 10,
        "weight": 1.0,
        "tier": "Tier 3 (Linguistic Foundation)",
        "icon": "✍️"
    },
    "readability": {
        "label": "Readability & Fluency",
        "description": "Evaluates sentence flow, cognitive ease, and active voice using ModernBERT sequence classification.",
        "max_score": 10,
        "weight": 1.0,
        "tier": "Tier 3 (Linguistic Foundation)",
        "icon": "📖"
    },
    "specificity": {
        "label": "Specificity & Depth",
        "description": "Evaluates micro-level technical depth, subtopic granularity, audience level, and concrete code/test examples.",
        "max_score": 10,
        "weight": 2.0,
        "tier": "Tier 1 (Core Quality Impact)",
        "icon": "🎯"
    },
    "context": {
        "label": "Context & Background",
        "description": "Evaluates operational domain, system architecture, practical situation, end-user persona, and business objective.",
        "max_score": 10,
        "weight": 1.5,
        "tier": "Tier 2 (Operational Limits)",
        "icon": "🌐"
    },
    "completeness": {
        "label": "Completeness",
        "description": "Evaluates macro prompt architecture across 5 pillars: Role, Core Task, Input Reference, Deliverable, and Acceptance Criteria.",
        "max_score": 10,
        "weight": 2.0,
        "tier": "Tier 1 (Core Quality Impact)",
        "icon": "🧩"
    },
    "ambiguity": {
        "label": "Clarity / Low Ambiguity",
        "description": "Scans for vague quantifiers, uncalibrated adverbs, and subjective directives using a 3-tier weighted penalty dictionary.",
        "max_score": 10,
        "weight": 1.0,
        "tier": "Tier 3 (Linguistic Foundation)",
        "icon": "🔍"
    },
    "constraints": {
        "label": "Constraints & Guardrails",
        "description": "Evaluates word/length bounds, strict schema formats, tone rules, complexity bounds, and negative exclusions.",
        "max_score": 10,
        "weight": 1.5,
        "tier": "Tier 2 (Operational Limits)",
        "icon": "📏"
    }
}

# Total Maximum Weighted Score (Direct 100-Point Scale)
TOTAL_MAX_RAW_SCORE = 70
TOTAL_WEIGHTED_MAX_SCORE = 100

# Quality Score Bands (0 - 100 Scale)
QUALITY_TIERS = {
    "Excellent": {
        "min_score": 85,
        "color": "#10B981",  # Green
        "description": "Outstanding prompt with clear instructions, rich context, and strict constraints.",
        "badge": "🌟 Excellent"
    },
    "Good": {
        "min_score": 70,
        "color": "#3B82F6",  # Blue
        "description": "Solid prompt that conveys intent well, with minor areas for refinement.",
        "badge": "👍 Good"
    },
    "Fair": {
        "min_score": 50,
        "color": "#F59E0B",  # Amber/Yellow
        "description": "Acceptable prompt but contains ambiguity, missing context, or few constraints.",
        "badge": "⚠️ Fair"
    },
    "Needs Improvement": {
        "min_score": 0,
        "color": "#EF4444",  # Red
        "description": "Prompt is vague, too brief, or lacks key instructions needed for optimal AI output.",
        "badge": "🔴 Needs Improvement"
    }
}

def get_quality_tier(score: float) -> Dict[str, Any]:
    """Returns the quality tier metadata based on overall score (0 - 100)."""
    if score >= 85:
        return {"tier": "Excellent", **QUALITY_TIERS["Excellent"]}
    elif score >= 70:
        return {"tier": "Good", **QUALITY_TIERS["Good"]}
    elif score >= 50:
        return {"tier": "Fair", **QUALITY_TIERS["Fair"]}
    else:
        return {"tier": "Needs Improvement", **QUALITY_TIERS["Needs Improvement"]}
