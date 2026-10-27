"""
PromptCraft Constraints Analyzer
--------------------------------
Evaluates whether a prompt imposes operational rules, boundaries, and negative
constraints across 5 key constraint dimensions.

Scoring Logic:
- Exactly 2 points per detected constraint type (Max: 10/10).
- 5 Constraint Types checked:
  1. Length / Word / Size Limits
  2. Format / Structural Constraints
  3. Tone / Style / Persona Rules
  4. Audience & Complexity Bounds
  5. Negative Constraints & Exclusions
"""

import re
from typing import Dict, Any, Optional

CONSTRAINT_NAMES = {
    "length_size": "Length / Word Limit",
    "format_structure": "Output Format (e.g. table, bullet points)",
    "tone_style": "Tone / Writing Style",
    "audience_level": "Audience Skill Level",
    "negative_exclusions": "What to Avoid (e.g., 'do not use...')"
}

# Regex Patterns for Constraint Types
CONSTRAINT_PATTERNS = {
    "length_size": re.compile(
        r"\b(\d+\s*[-–—]\s*words?|\d+\s+words?|\d+\s*[-–—]\s*(sentences?|paragraphs?|pages?|lines?|days?)|"
        r"under\s+\d+\s+(words?|lines?|paragraphs?|pages?)|"
        r"within\s+\d+\s+(words?|lines?|paragraphs?|pages?)|"
        r"maximum\s+of\s+\d+|max\s+\d+\s+(words?|lines?)|limit\s+(to|it\s+to)\s+\d+|"
        r"between\s+\d+\s+and\s+\d+\s+words?|\d+\s*[-–—]\s*\d+\s*words?|"
        r"at\s+least\s+\d+\s+words?|at\s+most\s+\d+\s+words?|"
        r"single\s+(paragraph|page|sentence)|one\s+paragraph|no\s+more\s+than\s+\d+\s+words?|"
        r"around\s+\d+\s+words?|approximately\s+\d+\s+words?|brief|short|concise)\b",
        re.IGNORECASE
    ),
    "format_structure": re.compile(
        r"\b(email|subject\s+line|formal\s+email|letter|memo|application|cover\s+letter|essay|report|"
        r"article|summary|outline|checklist|story|short\s+story|narrative(\s+sections?)?|scene|dialogue|script|screenplay|"
        r"copy|campaign|announcement|synthesis|critique|scenario|roleplay|"
        r"markdown\s+table|table|bullet\s+points?|bulleted\s+list|itinerar(y|ies)|breakdown|guide|"
        r"json(\s+object)?|numbered\s+list|python\s+function|csv|schema|chart|diagram|"
        r"markdown|latex|html|valid\s+json\s+only|strictly\s+json|follow\s+this\s+structure|output\s+format\s*:)\b",
        re.IGNORECASE
    ),
    "tone_style": re.compile(
        r"\b(formal|polite|professional|academic|objective|respectful|courteous|empathetic|"
        r"casual|friendly|authoritative|humorous|concise|direct|persuasive|technical|neutral|informal|"
        r"write\s+in\s+(first|third)\s+person|use\s+active\s+voice)\b",
        re.IGNORECASE
    ),
    "audience_level": re.compile(
        r"\b((to|for)\s+(my\s+|our\s+|the\s+|a\s+|an\s+)?([a-z\-]+\s+)?(professor|teacher|instructor|faculty|dean|"
        r"manager|boss|supervisor|director|client|customer|colleague|classmate|student|beginner|expert|developer|"
        r"analyst|engineer|decision-maker|data\s+scientist|user|consumer|candidate|scholar|"
        r"child|kid|non-technical|layman|novice|executive|undergraduate|postgraduate|reader|audience|"
        r"curious\s+beginner|curious\s+learner|friend|traveler|tourist|participant|enthusiast|"
        r"urban\s+areas?|rural\s+communities?|industrial\s+regions?|policy\s*makers?|researchers?)s?)\b|"
        r"\b(avoid\s+(all\s+)?jargon|plain\s+english|accessible\s+to|no\s+technical\s+jargon|"
        r"introductory\s+level|advanced\s+level|high\s+school\s+level)\b",
        re.IGNORECASE
    ),
    "negative_exclusions": re.compile(
        r"\b(distinguish\s+verified\s+facts|identify\s+any\s+unavailable|verified\s+facts\s+from\s+estimates|"
        r"published\s+within\s+the\s+last|reliable\s+sources\s+published|"
        r"do\s+not\s+(use|include|write|generate|mention|rely\s+on)|don'?t\s+(use|include|write|mention)|"
        r"without\s+(using|external\s+libraries|boilerplate|placeholders|hallucinating|mentioning|generic|unverified|dense|filler|jargon)|"
        r"exclude|excluding|never\s+(use|include)|no\s+(boilerplate|placeholders|external\s+imports|slang|jargon|fluff)|"
        r"only\s+(use|using)\s+standard\s+library|strictly\s+avoid|do\s+not\s+assume|"
        r"avoid\s+(all\s+|overly\s+)?(dense\s+)?(jargon|fluff|unverified|generic|filler|bias|claims?))\b",
        re.IGNORECASE
    )
}


def evaluate_constraints(cleaned_prompt: str, spacy_doc: Optional[Any] = None) -> Dict[str, bool]:
    """
    Evaluates the presence of 5 Constraint Types in the prompt.
    """
    text = cleaned_prompt
    
    detected: Dict[str, bool] = {
        "length_size": False,
        "format_structure": False,
        "tone_style": False,
        "audience_level": False,
        "negative_exclusions": False
    }
    
    for constraint_key, pattern in CONSTRAINT_PATTERNS.items():
        if pattern.search(text):
            detected[constraint_key] = True
            
    return detected


def analyze_constraints(prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes prompt constraints and assigns a 0 to 10 score (2 points per constraint type).
    
    Args:
        prompt_data: Preprocessed dictionary containing 'cleaned_prompt' and optionally 'spacy_doc'
        
    Returns:
        Structured evaluation dictionary for the Constraints parameter.
    """
    text = prompt_data.get("cleaned_prompt", "")
    if not text:
        return {
            "parameter": "constraints",
            "score": 0,
            "max_score": 10,
            "status": "Weak",
            "detected_count": 0,
            "features_detected": {k: False for k in CONSTRAINT_NAMES},
            "detected_list": [],
            "missing_list": list(CONSTRAINT_NAMES.values()),
            "feedback": "No prompt text provided to evaluate."
        }
    
    spacy_doc = prompt_data.get("spacy_doc")
    features_detected = evaluate_constraints(text, spacy_doc)
    
    detected_count = sum(1 for v in features_detected.values() if v)
    score = min(10, detected_count * 2)
    
    detected_list = [CONSTRAINT_NAMES[k] for k, v in features_detected.items() if v]
    missing_list = [CONSTRAINT_NAMES[k] for k, v in features_detected.items() if not v]
    
    # Determine status & feedback (Cause only)
    if score >= 8:
        status = "Strong"
        feedback = f"Prompt defines strict operational limits ({detected_count}/5 rules): format, tone, length, and negative exclusions."
    elif score >= 5:
        status = "Moderate"
        feedback = f"Prompt has limited operational limits ({detected_count}/5 rules). Missing: {', '.join(missing_list)}."
    else:
        status = "Weak"
        feedback = f"Prompt provides no rules, word count limits, formatting structure, or negative exclusions ({detected_count}/5 rules)."
    
    return {
        "parameter": "constraints",
        "score": score,
        "max_score": 10,
        "status": status,
        "detected_count": detected_count,
        "features_detected": features_detected,
        "detected_list": detected_list,
        "missing_list": missing_list,
        "feedback": feedback
    }
