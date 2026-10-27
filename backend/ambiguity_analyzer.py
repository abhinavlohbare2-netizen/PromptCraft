"""
PromptCraft Ambiguity & Clarity Analyzer
----------------------------------------
Evaluates prompt ambiguity and vagueness using a 3-tier weighted dictionary
of vague quantifiers, uncalibrated adverbs, and underspecified phrases.

Scoring Rules (High Score = Low Ambiguity):
- Penalty 0   -> 10 / 10 (Crystal Clear)
- Penalty 1-2 ->  8 / 10 (Minor Ambiguity)
- Penalty 3-4 ->  6 / 10 (Moderate Ambiguity)
- Penalty 5-6 ->  4 / 10 (High Ambiguity)
- Penalty 7+  ->  2 / 10 (Extremely Vague)
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from config.settings import VAGUE_WORDS_FILE
from utils.helpers import load_json_file

# Fallback dictionary in case static JSON file is unavailable
DEFAULT_VAGUE_WORDS = {
    "level_1": {
        "weight": 1,
        "terms": ["some", "several", "appropriate", "relevant", "suitable", "reasonable", "various", "many", "few", "a lot", "stuff", "things"]
    },
    "level_2": {
        "weight": 2,
        "terms": ["detailed", "briefly", "properly", "effectively", "clearly", "good", "simple", "quickly", "nicely", "concise", "standard", "normal"]
    },
    "level_3": {
        "weight": 3,
        "terms": ["make it better", "explain it well", "give a good answer", "improve this", "do it properly", "best possible", "as needed", "write something good", "fix everything", "do what is right", "make it sound professional", "give me all details"]
    }
}

# Cached compiled regex patterns
_compiled_patterns: Optional[List[Dict[str, Any]]] = None


def get_vague_patterns() -> List[Dict[str, Any]]:
    """Loads and compiles regex patterns for all vague terms across the 3 tiers."""
    global _compiled_patterns
    if _compiled_patterns is not None:
        return _compiled_patterns
    
    data = load_json_file(VAGUE_WORDS_FILE)
    levels = data.get("levels", DEFAULT_VAGUE_WORDS) if data else DEFAULT_VAGUE_WORDS
    
    compiled: List[Dict[str, Any]] = []
    
    # Sort terms by length descending so longer phrases match before sub-words
    for level_key, level_info in levels.items():
        weight = level_info.get("weight", 1)
        terms = level_info.get("terms", [])
        for term in terms:
            pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
            compiled.append({
                "term": term,
                "weight": weight,
                "level": level_key,
                "pattern": pattern
            })
            
    compiled.sort(key=lambda x: len(x["term"]), reverse=True)
    _compiled_patterns = compiled
    return _compiled_patterns


def calculate_ambiguity_score(penalty: int) -> int:
    """Calculates the 0-10 score based on total accumulated penalty."""
    if penalty == 0:
        return 10
    elif penalty <= 2:
        return 8
    elif penalty <= 4:
        return 6
    elif penalty <= 6:
        return 4
    else:
        return 2


def analyze_ambiguity(prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes prompt text for ambiguous, vague, or under-specified terms.
    
    Args:
        prompt_data: Preprocessed dictionary containing 'cleaned_prompt'
        
    Returns:
        Structured evaluation dictionary for the Ambiguity parameter.
    """
    text = prompt_data.get("cleaned_prompt", "")
    if not text:
        return {
            "parameter": "ambiguity",
            "score": 10,
            "max_score": 10,
            "status": "Strong",
            "total_penalty": 0,
            "detected_count": 0,
            "terms_detected": [],
            "feedback": "No prompt text provided to evaluate."
        }
    
    patterns = get_vague_patterns()
    detected_terms: List[Dict[str, Any]] = []
    total_penalty = 0
    
    # Track matched spans to avoid double-counting sub-words of matched phrases
    matched_spans: List[Tuple[int, int]] = []
    
    for item in patterns:
        for match in item["pattern"].finditer(text):
            span = match.span()
            # Check if this span overlaps with an already matched longer phrase
            is_overlapping = any(
                max(span[0], existing[0]) < min(span[1], existing[1])
                for existing in matched_spans
            )
            if not is_overlapping:
                matched_spans.append(span)
                total_penalty += item["weight"]
                detected_terms.append({
                    "term": match.group(0),
                    "matched_rule": item["term"],
                    "weight": item["weight"],
                    "level": item["level"],
                    "position": span[0]
                })
    
    score = calculate_ambiguity_score(total_penalty)
    
    # Determine status & feedback (Cause only)
    unique_terms = list(dict.fromkeys([d["term"] for d in detected_terms]))
    
    if score >= 8:
        status = "Strong"
        joined_terms = ", ".join(unique_terms)
        feedback = "Prompt uses direct, unambiguous wording throughout." if total_penalty == 0 else f"Prompt is mostly clear with minor vague wording ('{joined_terms}')."
    elif score >= 5:
        status = "Moderate"
        joined_terms = ", ".join(unique_terms[:3])
        feedback = f"Prompt uses subjective or open-ended words ('{joined_terms}') that leave meaning open to interpretation."
    else:
        status = "Weak"
        joined_terms = ", ".join(unique_terms[:4])
        feedback = f"Prompt relies heavily on vague, subjective qualifiers ('{joined_terms}')."
    
    return {
        "parameter": "ambiguity",
        "score": score,
        "max_score": 10,
        "status": status,
        "total_penalty": total_penalty,
        "detected_count": len(detected_terms),
        "terms_detected": detected_terms,
        "unique_terms": unique_terms,
        "feedback": feedback
    }
