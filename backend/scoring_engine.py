"""
PromptCraft Scoring Engine
--------------------------
Calculates aggregated quantitative scores across the 7 evaluation parameters
using the Tiered Weighted Scoring Model:
- Tier 1 (40%): Specificity (2.0x = 20 pts) + Completeness (2.0x = 20 pts)
- Tier 2 (30%): Constraints (1.5x = 15 pts) + Context (1.5x = 15 pts)
- Tier 3 (30%): Ambiguity (1.0x = 10 pts) + Readability (1.0x = 10 pts) + Grammar (1.0x = 10 pts)

Formula:
  Overall Score = sum(raw_score_i * weight_i)  [Direct 0 to 100 Scale]
"""

from typing import Dict, Any, List
from config.settings import (
    EVALUATION_PARAMETERS,
    PARAMETER_METADATA,
    PARAMETER_WEIGHTS,
    TOTAL_MAX_RAW_SCORE,
    TOTAL_WEIGHTED_MAX_SCORE,
    get_quality_tier
)


def calculate_overall_scores(parameter_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes aggregated raw score, weighted 0-100 score, quality tier,
    and strengths/weaknesses breakdown from individual analyzer results.
    
    Args:
        parameter_results: Dictionary mapping parameter names to their analyzer result dicts.
        
    Returns:
        Structured scoring summary dictionary with weighted contributions.
    """
    total_raw_score: float = 0.0
    total_weighted_score: float = 0.0
    breakdown: Dict[str, Dict[str, Any]] = {}
    strengths: List[Dict[str, Any]] = []
    moderate_areas: List[Dict[str, Any]] = []
    weaknesses: List[Dict[str, Any]] = []
    
    for param in EVALUATION_PARAMETERS:
        res = parameter_results.get(param, {})
        raw_score = float(res.get("score", 0.0))
        max_score = float(res.get("max_score", 10.0))
        status = res.get("status", "Weak")
        meta = PARAMETER_METADATA.get(param, {})
        label = meta.get("label", param.capitalize())
        icon = meta.get("icon", "📌")
        meta_weight = meta.get("weight", 1.0) if isinstance(meta, dict) else 1.0
        param_weight = PARAMETER_WEIGHTS.get(param)
        weight = float(param_weight if param_weight is not None else meta_weight)
        tier_label = meta.get("tier", "Standard")
        
        # Clamp raw score between 0 and max_score
        raw_score = max(0.0, min(max_score, raw_score))
        total_raw_score += raw_score
        
        # Weighted points earned (e.g. 8.0 raw * 2.0 weight = 16.0 weighted points)
        weighted_points = round(raw_score * weight, 1)
        max_weighted_points = round(max_score * weight, 1)
        total_weighted_score += weighted_points
        
        item_summary = {
            "parameter": param,
            "label": label,
            "icon": icon,
            "tier": tier_label,
            "score": round(raw_score, 1) if raw_score % 1 != 0 else int(raw_score),
            "max_score": int(max_score),
            "weight": weight,
            "weighted_points": weighted_points,
            "max_weighted_points": max_weighted_points,
            "percentage": round((raw_score / max_score) * 100, 1),
            "status": status,
            "feedback": res.get("feedback", ""),
            "details": res
        }
        breakdown[param] = item_summary
        
        # Categorize into Strengths vs Areas for Improvement (based on local 0-10 score)
        if raw_score >= 8.0:
            strengths.append(item_summary)
        elif raw_score >= 5.0:
            moderate_areas.append(item_summary)
        else:
            weaknesses.append(item_summary)
            
    # Compute final overall score (0 to 100 direct weighted scale)
    overall_score = int(round(total_weighted_score))
    overall_score = max(0, min(100, overall_score))
    
    # Retrieve Quality Tier metadata
    tier_info = get_quality_tier(overall_score)
    
    return {
        "overall_score": overall_score,
        "total_weighted_score": round(total_weighted_score, 1),
        "total_max_weighted_score": TOTAL_WEIGHTED_MAX_SCORE,
        "total_raw_score": round(total_raw_score, 1),
        "total_max_raw_score": TOTAL_MAX_RAW_SCORE,
        "quality_tier": tier_info["tier"],
        "badge": tier_info["badge"],
        "color": tier_info["color"],
        "description": tier_info["description"],
        "breakdown": breakdown,
        "strengths": strengths,
        "moderate_areas": moderate_areas,
        "weaknesses": weaknesses,
        "parameter_order": EVALUATION_PARAMETERS
    }
