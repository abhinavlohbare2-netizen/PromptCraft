"""
PromptCraft Preprocessing Module
--------------------------------
Implements Steps 0 through 5 of the prompt preparation pipeline:
- Step 0: Input Validation
- Step 1: Text Cleaning
- Step 2: Case Normalization
- Step 3: Tokenization & POS Tagging (spaCy with Bulletproof Fallback)
- Step 4: Stop Word Tagging & Filtering
- Step 5: Sentence Segmentation

CRITICAL RULE: The original user prompt is never overwritten or mutated.
"""

import re
import string
import threading
from typing import Dict, Any, List, Optional

from config.settings import SPACY_MODEL
from utils.validators import validate_prompt_input

# ---------------------------------------------------------------------------
# Built-in Standard English Stop Words & Directives (Zero-Dependency Fallback)
# ---------------------------------------------------------------------------
STANDARD_STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
    "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how",
    "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the",
    "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}

DIRECTIVE_VERBS = {
    "create", "write", "generate", "build", "develop", "explain", "summarize", "list",
    "design", "implement", "analyze", "draft", "provide", "produce", "compose", "optimize",
    "refactor", "evaluate", "compare", "classify", "formulate", "describe", "outline",
    "help", "review", "give", "suggest", "act", "assume", "convert", "translate"
}


# ---------------------------------------------------------------------------
# Fallback spaCy Classes (Guarantees zero crashes if spaCy is missing/slow)
# ---------------------------------------------------------------------------
class FallbackToken:
    """Mock Token that matches spaCy Token API for downstream analyzers."""
    def __init__(self, text: str, pos: str = "NOUN", tag: str = "NN", dep: str = "", is_stop: bool = False):
        self.text = text
        self.lemma_ = text.lower()
        self.pos_ = pos
        self.tag_ = tag
        self.dep_ = dep
        self.is_stop = is_stop
        self.is_punct = len(text) > 0 and all(ch in string.punctuation for ch in text)
        self.is_space = text.isspace()
        self.ent_type_ = ""

    def __repr__(self) -> str:
        return self.text


class FallbackSpan:
    """Mock Span that matches spaCy Span API (for sents, ents, noun_chunks)."""
    def __init__(self, text: str, tokens: List[FallbackToken], label: str = ""):
        self.text = text
        self._tokens = tokens
        self.label_ = label

    def __iter__(self):
        return iter(self._tokens)

    def __len__(self) -> int:
        return len(self._tokens)

    def __repr__(self) -> str:
        return self.text


class FallbackDoc:
    """Mock Doc that provides identical API to spaCy Doc across PromptCraft analyzers."""
    def __init__(self, text: str):
        self.text = text
        self._tokens: List[FallbackToken] = []
        self._sents: List[FallbackSpan] = []
        self._ents: List[FallbackSpan] = []
        self._noun_chunks: List[FallbackSpan] = []
        self._parse(text)

    def _parse(self, text: str):
        # 1. Split into rough sentences
        raw_sents = [s.strip() for s in re.split(r'(?<=[.!?\n])\s+', text) if s.strip()]
        if not raw_sents and text.strip():
            raw_sents = [text.strip()]

        for sent_str in raw_sents:
            sent_tokens: List[FallbackToken] = []
            # Tokenize by words and punctuation
            raw_words = re.findall(r"\w+|[^\w\s]", sent_str, re.UNICODE)
            has_verb = False
            for w in raw_words:
                w_lower = w.lower()
                is_stop = w_lower in STANDARD_STOP_WORDS
                
                # POS heuristic
                pos = "NOUN"
                tag = "NN"
                dep = ""
                if w in string.punctuation:
                    pos = "PUNCT"
                    tag = "."
                elif w.isdigit():
                    pos = "NUM"
                    tag = "CD"
                elif w_lower in DIRECTIVE_VERBS or w_lower.endswith("ing") or w_lower.endswith("ed"):
                    pos = "VERB"
                    tag = "VB"
                    if not has_verb:
                        dep = "ROOT"
                        has_verb = True
                elif w[0].isupper() and not is_stop:
                    pos = "PROPN"
                    tag = "NNP"

                tok = FallbackToken(w, pos=pos, tag=tag, dep=dep, is_stop=is_stop)
                sent_tokens.append(tok)
                self._tokens.append(tok)

            if sent_tokens:
                self._sents.append(FallbackSpan(sent_str, sent_tokens))

        # 2. Extract Named Entities (Regex heuristic)
        # Numbers / Cardinals
        for match in re.finditer(r"\b\d+(?:\.\d+)?\b", text):
            t_str = match.group()
            self._ents.append(FallbackSpan(t_str, [FallbackToken(t_str, pos="NUM")], label="CARDINAL"))

        # Dates / Time
        for match in re.finditer(r"\b(?:\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|today|yesterday|tomorrow|january|february|march|april|may|june|july|august|september|october|november|december)\b", text, re.IGNORECASE):
            t_str = match.group()
            self._ents.append(FallbackSpan(t_str, [FallbackToken(t_str)], label="DATE"))

        # Organizations / Proper nouns / Acronyms
        for match in re.finditer(r"\b[A-Z]{2,}\b|\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", text):
            t_str = match.group()
            self._ents.append(FallbackSpan(t_str, [FallbackToken(t_str, pos="PROPN")], label="ORG"))

        # 3. Extract Noun Chunks (sequences of words)
        for chunk in re.findall(r"\b[A-Za-z0-9_-]+(?:\s+[A-Za-z0-9_-]+){1,3}\b", text):
            c_tokens = [FallbackToken(w, is_stop=(w.lower() in STANDARD_STOP_WORDS)) for w in chunk.split()]
            self._noun_chunks.append(FallbackSpan(chunk, c_tokens))

    def __iter__(self):
        return iter(self._tokens)

    def __len__(self) -> int:
        return len(self._tokens)

    def __getitem__(self, idx: int) -> FallbackToken:
        return self._tokens[idx]

    @property
    def sents(self) -> List[FallbackSpan]:
        return self._sents

    @property
    def ents(self) -> List[FallbackSpan]:
        return self._ents

    @property
    def noun_chunks(self) -> List[FallbackSpan]:
        return self._noun_chunks


class FallbackSpacyPipeline:
    """Callable fallback pipeline that produces FallbackDoc."""
    def __call__(self, text: str) -> FallbackDoc:
        return FallbackDoc(text)


# ---------------------------------------------------------------------------
# Lazy-loaded spaCy model cache and thread lock
# ---------------------------------------------------------------------------
_nlp_model: Optional[Any] = None
_spacy_lock = threading.Lock()


def get_spacy_nlp() -> Any:
    """
    Loads and caches the spaCy NLP model safely across threads.
    Guaranteed to NEVER return None; falls back seamlessly to FallbackSpacyPipeline.
    """
    global _nlp_model
    with _spacy_lock:
        if _nlp_model is not None:
            return _nlp_model

        # 1. Try loading specified SPACY_MODEL ("en_core_web_sm")
        try:
            import spacy  # type: ignore
            try:
                _nlp_model = spacy.load(SPACY_MODEL)
                return _nlp_model
            except Exception:
                pass

            # 2. Try loading default "en_core_web_sm" directly
            try:
                _nlp_model = spacy.load("en_core_web_sm")
                return _nlp_model
            except Exception:
                pass

            # 3. Try importing module directly
            try:
                import en_core_web_sm  # type: ignore
                _nlp_model = en_core_web_sm.load()
                return _nlp_model
            except Exception:
                pass

            # 4. Try blank English pipeline with sentencizer
            try:
                blank_nlp = spacy.blank("en")
                if "sentencizer" not in blank_nlp.pipe_names:
                    blank_nlp.add_pipe("sentencizer")
                _nlp_model = blank_nlp
                return _nlp_model
            except Exception:
                pass
        except Exception:
            pass

        # 5. Pure Python Resilient Fallback (Guaranteed to NEVER fail)
        _nlp_model = FallbackSpacyPipeline()
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
    
    # Strip solitary trailing unmatched quote
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
    # Step 3, 4, 5: NLP Pipeline Processing (Guaranteed Zero Crashes)
    # -------------------------------------------------------------
    nlp = get_spacy_nlp()
    if nlp is None:
        nlp = FallbackSpacyPipeline()

    try:
        doc = nlp(cleaned_prompt)
    except Exception:
        fallback = FallbackSpacyPipeline()
        doc = fallback(cleaned_prompt)
    
    # Step 3: Tokens, Lemmas, and POS Tags
    tokens: List[str] = [token.text for token in doc]
    lemmas: List[str] = [getattr(token, "lemma_", token.text.lower()) for token in doc]
    pos_tags: List[Dict[str, str]] = [
        {
            "text": token.text,
            "pos": getattr(token, "pos_", "NOUN"),
            "tag": getattr(token, "tag_", "NN")
        }
        for token in doc
    ]
    
    # Step 4: Stop Word Tagging & Filtering
    stop_words: List[str] = [
        token.text for token in doc
        if getattr(token, "is_stop", False) and not getattr(token, "is_punct", False) and not getattr(token, "is_space", False)
    ]
    non_stop_tokens: List[str] = [
        token.text for token in doc
        if not getattr(token, "is_stop", False) and not getattr(token, "is_punct", False) and not getattr(token, "is_space", False)
    ]
    
    # Step 5: Sentence Segmentation
    sentences: List[str] = []
    if hasattr(doc, "sents"):
        sentences = [
            sent.text.strip() for sent in doc.sents if sent.text.strip()
        ]
    if not sentences and cleaned_prompt:
        sentences = [cleaned_prompt]
    
    # Words (excluding punctuation and whitespace)
    words: List[str] = [
        token.text for token in doc
        if not getattr(token, "is_punct", False) and not getattr(token, "is_space", False)
    ]
    if not words and cleaned_prompt:
        words = cleaned_prompt.split()
    
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
