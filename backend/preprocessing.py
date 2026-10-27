"""
PromptCraft Preprocessing Module
--------------------------------
Implements Steps 0 through 5 of the prompt preparation pipeline:
- Step 0: Input Validation
- Step 1: Text Cleaning
- Step 2: Case Normalization
- Step 3: Tokenization & POS Tagging (spaCy)
- Step 4: Stop Word Tagging & Filtering
- Step 5: Sentence Segmentation

CRITICAL RULE: The original user prompt is never overwritten or mutated.
"""

import re
import threading
from typing import Dict, Any, List, Optional

from config.settings import SPACY_MODEL
from utils.validators import validate_prompt_input

# Lazy-loaded spaCy model cache and thread lock
_nlp_model: Optional[Any] = None
_spacy_lock = threading.Lock()


def get_spacy_nlp() -> Any:
    """
    Loads and caches the spaCy NLP model safely across threads.
    Falls back gracefully to a blank English model if the pipeline model is missing.
    """
    global _nlp_model
    with _spacy_lock:
        if _nlp_model is None:
            try:
                import spacy  # type: ignore
                _nlp_model = spacy.load(SPACY_MODEL)
            except Exception:
                try:
                    import spacy  # type: ignore
                    import en_core_web_sm  # type: ignore
                    _nlp_model = en_core_web_sm.load()
                except Exception:
                    try:
                        import spacy  # type: ignore
                        # Resilient fallback: blank English pipeline with sentencizer
                        _nlp_model = spacy.blank("en")
                        if "sentencizer" not in _nlp_model.pipe_names:
                            _nlp_model.add_pipe("sentencizer")
                    except Exception:
                        _nlp_model = None
    return _nlp_model


def clean_text(raw_text: str) -> str:
    """
    Step 1: Text Cleaning
    - Normalizes horizontal whitespace (multiple spaces/tabs to single space)
    - Normalizes excessive newlines (max 2 consecutive newlines)
    - Normalizes unicode dashes (en-dash, em-dash to standard hyphen)
    - Normalizes smart/curly quotes to standard quotes
    - Strips unmatched solitary leading/trailing quotation marks
    - Trims leading and trailing whitespace
    """
    if not raw_text:
        return ""
    # Normalize carriage returns
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    # Normalize unicode dashes
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    # Normalize smart quotes
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    # Replace multiple horizontal spaces/tabs with a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Replace 3 or more newlines with 2 newlines
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    text = text.strip()
    
    # Strip solitary trailing unmatched quote (e.g. prompt ending in ...on time.")
    if text.endswith('"') and text.count('"') % 2 != 0:
        text = text[:-1].rstrip()
    if text.startswith('"') and text.count('"') % 2 != 0:
        text = text[1:].lstrip()
        
    return text


def preprocess_prompt(raw_prompt: str) -> Dict[str, Any]:
    """
    Executes the full 6-step preprocessing pipeline.
    
    Args:
        raw_prompt: The exact text entered or transcribed from the user.
        
    Returns:
        A structured dictionary containing validated, cleaned, tokenized,
        and segmented representations of the prompt.
        
    Raises:
        ValueError: If validation (Step 0) fails.
    """
    # -------------------------------------------------------------
    # Step 0: Input Validation
    # -------------------------------------------------------------
    is_valid, error_msg = validate_prompt_input(raw_prompt)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Preserve the unmodified original prompt
    original_prompt = raw_prompt
    
    # -------------------------------------------------------------
    # Step 1: Text Cleaning
    # -------------------------------------------------------------
    cleaned_prompt = clean_text(original_prompt)
    
    # -------------------------------------------------------------
    # Step 2: Case Normalization (Lowercase Analytical Copy)
    # -------------------------------------------------------------
    cleaned_prompt_lower = cleaned_prompt.lower()
    
    # -------------------------------------------------------------
    # Step 3, 4, 5: spaCy NLP Pipeline Processing
    # -------------------------------------------------------------
    nlp = get_spacy_nlp()
    doc = nlp(cleaned_prompt)
    
    # Step 3: Tokens, Lemmas, and POS Tags
    tokens: List[str] = [token.text for token in doc]
    lemmas: List[str] = [token.lemma_ for token in doc]
    pos_tags: List[Dict[str, str]] = [
        {"text": token.text, "pos": token.pos_, "tag": token.tag_}
        for token in doc
    ]
    
    # Step 4: Stop Word Tagging & Filtering
    stop_words: List[str] = [
        token.text for token in doc if token.is_stop and not token.is_punct and not token.is_space
    ]
    non_stop_tokens: List[str] = [
        token.text for token in doc if not token.is_stop and not token.is_punct and not token.is_space
    ]
    
    # Step 5: Sentence Segmentation
    sentences: List[str] = [
        sent.text.strip() for sent in doc.sents if sent.text.strip()
    ]
    # Fallback if sentence splitter returned empty
    if not sentences and cleaned_prompt:
        sentences = [cleaned_prompt]
    
    # Words (excluding punctuation and whitespace)
    words: List[str] = [
        token.text for token in doc if not token.is_punct and not token.is_space
    ]
    
    return {
        "original_prompt": original_prompt,
        "cleaned_prompt": cleaned_prompt,
        "cleaned_prompt_lower": cleaned_prompt_lower,
        "tokens": tokens,
        "lemmas": lemmas,
        "pos_tags": pos_tags,
        "stop_words": stop_words,
        "non_stop_tokens": non_stop_tokens,
        "sentences": sentences,
        "sentence_count": len(sentences),
        "word_count": len(words),
        "char_count": len(cleaned_prompt),
        "spacy_doc": doc
    }
