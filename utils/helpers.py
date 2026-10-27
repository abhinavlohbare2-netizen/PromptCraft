"""
Helper Functions for PromptCraft
--------------------------------
Common utility functions for text formatting, JSON extraction, file loading,
and UI badge rendering.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional
from config.settings import get_quality_tier


def load_json_file(file_path: Path) -> Any:
    """Safely loads and parses a JSON file from disk."""
    try:
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Error] Failed to load JSON file {file_path}: {e}")
        return None


def extract_json_from_llm_response(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Robustly extracts and parses a JSON object from an LLM output string,
    handling markdown code blocks (```json ... ```), raw strings, trailing commas, or surrounding text.
    """
    if not raw_text or not isinstance(raw_text, str):
        return None
    
    text = raw_text.strip()
    if text.startswith("Error communicating with Gemini AI:"):
        return None
    
    # 1. Check for markdown code blocks (```json ... ``` or ``` ...)
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if json_match:
        text = json_match.group(1).strip()
    
    # 2. Try direct JSON parsing
    try:
        parsed = json.loads(text, strict=False)
        if isinstance(parsed, (dict, list)):
            return parsed  # type: ignore
    except json.JSONDecodeError:
        pass
    
    # 3. Fallback: Find outermost '{' and '}' or '[' and ']'
    start_brace = text.find("{")
    end_brace = text.rfind("}")
    start_bracket = text.find("[")
    end_bracket = text.rfind("]")
    
    candidates = []
    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        candidates.append(text[start_brace : end_brace + 1])
    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
        candidates.append(text[start_bracket : end_bracket + 1])
        
    for cand in candidates:
        try:
            parsed = json.loads(cand, strict=False)
            if isinstance(parsed, (dict, list)):
                return parsed  # type: ignore
        except json.JSONDecodeError:
            # Try removing trailing commas before closing braces/brackets
            cleaned = re.sub(r",\s*([}\]])", r"\1", cand)
            try:
                parsed = json.loads(cleaned, strict=False)
                if isinstance(parsed, (dict, list)):
                    return parsed  # type: ignore
            except json.JSONDecodeError:
                pass
    
    return None


def format_score_badge_html(score: float) -> str:
    """Generates an HTML badge string for displaying a score with color-coding."""
    tier_info = get_quality_tier(score)
    color = tier_info["color"]
    badge_text = tier_info["badge"]
    
    return (
        f'<span style="background-color: {color}22; color: {color}; '
        f'padding: 4px 12px; border-radius: 9999px; font-weight: 600; '
        f'border: 1px solid {color}55; font-size: 0.9rem;">'
        f'{badge_text} ({int(round(score))}/100)</span>'
    )


def count_words(text: str) -> int:
    """Returns the total word count of a string."""
    if not text:
        return 0
    return len(text.strip().split())


def copy_to_system_clipboard(text: str) -> bool:
    """Copies text to the system OS clipboard across Windows, Linux, and macOS."""
    if not text:
        return False
    import sys
    # 1. Native Windows clip.exe (Zero external dependencies, fast, native)
    if sys.platform == "win32":
        try:
            import subprocess
            proc = subprocess.run(
                ["clip"],
                input=text.encode("utf-16le"),
                check=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            if proc.returncode == 0:
                return True
        except Exception:
            pass
            
    # 2. Pyperclip library
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        pass
        
    return False


def embed_script_component(html_code: str, height: int = 0):
    """Executes client-side script in an iframe without triggering Streamlit's deprecation console warning."""
    import streamlit as st
    try:
        if hasattr(st, "_main") and hasattr(st._main, "_html"):
            return st._main._html(html_code, height=height)
    except Exception:
        pass
    import streamlit.components.v1 as components
    return components.html(html_code, height=height)


def inject_client_clipboard_copy(text: str):
    """Executes client-side copy directly inside the browser DOM."""
    import json
    safe_text = json.dumps(text)
    embed_script_component(f"""
    <script>
    (function() {{
        const text = {safe_text};
        let copied = false;
        try {{
            if (window.parent && window.parent.navigator && window.parent.navigator.clipboard) {{
                window.parent.navigator.clipboard.writeText(text);
                copied = true;
            }}
        }} catch(e) {{}}
        if (!copied) {{
            try {{
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText(text);
                    copied = true;
                }}
            }} catch(e) {{}}
        }}
        try {{
            const pdoc = (window.parent && window.parent.document) ? window.parent.document : document;
            const ta = pdoc.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            ta.style.left = '-9999px';
            pdoc.body.appendChild(ta);
            ta.focus();
            ta.select();
            pdoc.execCommand('copy');
            pdoc.body.removeChild(ta);
        }} catch(e) {{}}
    }})();
    </script>
    """, height=0)

