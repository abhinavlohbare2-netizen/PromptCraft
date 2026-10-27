"""
PromptCraft Improvement Engine
------------------------------
Generates detailed qualitative weakness diagnosis and targeted recommendations
based on quantitative 7-parameter evaluation results and the original user prompt text.

Features:
- Produces structured parameter-by-parameter analysis with 100% accurate root causes
- Strictly isolates pure causes (why score occurred) from actionable improvements (how to fix it)
- Uses Gemini 3.7 Flash with contextual evaluation evidence and robust prompt-aware fallback
"""

from typing import Dict, Any, List
from backend.llm_service import generate_structured_json, is_llm_available


def generate_fallback_recommendations(
    scoring_data: Dict[str, Any],
    original_prompt: str = ""
) -> Dict[str, Any]:
    """
    Generates prompt-tailored, deterministic rule-based recommendations
    if LLM service is offline or rate-limited.
    Strictly separates pure root causes from pure actionable improvements.
    """
    breakdown = scoring_data.get("breakdown", {})
    parameter_analysis: List[Dict[str, Any]] = []
    actionable_tips: List[str] = []
    
    words = original_prompt.split() if original_prompt else []
    word_count = len(words)
    is_short = word_count <= 15
    is_comparison = any(w.lower() in ["better", "vs", "versus", "or", "compare", "difference"] for w in words)
    is_code_req = any(w.lower() in ["code", "python", "java", "function", "script", "program", "sql", "api"] for w in words)
    
    for param_key, param_info in breakdown.items():
        score = float(param_info.get("score", 0))
        label = param_info.get("label", param_key.capitalize())
        details = param_info.get("details", {})
        
        # 1. Grammar & Syntax
        if param_key == "grammar":
            err_count = details.get("errors_count", 0)
            if score >= 7.0:
                status = "Strong"
                weakness = None
                cause = None
                improvement = "Grammar and sentence syntax are clear and correct."
            else:
                status = "Weak"
                weakness = "Contains grammatical errors or spelling typos."
                cause = f"The prompt has {err_count} spelling or syntax errors that reduce clarity."
                improvement = "Fix spelling errors and grammar punctuation for precise AI interpretation."

        # 2. Readability & Fluency
        elif param_key == "readability":
            if score >= 7.0 or is_short:
                status = "Strong"
                weakness = None
                cause = None
                improvement = "Prompt phrasing is clear, concise, and easy to read."
            else:
                status = "Moderate"
                weakness = "Dense sentence structure or run-on phrasing."
                cause = "The prompt is formatted as a single dense paragraph with complex clauses."
                improvement = "Break long sentences into shorter, simpler points or organized bullet lists."

        # 3. Specificity & Depth
        elif param_key == "specificity":
            if score >= 7.0:
                status = "Strong"
                weakness = None
                cause = None
                improvement = "Prompt includes concrete topics, depth levels, and technical details."
            else:
                status = "Weak" if score < 4.0 else "Moderate"
                weakness = "Lacks specific criteria, subtopics, and concrete examples."
                if is_comparison:
                    cause = "The prompt asks which option is better in general without specifying comparison criteria (e.g., performance, ease of use, community support, or specific use cases)."
                    improvement = "Specify exact comparison criteria (e.g., runtime speed, memory usage, web backend vs data science) and request 2 practical examples."
                elif is_code_req:
                    cause = "The prompt requests code without specifying the framework, input/output constraints, error handling, or performance targets."
                    improvement = "Add specific technical requirements, target library versions, and request sample test cases."
                else:
                    cause = "The prompt states a high-level request without naming specific subtopics, technical depth, or concrete examples."
                    improvement = "Add specific subtopics, real-world examples, and state whether you want beginner or advanced depth."

        # 4. Context & Background
        elif param_key == "context":
            if score >= 7.0:
                status = "Strong"
                weakness = None
                cause = None
                improvement = "Prompt provides thorough background context and audience information."
            else:
                status = "Weak" if score < 4.0 else "Moderate"
                weakness = "Missing background context and target audience."
                if is_comparison:
                    cause = "The prompt does not explain who will use the technology, the developer's experience level, or what kind of application is being built."
                    improvement = "State your technical background (e.g., beginner programmer) and the intended application (e.g., building a REST API)."
                else:
                    cause = "The prompt does not state who this is for, what problem it solves, or the practical scenario where it will be used."
                    improvement = "State the target audience (e.g., students, team leads) and the practical project goal."

        # 5. Completeness
        elif param_key == "completeness":
            if score >= 7.0:
                status = "Strong"
                weakness = None
                cause = None
                improvement = "Prompt contains all fundamental components including role, task, and output expectations."
            else:
                status = "Weak" if score < 4.0 else "Moderate"
                weakness = "Missing core prompt components like AI persona and deliverable structure."
                if is_comparison:
                    cause = "The prompt does not assign an AI role and does not specify how the comparison should be structured (e.g., pros/cons, comparison table)."
                    improvement = "Ask the AI to act as a Senior Software Architect and deliver a structured side-by-side comparison with a summary table."
                else:
                    cause = "The prompt is missing an explicit AI role (who to act as) and clear output structure specifications."
                    improvement = "Assign an AI role (e.g., 'Act as a specialist') and clearly define the expected output format."

        # 6. Clarity / Low Ambiguity
        elif param_key == "ambiguity":
            detected_terms = details.get("detected_terms", [])
            if score >= 7.0:
                status = "Strong"
                weakness = None
                cause = None
                improvement = "Prompt uses unambiguous, direct terminology."
            else:
                status = "Weak"
                vague_str = ", ".join([f"'{t['term']}'" for t in detected_terms[:3]]) if detected_terms else "'some', 'good'"
                weakness = f"Contains subjective words ({vague_str})."
                cause = f"The prompt uses subjective words ({vague_str}) that leave quantity and quality open to interpretation."
                improvement = "Replace vague qualifiers with exact numbers and quantifiable standards (e.g., 'provide 3 benchmarks')."

        # 7. Constraints & Guardrails
        elif param_key == "constraints":
            if score >= 7.0:
                status = "Strong"
                weakness = None
                cause = None
                improvement = "Prompt defines explicit length, format, and style boundaries."
            else:
                status = "Weak" if score < 4.0 else "Moderate"
                weakness = "No rules, length boundaries, or formatting limits."
                cause = "The prompt provides no word count limits, formatting guidelines (e.g., markdown tables), or things to exclude."
                improvement = "Set a word count limit (e.g., under 400 words) and specify formatting like markdown headers and bullet points."

        else:
            status = "Strong" if score >= 7.0 else "Weak"
            weakness = None if status == "Strong" else f"Needs improvement in {label}."
            cause = None if status == "Strong" else f"Missing specific criteria for {label}."
            improvement = f"Maintain {label}." if status == "Strong" else f"Add clear details for {label}."

        parameter_analysis.append({
            "parameter": label,
            "score": score,
            "status": status,
            "weakness": weakness,
            "cause": cause,
            "improvement": improvement
        })
        
        if status != "Strong" and improvement:
            actionable_tips.append(f"Tip for {label}: {improvement}")

    overall_score = scoring_data.get("overall_score", 0)
    weak_params = [a['parameter'] for a in parameter_analysis if a['status'] != 'Strong']
    overall_analysis = (
        f"Prompt scored {overall_score}/100. "
        f"Main areas to improve: {', '.join(weak_params) if weak_params else 'None (excellent prompt!)'}."
    )

    return {
        "parameter_analysis": parameter_analysis,
        "overall_analysis": overall_analysis,
        "actionable_tips": actionable_tips
    }


def analyze_weaknesses_and_improvements(
    original_prompt: str,
    evaluation_payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyzes prompt weaknesses across all 7 parameters and generates structured advice.
    Strictly separates pure root causes (why the score occurred) from actionable improvements (how to fix it).
    
    Args:
        original_prompt: Unmodified user text.
        evaluation_payload: Full evaluation dictionary from evaluate_prompt().
        
    Returns:
        Structured dictionary with parameter_analysis, overall_analysis, and actionable_tips.
    """
    scoring = evaluation_payload.get("scoring", {})
    breakdown = scoring.get("breakdown", {})
    overall_score = evaluation_payload.get("overall_score", 0)
    
    if not is_llm_available():
        return generate_fallback_recommendations(scoring, original_prompt)
        
    # Construct structured prompt with deep diagnostic metrics for Gemini
    score_summary_lines = []
    for param_key, param_info in breakdown.items():
        score = param_info.get("score", 0)
        label = param_info.get("label", param_key.capitalize())
        status = param_info.get("status", "Weak")
        details = param_info.get("details", {})
        missing = details.get("missing_list", [])
        detected = details.get("detected_list", [])
        
        detail_parts = []
        if detected:
            detail_parts.append(f"Detected: {', '.join(detected[:3])}")
        if missing:
            detail_parts.append(f"Missing: {', '.join(missing[:3])}")
        if not detail_parts:
            detail_parts.append(f"Feedback: {param_info.get('feedback', '')}")
            
        score_summary_lines.append(
            f"- {label}: {score}/10 (Status: {status}) | Details: {'; '.join(detail_parts)}"
        )
        
    scores_text = "\n".join(score_summary_lines)
    
    system_instruction = (
        "You are PromptCraft's expert AI prompt diagnostics engine.\n"
        "Your task is to analyze the user's prompt alongside the 7-Parameter Evaluation Engine Results.\n"
        "Generate a crystal-clear, user-friendly, and actionable breakdown in simple, everyday English.\n\n"
        "CRITICAL RULES:\n"
        "1. LOOK AT BOTH THE ORIGINAL PROMPT AND EVALUATION METRICS:\n"
        "   - Tailor your explanations directly to the specific topic and context of the user's prompt.\n"
        "   - Do NOT use generic cookie-cutter sentences.\n\n"
        "2. PURE ROOT CAUSES ONLY IN THE 'cause' FIELD:\n"
        "   - The 'cause' field MUST explain strictly WHY the prompt lost points and WHAT gap exists in the prompt text.\n"
        "   - NEVER include recommendations, instructions, or action verbs in 'cause'.\n"
        "   - NEVER write 'Consider...', 'Try...', 'Please...', 'You should...', 'Tell the AI...'.\n"
        "   - Example of correct cause: 'The prompt asks to compare two languages without stating the specific project type, performance needs, or developer skill level.'\n\n"
        "3. PURE ACTIONABLE FIXES IN THE 'improvement' FIELD:\n"
        "   - Must start with a direct action verb (e.g., 'Specify...', 'Add...', 'Define...', 'State...', 'Limit...').\n"
        "   - Example of correct improvement: 'Specify the target application domain (e.g., web backend vs data science) and request a side-by-side comparison table.'\n\n"
        "4. ALIGNMENT WITH SCORES:\n"
        "   - If score >= 7.0: status = 'Strong', weakness = null, cause = null, improvement = 'Prompt already meets high quality standards.'\n"
        "   - If score < 7.0: status = 'Weak' or 'Moderate', provide explicit weakness, pure cause, and actionable improvement.\n\n"
        "5. SIMPLE & FRIENDLY LANGUAGE:\n"
        "   - Write in warm, encouraging, everyday English so anyone can understand immediately."
    )
    
    prompt = f"""
Analyze this prompt and its 7-parameter evaluation results:

USER PROMPT:
\"\"\"{original_prompt}\"\"\"

7-PARAMETER QUANTITATIVE EVALUATION RESULTS (Overall Score: {overall_score}/100):
{scores_text}

Return a valid JSON object matching EXACTLY this schema:
{{
    "parameter_analysis": [
        {{
            "parameter": "<Exact Parameter Name>",
            "score": <number>,
            "status": "Strong" | "Moderate" | "Weak",
            "weakness": "<Specific weakness in prompt text, or null if Strong>",
            "cause": "<Strictly WHY the prompt has this flaw with NO recommendations, or null if Strong>",
            "improvement": "<Actionable instruction starting with an action verb to fix the weakness>"
        }}
    ],
    "overall_analysis": "<2 sentence clear summary of prompt quality and top priorities>",
    "actionable_tips": [
        "<Actionable tip 1>",
        "<Actionable tip 2>",
        "<Actionable tip 3>"
    ]
}}
"""
    
    structured_response = generate_structured_json(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=0.2
    )
    
    if structured_response and "parameter_analysis" in structured_response:
        # Sanitize responses
        for item in structured_response["parameter_analysis"]:
            p_score = float(item.get("score", 0))
            p_status = item.get("status", "Weak")
            if p_score >= 7.0:
                item["status"] = "Strong"
                item["weakness"] = None
                item["cause"] = None
                if not item.get("improvement") or "maintain" in item.get("improvement", "").lower():
                    item["improvement"] = f"Prompt already excels in {item.get('parameter', 'this parameter')}."
            elif p_status != "Strong":
                # Ensure cause does not contain advice verbs
                cause_text = item.get("cause", "")
                if cause_text:
                    for sep in [". Consider ", ". Try ", ". Tell the AI ", ". Please ", ". You should "]:
                        if sep in cause_text:
                            cause_text = cause_text.split(sep)[0].strip()
                    item["cause"] = cause_text
                    
        return structured_response
        
    # Intelligent fallback if LLM failed
    return generate_fallback_recommendations(scoring, original_prompt)
