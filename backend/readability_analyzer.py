"""
PromptCraft Readability Analyzer
--------------------------------
Evaluates prompt readability and linguistic flow using the fine-tuned
ModernBERT transformer model: 'opendatalab/meta-rater-readability-rating'.

Inference Method:
- PyTorch + Hugging Face Transformers
- 6-class sequence classification (scores 0 to 5)
- Probability-weighted expectation score:
    model_score = sum(i * P(label_i) for i in 0..5)
- Normalization to PromptCraft 0-10 scale:
    promptcraft_score = (model_score / 5.0) * 10.0
"""

import os
import threading
from typing import Dict, Any, Optional, Tuple

# Suppress symlink warnings on Windows
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

MODEL_NAME = "opendatalab/meta-rater-readability-rating"

# Singleton cached tokenizer, model, and thread lock
_tokenizer: Optional[Any] = None
_model: Optional[Any] = None
_readability_lock = threading.Lock()


def get_readability_model() -> Tuple[Any, Any]:
    """
    Loads and caches the ModernBERT tokenizer and sequence classification model lazily.
    Uses a thread lock to ensure safe background pre-warming.
    """
    global _tokenizer, _model
    with _readability_lock:
        if _tokenizer is None or _model is None:
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification  # type: ignore
                tok = AutoTokenizer.from_pretrained(MODEL_NAME)
                mod = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
                if mod is not None:
                    mod.eval()
                _tokenizer = tok
                _model = mod
            except Exception as e:
                print(f"[Readability] Error loading ModernBERT model: {e}")
                return None, None
    return _tokenizer, _model



def analyze_readability(prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes prompt readability using the ModernBERT-base transformer model.
    
    Args:
        prompt_data: Preprocessed dictionary containing 'cleaned_prompt'
        
    Returns:
        Structured evaluation dictionary for the Readability parameter.
    """
    text = prompt_data.get("cleaned_prompt", "")
    if not text:
        return {
            "parameter": "readability",
            "score": 10.0,
            "max_score": 10,
            "model_score_0_5": 5.0,
            "status": "Strong",
            "model_name": MODEL_NAME,
            "feedback": "No text provided to evaluate."
        }
    
    try:
        tokenizer, model = get_readability_model()
        if tokenizer is None or model is None:
            raise RuntimeError("ModernBERT model not loaded")
            
        import torch  # type: ignore
        import torch.nn.functional as F  # type: ignore
        
        # Tokenize prompt (max length 512 tokens)
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )
        
        # Inference with PyTorch (no gradient calculation)
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = F.softmax(logits, dim=-1)[0]
            
            # Probability-weighted expected score across labels 0 to 5
            weights = torch.arange(0, 6, dtype=torch.float32, device=logits.device)
            raw_model_score = torch.sum(probs * weights).item()
            
            # Clamp between 0.0 and 5.0
            raw_model_score = max(0.0, min(5.0, raw_model_score))
            
            # Normalize to 0-10 scale
            normalized_score = round((raw_model_score / 5.0) * 10.0, 1)
            
    except Exception as e:
        print(f"[Warning] ModernBERT readability inference warning: {e}")
        # Fallback to standard baseline score
        raw_model_score = 3.5
        normalized_score = 7.0
    
    # Adjust scoring for short, simple, naturally readable prompts (< 20 words)
    words = text.split()
    word_count = len(words)
    if word_count <= 15 and normalized_score < 8.0:
        normalized_score = max(normalized_score, 8.5)
        raw_model_score = max(raw_model_score, 4.25)
    
    # Determine status & feedback (Cause only)
    if normalized_score >= 8.0:
        status = "Strong"
        feedback = "Prompt is concise, clear, and easy to read."
    elif normalized_score >= 5.0:
        status = "Moderate"
        if word_count > 25:
            feedback = "Prompt contains dense sentences that could be structured with line breaks or bullet points."
        else:
            feedback = "Prompt is moderately clear but could benefit from structured phrasing."
    else:
        status = "Weak"
        feedback = "Prompt uses convoluted phrasing and run-on sentences that make comprehension difficult."
    
    return {
        "parameter": "readability",
        "score": normalized_score,
        "max_score": 10,
        "model_score_0_5": round(raw_model_score, 2),
        "status": status,
        "model_name": MODEL_NAME,
        "feedback": feedback
    }
