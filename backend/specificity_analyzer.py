"""
PromptCraft Specificity Analyzer
--------------------------------
Evaluates prompt micro-level technical depth, granularity, and precision
across 5 distinct technical indicators using spaCy NLP and pattern analysis:

1. Granular Subtopic Focus (Specific sub-mechanisms or domain components)
2. Target Audience Calibration (Explicit calibration of reader expertise)
3. Technical Depth Level (Explicit technical depth modifier)
4. Concrete Examples / Test Cases Requested (Explicit sample payloads or code test cases)
5. Named Technical Entities & Parameters (Specific versions, protocols, libraries, or numbers)

Scoring Logic (Orthogonal - Zero Overlap with Formats/Limits):
- Exactly 2.0 points per satisfied indicator (Max: 10/10).
"""

import re
from typing import Dict, Any, Optional

INDICATOR_NAMES = {
    "subtopic_focus": "Specific Topics / Subtopics",
    "audience_calibration": "Audience Skill Level",
    "technical_depth": "Depth Level (e.g. beginner vs deep-dive)",
    "concrete_examples": "Real Examples / Test Cases",
    "named_entities_params": "Exact Names, Numbers & Tools"
}

# Regex Patterns for Specificity Indicators
SPECIFICITY_PATTERNS = {
    "subtopic_focus": re.compile(
        r"\b(specifically|focusing\s+on|such\s+as|including|include|covering|aspects?\s+of|"
        r"details?\s+of|regarding|in\s+terms\s+of|related\s+to|subtopic|particular\s+focus|"
        r"mention|mentioning|state|stating|mechanism\s+of|internals?\s+of|architecture\s+of|"
        r"explain\s+the|detail\s+the|explore\s+the|examine\s+the|cover\s+the|break\s+down\s+the|highlight\s+the|roles?\s+of|mechanics?\s+of|phases?\s+of)\b",
        re.IGNORECASE
    ),
    "audience_calibration": re.compile(
        r"\b((to|for)\s+(my\s+|our\s+|the\s+|a\s+|an\s+)?([a-z\-]+\s+)?(professor|teacher|instructor|faculty|dean|"
        r"manager|boss|supervisor|director|client|customer|colleague|classmate|student|beginner|expert|developer|"
        r"child|5-year-old|kid|audience|reader|patient|layman|novice|professional|senior|undergraduate|postgraduate|non-technical|"
        r"curious\s+beginner|curious\s+learner|friend|traveler|tourist|candidate|shopper|user|consumer|stakeholder|scholar|enthusiast|participant|practitioner)s?)\b|"
        r"\b(target\s+audience|aimed\s+at|intended\s+for|tailored\s+for|calibrated\s+for)\b",
        re.IGNORECASE
    ),
    "technical_depth": re.compile(
        r"\b(step-by-step|step\s+by\s+step|in-depth|in\s+depth|deep\s+dive|high-level|"
        r"comprehensive|thorough|rigorous|first-principles|from\s+first\s+principles|"
        r"from\s+scratch|low-level|architectural\s+overview|granular|detailed\s+walkthrough|"
        r"formal|structured|clear\s+subject\s+line|complete\s+details?|"
        r"chronological|day-by-day|step-by-step\s+mechanics|underlying\s+(mechanics|principles)|foundational|detailed|action-packed|granular\s+breakdown)\b",
        re.IGNORECASE
    ),
    "concrete_examples": re.compile(
        r"\b(example|examples|sample|samples|case\s+study|case\s+studies|demonstration|"
        r"test\s+case|test\s+cases|sample\s+input|sample\s+output|sample\s+payload|"
        r"code\s+snippet|mock\s+data|realistic\s+scenario|show\s+how|walk\s+through\s+an\s+example|"
        r"concrete\s+([a-z\-]+\s+){0,3}(imagery|descriptions?|dialogue|examples?|details?|itinerar(y|ies)|breakdowns?|recommendations?|metrics?|steps?|use-cases?|scenarios?|data)|"
        r"(vivid\s+)?(everyday\s+)?analog(y|ies)|practical\s+(real-world\s+)?(examples?|use-cases?|applications?|scenarios?)|itemized\s+(expense\s+)?breakdown|daily\s+(breakdown|activities|schedule)|"
        r"assignments?|coursework|lectures?|subject\s+line)\b",
        re.IGNORECASE
    ),
    "named_entities_params": re.compile(
        r"\b(\d+\s*[-–—]?\s*(words?|sentences?|paragraphs?|pages?|lines?|days?|nights?|hours?|weeks?|months?|years?|dollars?|inr|rs\.?|usd|eur|budget)|"
        r"(five|ten|three|two|\d+)\s+years|"
        r"python(\s+\d+(\.\d+)*)?|pandas|numpy|scipy|sql|nosql|mongodb|node(\.js)?|react|fastapi|django|postgres(ql)?|redis|"
        r"docker|kubernetes|aws|gcp|azure|rest\s+api|graphql|oauth\d*|jwt|tls\s*\d+(\.\d+)*|"
        r"json|csv|html|css|markdown|table|chlorophyll|glucose|oxygen|co2|carbon\s+dioxide|"
        r"q[1-4]|chapter\s*\d+|ttl|latency|throughput|p99|sla|big-o|o\([1nlog\s]+\)|\d+\s*(ms|seconds?|minutes?|gb|mb|kb|%))\b",
        re.IGNORECASE
    )
}


def evaluate_specificity_indicators(cleaned_prompt: str, spacy_doc: Optional[Any] = None) -> Dict[str, bool]:
    """
    Evaluates all 5 Specificity Indicators using regex patterns and spaCy linguistic analysis.
    """
    text = cleaned_prompt
    
    indicators: Dict[str, bool] = {
        "subtopic_focus": False,
        "audience_calibration": False,
        "technical_depth": False,
        "concrete_examples": False,
        "named_entities_params": False
    }
    
    # 1. Subtopic Focus
    if SPECIFICITY_PATTERNS["subtopic_focus"].search(text):
        indicators["subtopic_focus"] = True
    elif spacy_doc:
        meaningful_chunks = [c for c in spacy_doc.noun_chunks if not any(t.is_stop for t in c)]
        if len(meaningful_chunks) >= 2:
            indicators["subtopic_focus"] = True
    
    # 2. Audience Calibration
    if SPECIFICITY_PATTERNS["audience_calibration"].search(text):
        indicators["audience_calibration"] = True
    
    # 3. Technical Depth Level
    if SPECIFICITY_PATTERNS["technical_depth"].search(text):
        indicators["technical_depth"] = True
    
    # 4. Concrete Examples / Test Cases
    if SPECIFICITY_PATTERNS["concrete_examples"].search(text):
        indicators["concrete_examples"] = True
    
    # 5. Named Technical Entities & Parameters
    if SPECIFICITY_PATTERNS["named_entities_params"].search(text):
        indicators["named_entities_params"] = True
    elif spacy_doc:
        # Check for named entities (GPE location, DATE duration, CARDINAL numbers, PERSON, ORG)
        entities = [ent for ent in spacy_doc.ents if ent.label_ in ("GPE", "DATE", "CARDINAL", "PERSON", "ORG", "LOC")]
        proper_nouns = [t.text for t in spacy_doc if t.pos_ == "PROPN" and not t.is_stop]
        if entities or proper_nouns:
            indicators["named_entities_params"] = True
    
    return indicators


def analyze_specificity(prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes prompt specificity and assigns a 0 to 10 score (2 points per satisfied indicator).
    
    Args:
        prompt_data: Preprocessed dictionary containing 'cleaned_prompt' and optionally 'spacy_doc'
        
    Returns:
        Structured evaluation dictionary for the Specificity parameter.
    """
    text = prompt_data.get("cleaned_prompt", "")
    if not text:
        return {
            "parameter": "specificity",
            "score": 0,
            "max_score": 10,
            "status": "Weak",
            "detected_count": 0,
            "features_detected": {k: False for k in INDICATOR_NAMES},
            "detected_list": [],
            "missing_list": list(INDICATOR_NAMES.values()),
            "feedback": "No prompt text provided to evaluate."
        }
    
    spacy_doc = prompt_data.get("spacy_doc")
    features_detected = evaluate_specificity_indicators(text, spacy_doc)
    
    # Count satisfied indicators (2 points each -> Max 10)
    detected_count = sum(1 for detected in features_detected.values() if detected)
    score = min(10, detected_count * 2)
    
    detected_list = [INDICATOR_NAMES[k] for k, v in features_detected.items() if v]
    missing_list = [INDICATOR_NAMES[k] for k, v in features_detected.items() if not v]
    
    # Determine status & feedback (Cause only)
    if score >= 8:
        status = "Strong"
        feedback = f"Prompt is highly specific ({detected_count}/5 details): covers specific subtopics, audience level, depth, and concrete examples."
    elif score >= 5:
        status = "Moderate"
        feedback = f"Prompt is only moderately detailed ({detected_count}/5 details). Missing: {', '.join(missing_list)}."
    else:
        status = "Weak"
        feedback = f"Prompt is too broad and general ({detected_count}/5 details). Missing: {', '.join(missing_list)}."
    
    return {
        "parameter": "specificity",
        "score": score,
        "max_score": 10,
        "status": status,
        "detected_count": detected_count,
        "features_detected": features_detected,
        "detected_list": detected_list,
        "missing_list": missing_list,
        "feedback": feedback
    }
