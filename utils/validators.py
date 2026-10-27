"""
Validation Utilities for PromptCraft
------------------------------------
Provides input validation checks for prompts, files, and payload structures.
"""

from typing import Tuple
from config.settings import MIN_PROMPT_LENGTH, MAX_PROMPT_LENGTH

ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".webm"}


def validate_prompt_input(text: str) -> Tuple[bool, str]:
    """
    Validates user prompt text according to Step 0 Preprocessing rules.
    
    Returns:
        (is_valid: bool, error_message: str)
    """
    if text is None:
        return False, "Prompt cannot be None."
    
    # Check if empty or whitespace-only
    stripped = text.strip()
    if not stripped:
        return False, "Prompt is empty. Please enter or upload a prompt to analyze."
    
    # Check minimum character length
    if len(stripped) < MIN_PROMPT_LENGTH:
        return False, f"Prompt is too short (minimum {MIN_PROMPT_LENGTH} characters required)."
    
    # Check maximum character length
    if len(text) > MAX_PROMPT_LENGTH:
        return False, f"Prompt exceeds the maximum allowed length ({MAX_PROMPT_LENGTH} characters)."
    
    return True, ""


def validate_document_file(filename: str) -> Tuple[bool, str]:
    """Validates if an uploaded document format is supported."""
    if not filename:
        return False, "No filename provided."
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        return False, f"Unsupported document format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_DOCUMENT_EXTENSIONS))}"
    return True, ""


def validate_image_file(filename: str) -> Tuple[bool, str]:
    """Validates if an uploaded image format is supported for OCR."""
    if not filename:
        return False, "No filename provided."
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"Unsupported image format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
    return True, ""


def validate_audio_file(filename: str) -> Tuple[bool, str]:
    """Validates if an uploaded audio format is supported for Whisper."""
    if not filename:
        return False, "No filename provided."
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        return False, f"Unsupported audio format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}"
    return True, ""
