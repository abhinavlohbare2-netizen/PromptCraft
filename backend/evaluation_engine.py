"""
PromptCraft Master Evaluation Engine
------------------------------------
Orchestrates the entire prompt evaluation pipeline:
1. Executes 6-step text preprocessing
2. Invokes all 7 rule-based/NLP quantitative analyzers
3. Aggregates results via Scoring Engine
4. Assembles the standardized evaluation payload

STRICT BOUNDARY:
This module performs quantitative evaluation ONLY.
LLM-based natural language explanations and prompt rewriting
occur downstream in post-evaluation stages.
"""

import uuid
from datetime import datetime
from typing import Dict, Any

from backend.preprocessing import preprocess_prompt
from backend.grammar_analyzer import analyze_grammar
from backend.readability_analyzer import analyze_readability
from backend.specificity_analyzer import analyze_specificity
from backend.context_analyzer import analyze_context
from backend.completeness_analyzer import analyze_completeness
from backend.ambiguity_analyzer import analyze_ambiguity
from backend.constraints_analyzer import analyze_constraints
from backend.scoring_engine import calculate_overall_scores


def evaluate_prompt(raw_prompt: str, input_method: str = "text") -> Dict[str, Any]:
    """
    Master pipeline entrypoint for evaluating prompt quality.
    
    Args:
        raw_prompt: The unmodified user prompt string.
        input_method: Origin method ("text", "live_voice", "image", "document").
        
    Returns:
        Standardized, comprehensive evaluation report dictionary.
        
    Raises:
        ValueError: If input validation fails (e.g. empty or invalid prompt).
    """
    # Step 1: Preprocess prompt (Steps 0 through 5)
    preprocessed_data = preprocess_prompt(raw_prompt)
    
    # Step 2: Run all 7 quantitative analyzers
    grammar_res = analyze_grammar(preprocessed_data)
    readability_res = analyze_readability(preprocessed_data)
    specificity_res = analyze_specificity(preprocessed_data)
    context_res = analyze_context(preprocessed_data)
    completeness_res = analyze_completeness(preprocessed_data)
    ambiguity_res = analyze_ambiguity(preprocessed_data)
    constraints_res = analyze_constraints(preprocessed_data)
    
    parameter_results = {
        "grammar": grammar_res,
        "readability": readability_res,
        "specificity": specificity_res,
        "context": context_res,
        "completeness": completeness_res,
        "ambiguity": ambiguity_res,
        "constraints": constraints_res
    }
    
    # Step 3: Compute overall aggregated scores and quality tier
    scoring_summary = calculate_overall_scores(parameter_results)
    
    # Step 4: Package the master evaluation payload
    evaluation_id = str(uuid.uuid4())
    timestamp_iso = datetime.now().isoformat()
    
    return {
        "evaluation_id": evaluation_id,
        "timestamp": timestamp_iso,
        "input_method": input_method,
        "original_prompt": preprocessed_data["original_prompt"],
        "cleaned_prompt": preprocessed_data["cleaned_prompt"],
        "overall_score": scoring_summary["overall_score"],
        "quality_tier": scoring_summary["quality_tier"],
        "badge": scoring_summary["badge"],
        "color": scoring_summary["color"],
        "description": scoring_summary["description"],
        "scoring": scoring_summary,
        "parameter_results": parameter_results,
        "statistics": {
            "word_count": preprocessed_data["word_count"],
            "sentence_count": preprocessed_data["sentence_count"],
            "char_count": preprocessed_data["char_count"]
        }
    }
