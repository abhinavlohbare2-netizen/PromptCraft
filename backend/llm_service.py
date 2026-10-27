"""
PromptCraft LLM Service Module
-------------------------------
Manages communication with Google Gemini Generative AI:
- Generates natural language explanations
- Produces structured JSON responses with robust markdown-fence stripping
- Implements automatic retries and graceful fallback handling

STRICT BOUNDARY:
The LLM is invoked only for qualitative explanations and prompt rewriting.
It MUST NOT calculate or override evaluation scores.
"""

import warnings
# Suppress deprecation warnings from legacy genai wrapper before import
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from typing import Dict, Any, Optional
import google.generativeai as genai  # type: ignore

from config.settings import GEMINI_API_KEYS, GEMINI_MODEL
from utils.helpers import extract_json_from_llm_response

# Multi-Key Pool State
_active_key_index = 0
_is_configured = False

def _configure_active_key():
    global _is_configured, _active_key_index
    if not GEMINI_API_KEYS:
        _is_configured = False
        return
    if _active_key_index >= len(GEMINI_API_KEYS):
        _active_key_index = 0
    key = GEMINI_API_KEYS[_active_key_index]
    try:
        genai.configure(api_key=key)
        _is_configured = True
    except Exception as e:
        print(f"[Warning] Failed to configure Gemini API Key #{_active_key_index + 1}: {e}")

_configure_active_key()


def is_llm_available() -> bool:
    """Returns True if at least one Gemini API key is configured."""
    return bool(GEMINI_API_KEYS and _is_configured)


def get_current_key_info() -> str:
    """Returns human-friendly info about active API key in pool."""
    if not GEMINI_API_KEYS:
        return "No API key configured"
    return f"Key #{_active_key_index + 1} of {len(GEMINI_API_KEYS)}"


def switch_to_next_key() -> bool:
    """Rotates to the next available API key in the pool."""
    global _active_key_index
    if len(GEMINI_API_KEYS) <= 1:
        return False
    _active_key_index = (_active_key_index + 1) % len(GEMINI_API_KEYS)
    next_key = GEMINI_API_KEYS[_active_key_index]
    try:
        genai.configure(api_key=next_key)
        print(f"[Info] Auto-Failover: Switched to Gemini API Key #{_active_key_index + 1} of {len(GEMINI_API_KEYS)}")
        return True
    except Exception as e:
        print(f"[Warning] Failed to configure Gemini API Key #{_active_key_index + 1}: {e}")
        return False


def generate_text(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.7,
    max_output_tokens: int = 2048,
    response_mime_type: Optional[str] = None
) -> str:
    """
    Generates a natural language text response from Gemini with seamless multi-key auto-failover.
    If an API key runs out of tokens or hits quota limits, it instantly switches to the next available key.
    
    Args:
        prompt: The user instruction / payload.
        system_instruction: Optional system persona or guidance.
        temperature: Sampling temperature (0.0 to 1.0).
        max_output_tokens: Maximum tokens in response.
        response_mime_type: Optional MIME type (e.g. 'application/json').
        
    Returns:
        Generated text string, or an informative message on error.
    """
    if not is_llm_available():
        return "LLM service is currently offline. Please provide a valid GEMINI_API_KEY in .env."
        
    candidate_models = [
        "gemini-3.5-flash-lite",
        "gemini-3.7-flash",
        "gemini-3.8-flash",
        GEMINI_MODEL
    ]
    # De-duplicate while preserving order
    seen = set()
    candidate_models = [m for m in candidate_models if m and not (m in seen or seen.add(m))]
    
    last_error = None
    
    for key_idx, key in enumerate(GEMINI_API_KEYS):
        try:
            genai.configure(api_key=key)
        except Exception as e:
            last_error = e
            continue
            
        for model_name in candidate_models:
            try:
                generation_config: Dict[str, Any] = {
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                }
                if response_mime_type:
                    generation_config["response_mime_type"] = response_mime_type
                
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=generation_config,  # type: ignore
                    system_instruction=system_instruction
                )
                
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                # If rate-limited or quota exhausted on this model, try the next model candidate
                # If all candidate models fail on this key, loop moves to next key
                continue
            
    print(f"[Error] All Gemini API keys exhausted: {last_error}")
    return f"Error communicating with Gemini AI: {str(last_error)}"


def generate_structured_json(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.2,
    max_retries: int = 1
) -> Optional[Dict[str, Any]]:
    """
    Generates and parses a structured JSON response from Gemini.
    Guarantees reliable dictionary output by using native application/json
    MIME type output and robust markdown-fence stripping.
    
    Args:
        prompt: Prompt payload with JSON schema specification.
        system_instruction: Optional system instruction enforcing JSON formatting.
        temperature: Low temperature for deterministic structured output.
        max_retries: Number of retries on malformed JSON.
        
    Returns:
        Parsed dictionary, or None if extraction fails.
    """
    if not is_llm_available():
        return None
        
    enforced_system = (
        "You are PromptCraft's structured analysis engine. "
        "You MUST respond ONLY with a valid JSON object matching the requested schema. "
        "Do NOT include conversational preamble, apologies, or markdown explanation outside the JSON."
    )
    if system_instruction:
        enforced_system = f"{enforced_system}\n\n{system_instruction}"
        
    for attempt in range(max_retries):
        try:
            raw_response = generate_text(
                prompt=prompt,
                system_instruction=enforced_system,
                temperature=temperature,
                response_mime_type="application/json"
            )
            
            # If the LLM call errored out (e.g. quota limit), exit immediately to fallback
            if not raw_response or raw_response.startswith("Error communicating with Gemini AI:"):
                return None
            
            parsed = extract_json_from_llm_response(raw_response)
            if parsed is not None:
                return parsed
                
            # If native JSON mode didn't succeed, try standard text extraction
            raw_response_fallback = generate_text(
                prompt=prompt,
                system_instruction=enforced_system,
                temperature=temperature
            )
            parsed_fallback = extract_json_from_llm_response(raw_response_fallback)
            if parsed_fallback is not None:
                return parsed_fallback
                
        except Exception as e:
            print(f"[Warning] LLM JSON generation error: {e}")
            
    return None
