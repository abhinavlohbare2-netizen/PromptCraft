"""
PromptCraft Grammar Analyzer
----------------------------
Evaluates prompt grammar, syntax, and spelling quality using LanguageTool.

Scoring Rules (as per Specification):
- 0 errors   -> 10 / 10
- 1 error    ->  8 / 10
- 2-4 errors ->  5 / 10
- 5+ errors  ->  2 / 10
"""

import threading
from typing import Dict, Any, List, Optional
import language_tool_python  # type: ignore

# Cached LanguageTool instance and thread lock to avoid startup overhead/race conditions
_tool_instance: Optional[Any] = None
_grammar_lock = threading.Lock()


def get_language_tool() -> Any:
    """Returns a singleton cached instance of LanguageTool safely across threads."""
    global _tool_instance
    with _grammar_lock:
        if _tool_instance is None:
            try:
                _tool_instance = language_tool_python.LanguageTool("en-US")
            except Exception:
                # Fallback to public remote server if local java execution fails
                _tool_instance = language_tool_python.LanguageTool("en-US", remote_server="https://api.languagetool.org/v2/")
    return _tool_instance


def calculate_grammar_score(error_count: int) -> int:
    """Calculates the 0-10 grammar score based on error count."""
    if error_count == 0:
        return 10
    elif error_count == 1:
        return 8
    elif 2 <= error_count <= 4:
        return 5
    else:
        return 2


def analyze_grammar(prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes the grammatical correctness and spelling of the prompt.
    
    Args:
        prompt_data: Preprocessed dictionary containing 'cleaned_prompt'
        
    Returns:
        Structured evaluation result dictionary for the Grammar parameter.
    """
    text = prompt_data.get("cleaned_prompt", "")
    if not text:
        return {
            "parameter": "grammar",
            "score": 10,
            "max_score": 10,
            "status": "Strong",
            "error_count": 0,
            "errors": [],
            "feedback": "No text provided to evaluate."
        }
    
    try:
        tool = get_language_tool()
        matches = tool.check(text)
    except Exception as e:
        print(f"[Warning] LanguageTool evaluation warning: {e}")
        matches = []
    
    # Tech Terms Whitelist & Code Patterns (Ignore false positive spelling errors on code keywords)
    TECH_WHITELIST = {
        "sqlite", "sqlite3", "tkinter", "ttk", "treeview", "pep8", "asyncpg", "fastapi",
        "django", "flask", "pytorch", "tensorflow", "scikit", "numpy", "pandas", "rest",
        "oauth", "oauth2", "jwt", "tls", "sql", "nosql", "mongodb", "postgresql", "mysql",
        "graphql", "kubernetes", "docker", "redis", "devops", "json", "csv", "yaml", "xml",
        "markdown", "docstrings", "docstring", "pydantic", "bcrypt", "fastapi", "big-o",
        "dataset", "datasets", "subtopics", "subtopic", "codebase", "llm", "llms", "nosql"
    }

    # Extract detailed error objects (filtering out tech jargon false positives)
    detected_errors: List[Dict[str, Any]] = []
    for match in matches:
        error_len = getattr(match, "error_length", getattr(match, "errorLength", 0))
        rule_id = getattr(match, "rule_id", getattr(match, "ruleId", "GRAMMAR_RULE"))
        category = getattr(match, "category", "Grammar")
        
        # Extract the specific word that was flagged
        offset = getattr(match, "offset", 0)
        flagged_word = text[offset:offset+error_len].strip().strip(".,;:\"'()")
        flagged_word_lower = flagged_word.lower()
        
        # Skip if flagged word is a known tech term, markdown case suggestion, file path (.py, .js), proper noun, or location
        if rule_id in ("MORFOLOGIK_RULE_EN_US", "GERMAN_SPELLER_RULE") or "SPELL" in rule_id.upper() or "MARKDOWN" in rule_id.upper():
            if (
                flagged_word_lower in TECH_WHITELIST
                or any(flagged_word_lower.endswith(ext) for ext in (".py", ".js", ".ts", ".json", ".csv", ".db", ".sql", ".txt"))
                or "." in flagged_word_lower
                or any(t in flagged_word_lower for t in ("sqlite", "tkinter", "ttk", "pep8", "treeview", "markdown"))
                or (flagged_word and flagged_word[0].isupper() and flagged_word.isalpha())  # Capitalized proper noun / city
            ):
                continue

        detected_errors.append({
            "message": match.message,
            "context": match.context,
            "offset": offset,
            "length": error_len,
            "rule_id": rule_id,
            "category": category,
            "replacements": match.replacements[:3] if match.replacements else []
        })
    
    error_count = len(detected_errors)
    score = calculate_grammar_score(error_count)
    
    # Determine status (Cause only)
    if score >= 8:
        status = "Strong"
        feedback = "No spelling or grammar errors detected." if error_count == 0 else "Contains 1 minor typographical error."
    elif score >= 5:
        status = "Moderate"
        feedback = f"Contains {error_count} spelling or grammar errors that reduce prompt precision."
    else:
        status = "Weak"
        feedback = f"Contains {error_count} severe spelling, punctuation, or grammar errors."
    
    return {
        "parameter": "grammar",
        "score": score,
        "max_score": 10,
        "status": status,
        "error_count": error_count,
        "errors": detected_errors,
        "feedback": feedback
    }
