"""
PromptCraft Completeness Analyzer
---------------------------------
Evaluates whether a prompt contains the 5 fundamental macro-structural pillars
of a complete, self-contained prompt brief (aligned with the CO-STAR and CRISPE frameworks):

1. Assigned AI Role / Persona (e.g. "Act as a Senior Database Architect...")
2. Core Task Directive (e.g. "Design", "Refactor", "Analyze", "Implement", "Draft"...)
3. Input Data / Reference Anchor (e.g. "Given the following schema...", "Based on the attached logs...")
4. Target Deliverable Definition (e.g. "Create a migration plan", "Provide a root-cause report", "Write unit tests"...)
5. Success Criteria / Acceptance Standard (e.g. "Ensure zero regression", "Optimized for latency", "Aligned with OWASP Top 10"...)

Scoring Logic (Orthogonal - Zero Overlap with Formats/Limits):
- Exactly 2.0 points per detected macro-structural pillar (Max: 10/10).
"""

import re
from typing import Dict, Any, Optional

PILLAR_NAMES = {
    "assigned_role": "AI Role (who to act as)",
    "task_directive": "Main Task (what to do)",
    "input_reference": "Input Info (reference data/details)",
    "target_deliverable": "Expected Output (final format)",
    "success_criteria": "Goal / Success Criteria"
}

# Regex Patterns for Macro-Structural Prompt Pillars
PILLAR_PATTERNS = {
    "assigned_role": re.compile(
        r"\b(act\s+as\s+(a\s+|an\s+)?([a-z0-9\-\.]+\s+){0,8}(developer|engineer|architect|auditor|expert|"
        r"consultant|specialist|analyst|tutor|teacher|copywriter|designer|manager|scientist|researcher|student|assistant|"
        r"mentor|coach|strategist|educator|instructor|professor|writer|author|storyteller|novelist|counselor|advisor|reviewer|interviewer|"
        r"planner|coordinator|communicator|creator|producer|director|practitioner|evaluator|operator|trainer|facilitator|guide)|"
        r"you\s+are\s+(a\s+|an\s+)?([a-z0-9\-\.]+\s+){0,8}(senior|staff|principal|lead|expert|experienced|specialist|architect|engineer|developer|assistant|mentor|educator|author|writer|planner|coordinator|strategist|consultant)|"
        r"as\s+(a\s+|an\s+)?([a-z0-9\-\.]+\s+){0,8}(expert|specialist|veteran|professional|architect|engineer|student|mentor|educator|author|writer|planner|coordinator|strategist|consultant)|"
        r"i\s+am\s+(a\s+|an\s+)?(student|developer|engineer|employee|client|teacher|researcher|traveler|learner|user))\b",
        re.IGNORECASE
    ),
    "task_directive": re.compile(
        r"\b(write|create|draft|explain|analyze|summarize|build|implement|calculate|"
        r"generate|extract|compare|describe|list|solve|evaluate|develop|design|outline|"
        r"classify|translate|debug|optimize|rephrase|review|compose|construct|refactor|benchmark|request|requesting|conduct|simulate|"
        r"plan|schedule|recommend|structure|formulate|prioritize|coordinate|audit)\b",
        re.IGNORECASE
    ),
    "input_reference": re.compile(
        r"\b(given\s+(the\s+following|this|these|our|my)|based\s+on\s+(the|this|these|our|attached|provided|this\s+premise|all\s+available)|"
        r"here\s+is\s+(the|our|my)|refer\s+to\s+(the|this)|using\s+(the\s+following|this\s+data|the\s+provided)|"
        r"input\s*:\s*|context\s*:\s*|sample\s+data\s*:|the\s+provided\s+(code|text|document|schema|logs?|table)|"
        r"for\s+(a\s+|an\s+)?([a-z\-]+\s+){0,3}(vacation|trip|group\s+trip|holiday|leave|absence|wedding|event|conference|sickness|illness|emergency|project|examination|exam|syllabus|curriculum|initiative|campaign|study|workflow|process)|"
        r"regarding|details?\s+of|in\s+[A-Z][a-z]+|for\s+\d+\s+(days?|weeks?|months?|subjects?|hours?))\b",
        re.IGNORECASE
    ),
    "target_deliverable": re.compile(
        r"\b(email|leave\s+(application|request)|letter|memo|essay|report|article|summary|outline|checklist|"
        r"story|short\s+story|narrative|scene|dialogue|script|screenplay|"
        r"migration\s+plan|root-cause\s+(analysis|report)|troubleshooting\s+guide|"
        r"study\s+plan|study\s+schedule|timetable|curriculum|syllabus|schedule|day-wise\s+table|"
        r"itinerary|day-by-day\s+itinerary|travel\s+plan|budget\s+plan|workflow|lesson\s+plan|action\s+items?|explanation|"
        r"comparison(\s+table)?|table|overview|guide|breakdown|"
        r"unit\s+test(\s+suite)?|code\s+implementation|architecture\s+document|"
        r"executive\s+summary|technical\s+specification|step-by-step\s+guide|pull\s+request|"
        r"comprehensive\s+report|action\s+plan|post-mortem|recommendations?\s+list|"
        r"copy|campaign|announcement|synthesis|critique|scenario|roleplay|"
        r"(\d+|three|two|multiple)?\s*(modular\s+)?files|complete\s+codebase|(desktop\s+)?application|source\s+code|message|response)\b",
        re.IGNORECASE
    ),
    "success_criteria": re.compile(
        r"\b(ensure\s+(the\s+|an?\s+)?(robust|that|zero|no|high|low|proper|clean|correct|seamless|compelling|powerful|clear|authentic|formal|accurate|effective|comprehensive|thorough|actionable|reliable|optimal|practical|accessible|structured|smooth|successful|engaging|production-ready)|"
        r"optimized\s+for|aligned\s+with|must\s+achieve|satisfying\s+(the|these)|criteria\s*:|success\s+metric\s*:|"
        r"zero\s+regression|production-ready|compliant\s+with|within\s+latency\s+budget|"
        r"proper\s+(exception|error)\s+handling|(to|and|in\s+order\s+to)\s+prevent\s+(errors?|downtime|vulnerabilities?|misinterpretation|churn|bias|mistakes|flaws|delays|unexpected\s+costs?|confusion|failure)|"
        r"maintain\s+backward\s+compatibility|deliver\s+a\s+(powerful|compelling)\s+resolution|compelling\s+resolution|"
        r"maximize\s+(conversion|retention|engagement|efficiency|practical\s+retention|understanding)|clear\s+subject\s+line|on\s+time|catch\s+up|all\s+missed|submit\s+pending|"
        r"showing\s+why|essential\s+for|for\s+optimal\s+results|for\s+practical\s+retention|conceptual\s+mastery)\b",
        re.IGNORECASE
    )
}


def evaluate_completeness_pillars(cleaned_prompt: str, spacy_doc: Optional[Any] = None) -> Dict[str, bool]:
    """
    Evaluates the presence of the 5 Macro-Structural Prompt Pillars.
    """
    text = cleaned_prompt
    
    detected: Dict[str, bool] = {
        "assigned_role": False,
        "task_directive": False,
        "input_reference": False,
        "target_deliverable": False,
        "success_criteria": False
    }
    
    # Check Pillar Regexes
    for pillar_key, pattern in PILLAR_PATTERNS.items():
        if pattern.search(text):
            detected[pillar_key] = True
            
    # Linguistic Fallback for Task Directive via Root Verb
    if not detected["task_directive"] and spacy_doc:
        for token in spacy_doc:
            if token.pos_ == "VERB" and (token.dep_ == "ROOT" or token.tag_ == "VB"):
                detected["task_directive"] = True
                break
                
    return detected


def analyze_completeness(prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes prompt macro-structural completeness and assigns a 0 to 10 score (2 points per pillar).
    
    Args:
        prompt_data: Preprocessed dictionary containing 'cleaned_prompt' and optionally 'spacy_doc'
        
    Returns:
        Structured evaluation dictionary for the Completeness parameter.
    """
    text = prompt_data.get("cleaned_prompt", "")
    if not text:
        return {
            "parameter": "completeness",
            "score": 0,
            "max_score": 10,
            "status": "Weak",
            "detected_count": 0,
            "pillars_detected": {k: False for k in PILLAR_NAMES},
            "detected_list": [],
            "missing_list": list(PILLAR_NAMES.values()),
            "feedback": "No prompt text provided to evaluate."
        }
    
    spacy_doc = prompt_data.get("spacy_doc")
    pillars_detected = evaluate_completeness_pillars(text, spacy_doc)
    
    detected_count = sum(1 for v in pillars_detected.values() if v)
    score = min(10, detected_count * 2)
    
    detected_list = [PILLAR_NAMES[k] for k, v in pillars_detected.items() if v]
    missing_list = [PILLAR_NAMES[k] for k, v in pillars_detected.items() if not v]
    
    # Determine status & feedback (Cause only)
    if score >= 8:
        status = "Strong"
        feedback = f"Prompt includes all core components ({detected_count}/5 parts): role, task, input info, and expected output."
    elif score >= 5:
        status = "Moderate"
        feedback = f"Prompt is partially complete ({detected_count}/5 parts). Missing: {', '.join(missing_list)}."
    else:
        status = "Weak"
        feedback = f"Prompt is missing fundamental components ({detected_count}/5 parts): {', '.join(missing_list)}."
    
    return {
        "parameter": "completeness",
        "score": score,
        "max_score": 10,
        "status": status,
        "detected_count": detected_count,
        "pillars_detected": pillars_detected,
        "detected_list": detected_list,
        "missing_list": missing_list,
        "feedback": feedback
    }
