"""
PromptCraft Context Analyzer
----------------------------
Evaluates prompt background and domain context across 5 distinct categories
using regex pattern matching and spaCy linguistic analysis.

Scoring Logic:
- Exactly 2 points per detected context category (Max: 10/10).
- 5 categories checked:
  1. Background Information
  2. Purpose / Goal
  3. User / Audience Context
  4. Domain / Subject Environment
  5. Practical Situation / Use-Case
"""

import re
from typing import Dict, Any, Optional

CATEGORY_NAMES = {
    "background_info": "Project / Situation Background",
    "purpose_goal": "Goal / Why This Is Needed",
    "audience_context": "Target Audience (who it is for)",
    "domain_context": "Field / Subject Area",
    "situation_usecase": "Real-World Use Case"
}

# Regex Patterns for the 5 Context Categories
CONTEXT_PATTERNS = {
    "background_info": re.compile(
        r"\b(for\s+(a\s+|an\s+)?([a-z\-]+\s+){0,3}(vacation|trip|group\s+trip|holiday|leave|absence|wedding|event|conference|sickness|illness|emergency|exam|test|preparation|project|migration|lesson|study|initiative|campaign)|"
        r"due\s+to|because\s+of|reason\s+(is|being)|as\s+i\s+(will\s+be|am)|since\s+(i|we)|"
        r"solutions\s+to\s+climate\s+change|climate\s+change|global\s+warming|environmental\s+impact|energy\s+source|clean\s+energy|"
        r"biological\s+process|mechanics\s+of|concept\s+of|principles\s+of|"
        r"to\s+(write|build|design|create|structure|conduct|implement|craft|draft|develop|produce|analyze|extract|provide)\s+(a|an)\s+[^.;\n]+?\s+(implementation|itinerary|guide|critique|session|workflow|campaign|narrative|system|application|plan|script|endpoint|api|pipeline|solution|analysis|scene|letter|message|email|module)\b|"
        r"grounded\s+in\s+(the\s+)?(uploaded|provided)?\s*(reference|guidelines?|specifications?)|"
        r"based\s+on\s+(this|these|the)\s+(requirements|specifications?|premise|details?|travel\s+itinerary|travel\s+plan|scenario|guidelines?|campaign|analytical|simulation)|"
        r"following\s+(these|the)\s+(technical\s+)?(specifications?|guidelines?|criteria|standards?)|"
        r"i\s+am\s+(working\s+on|building|developing|studying|learning|designing|writing|traveling|taking|preparing)|"
        r"we\s+(currently\s+have|are\s+building|are\s+developing|use|have|need)|"
        r"given\s+that|as\s+background|our\s+([a-z\-]+\s+){0,3}project|in\s+our\s+([a-z\-]+\s+){0,3}(codebase|team|organization|project|classroom|system|group)|"
        r"the\s+current\s+system|recently|we\s+noticed|my\s+team\s+is|"
        r"i\s+have\s+a\s+dataset|we\s+run\s+a|i\s+am\s+a\s+(student|developer|engineer|teacher|manager|mentor|assistant|researcher))\b",
        re.IGNORECASE
    ),
    "purpose_goal": re.compile(
        r"\b(requesting|to\s+request|applying\s+for|to\s+apply|to\s+ask|seeking|asking\s+for|"
        r"in\s+order\s+to|so\s+that|with\s+the\s+goal\s+of|our\s+objective\s+is|"
        r"solutions\s+to|as\s+solutions\s+to|to\s+solve|to\s+mitigate|to\s+recommend|recommending\s+which|"
        r"aiming\s+to|to\s+achieve|for\s+the\s+purpose\s+of|the\s+intention\s+is|"
        r"to\s+ensure\s+that|to\s+help\s+(me|us|them)|the\s+aim\s+is|to\s+prevent|"
        r"so\s+i\s+can|so\s+we\s+can|to\s+improve|to\s+catch\s+up|to\s+submit|to\s+notify|to\s+inform|to\s+evaluate|to\s+prepare|"
        r"showing\s+why|essential\s+for|to\s+explain|to\s+explore|to\s+understand|to\s+maximize|to\s+guide)\b",
        re.IGNORECASE
    ),
    "audience_context": re.compile(
        r"\b((to|for)\s+(my\s+|our\s+|the\s+|a\s+|an\s+)?([a-z\-]+\s+)?(professor|teacher|instructor|faculty|dean|principal|"
        r"clients?|customers?|consumers?|shoppers?|candidates?|scholars?|users?|stakeholders?|executives?|managers?|boss|supervisor|"
        r"patients?|students?|beginners?|developers?|engineers?|readers?|children|kids?|"
        r"non-technical|board\s+members?|investors?|employees?|directors?|classmates?|colleagues?|teams?|"
        r"curious\s+beginners?|curious\s+learners?|friends?|travelers?|tourists?|participants?|enthusiasts?|practitioners?|"
        r"urban\s+areas?|rural\s+communities?|industrial\s+regions?|policy\s*makers?|researchers?))\b|"
        r"\b(target\s+audience|intended\s+for|read\s+by|presented\s+to|tailored\s+for|addressed\s+to)\b",
        re.IGNORECASE
    ),
    "domain_context": re.compile(
        r"\b(professor|lectures?|assignments?|coursework|syllabus|academic|education|university|college|school|faculty|exam|semester|"
        r"environment|environmental|climate(\s+change)?|energy|renewable|solar|wind|hydropower|sustainability|clean\s+tech|ecology|conservation|"
        r"plants?|biology|biological|photosynthesis|ecosystems?|nature|science|"
        r"travel|tourism|itinerary|vacation|trip|hotel|hotels|hospitality|logistics|"
        r"healthcare|medical|hospital|clinical|fintech|banking|financial|investment|"
        r"cloud|aws|azure|gcp|devops|kubernetes|docker|cybersecurity|security|infosec|"
        r"software|programming|database|machine\s+learning|artificial\s+intelligence|data\s+science|data\s+analytics|analytics|statistics|backend|"
        r"literature|fiction|creative\s+writing|creative\s+arts|storytelling|"
        r"marketing|advertising|branding|market\s+research|sales|copywriting|recruitment|coaching|interview\s+prep|"
        r"e-commerce|ecommerce|retail|legal|law|compliance|gdpr|hipaa|"
        r"k-12|automotive|manufacturing|telecom|real\s+estate|biotech|workplace|corporate)\b",
        re.IGNORECASE
    ),
    "situation_usecase": re.compile(
        r"\b(leave(\s+of\s+absence)?|vacation|family\s+vacation|trip|group\s+trip|travel|holiday|absence|sick\s+leave|medical\s+leave|"
        r"for\s+an?\s+(upcoming\s+)?([a-z\-]+\s+)?(meeting|presentation|interview|exam|examinations?|test|audit|"
        r"demo|pitch|release|deployment|outage|incident|sprint\s+review|onboarding|review|migration|comparison|analysis|study))\b|"
        r"\b(comparative\s+analysis|case\s+study|product\s+launch|campaign|for\s+(urban\s+areas|rural\s+communities|industrial\s+regions)|"
        r"in\s+production|production-ready|in\s+a\s+live\s+environment|during\s+an\s+incident|for\s+semester\s+examinations|"
        r"for\s+(educational\s+institutions|enterprises?|organizations?|startups?)|"
        r"for\s+a\s+job\s+interview|to\s+resolve\s+a\s+(ticket|bug|issue)|real-world\s+(scenarios?|industry\s+examples|use\s+cases?|study|launch|ecosystems?|applications?|settings?)|daily\s+activities|day-to-day)\b",
        re.IGNORECASE
    )
}


def evaluate_context_categories(cleaned_prompt: str, spacy_doc: Optional[Any] = None) -> Dict[str, bool]:
    """
    Evaluates the presence of 5 Context Categories in the prompt.
    """
    text = cleaned_prompt
    
    detected: Dict[str, bool] = {
        "background_info": False,
        "purpose_goal": False,
        "audience_context": False,
        "domain_context": False,
        "situation_usecase": False
    }
    
    # Check regex patterns
    for category_key, pattern in CONTEXT_PATTERNS.items():
        if pattern.search(text):
            detected[category_key] = True
    
    # Additional spaCy Named Entity / Dependency context signals
    if spacy_doc:
        entities = {ent.label_ for ent in spacy_doc.ents}
        # Organization, Law, or Product entities reinforce domain context
        if any(label in entities for label in ("ORG", "LAW", "PRODUCT", "MONEY")):
            detected["domain_context"] = True
    
    return detected


def analyze_context(prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes prompt context and assigns a 0 to 10 score (2 points per category).
    
    Args:
        prompt_data: Preprocessed dictionary containing 'cleaned_prompt' and optionally 'spacy_doc'
        
    Returns:
        Structured evaluation dictionary for the Context parameter.
    """
    text = prompt_data.get("cleaned_prompt", "")
    if not text:
        return {
            "parameter": "context",
            "score": 0,
            "max_score": 10,
            "status": "Weak",
            "detected_count": 0,
            "features_detected": {k: False for k in CATEGORY_NAMES},
            "detected_list": [],
            "missing_list": list(CATEGORY_NAMES.values()),
            "feedback": "No prompt text provided to evaluate."
        }
    
    spacy_doc = prompt_data.get("spacy_doc")
    features_detected = evaluate_context_categories(text, spacy_doc)
    
    detected_count = sum(1 for v in features_detected.values() if v)
    score = min(10, detected_count * 2)
    
    detected_list = [CATEGORY_NAMES[k] for k, v in features_detected.items() if v]
    missing_list = [CATEGORY_NAMES[k] for k, v in features_detected.items() if not v]
    
    # Determine status & feedback (Cause only)
    if score >= 8:
        status = "Strong"
        feedback = f"Prompt provides rich background context ({detected_count}/5 details): situation, audience, domain, and objective."
    elif score >= 5:
        status = "Moderate"
        feedback = f"Prompt has limited background context ({detected_count}/5 details). Missing: {', '.join(missing_list)}."
    else:
        status = "Weak"
        feedback = f"Prompt lacks background information ({detected_count}/5 details). Missing: {', '.join(missing_list)}."
    
    return {
        "parameter": "context",
        "score": score,
        "max_score": 10,
        "status": status,
        "detected_count": detected_count,
        "features_detected": features_detected,
        "detected_list": detected_list,
        "missing_list": missing_list,
        "feedback": feedback
    }
