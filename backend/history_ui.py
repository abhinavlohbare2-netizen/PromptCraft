"""
PromptCraft History & Analytics UI
----------------------------------
Renders user evaluation history and performance metrics fetched live from MongoDB Atlas.
"""

import streamlit as st
from database.repositories import get_user_evaluations, get_user_statistics


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_cached_stats(email: str):
    return get_user_statistics(email)


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_cached_evaluations(email: str, limit: int = 30):
    return get_user_evaluations(email, limit=limit)


def render_history_view(user_email: str):
    """Renders the user prompt history dashboard powered by MongoDB Atlas."""
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h2 style="font-size: 1.5rem; font-weight: 800; color: #0F172A; margin: 0 0 4px 0;">Evaluation History & Analytics</h2>
        <div style="font-size: 0.88rem; color: #64748B;">All your prompt assessments, 7-dimension scores, and AI optimizations saved in MongoDB Atlas.</div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Fetch live metrics from MongoDB Atlas (cached in RAM for instant 0ms switching)
    stats = _fetch_cached_stats(user_email)
    eval_list = _fetch_cached_evaluations(user_email, limit=30)

    # 2. Stat Overview Cards
    total_evals = stats.get("total_prompts", len(eval_list))
    avg_score = stats.get("avg_score", 0)
    max_score = stats.get("max_score", 0)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div style="background:#FFFFFF; border:1.5px solid #E2E8F0; border-radius:14px; padding:16px 20px; box-shadow:0 1px 4px rgba(0,0,0,0.03);">
            <div style="font-size:0.78rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.04em;">Total Prompts Evaluated</div>
            <div style="font-size:2rem; font-weight:800; color:#0F172A; margin-top:4px;">{total_evals}</div>
            <div style="font-size:0.75rem; color:#4F46E5; margin-top:2px;">📁 Logged in MongoDB Atlas</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div style="background:#FFFFFF; border:1.5px solid #E2E8F0; border-radius:14px; padding:16px 20px; box-shadow:0 1px 4px rgba(0,0,0,0.03);">
            <div style="font-size:0.78rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.04em;">Average Quality Score</div>
            <div style="font-size:2rem; font-weight:800; color:#4F46E5; margin-top:4px;">{avg_score} <span style="font-size:1rem; color:#94A3B8; font-weight:600;">/ 100</span></div>
            <div style="font-size:0.75rem; color:#10B981; margin-top:2px;">⚡ Across all 7 parameters</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div style="background:#FFFFFF; border:1.5px solid #E2E8F0; border-radius:14px; padding:16px 20px; box-shadow:0 1px 4px rgba(0,0,0,0.03);">
            <div style="font-size:0.78rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.04em;">Highest Score</div>
            <div style="font-size:2rem; font-weight:800; color:#059669; margin-top:4px;">{max_score} <span style="font-size:1rem; color:#94A3B8; font-weight:600;">/ 100</span></div>
            <div style="font-size:0.75rem; color:#059669; margin-top:2px;">🏆 Personal Best Record</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # 3. Prompt Evaluation Log Cards
    if not eval_list:
        st.markdown("""
        <div style="background:#FFFFFF; border:1.5px dashed #CBD5E1; border-radius:16px; padding:36px 20px; text-align:center; margin-top:10px;">
            <div style="font-size:2rem; margin-bottom:8px;">📝</div>
            <div style="font-size:1.1rem; font-weight:700; color:#1E293B;">No prompt evaluations recorded yet</div>
            <div style="font-size:0.85rem; color:#64748B; max-width:420px; margin:6px auto 16px auto;">
                Switch to the "⚡ Evaluate" tab to analyze your first prompt and see your results stored here in MongoDB Atlas!
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px;">
            <span style="font-size:1.05rem; font-weight:800; color:#0F172A;">Recent Prompt Evaluations ({len(eval_list)})</span>
            <span style="font-size:0.78rem; font-weight:600; color:#4F46E5; background:#EEF2FF; border:1px solid #C7D2FE; padding:3px 10px; border-radius:999px;">Live from MongoDB</span>
        </div>
        """, unsafe_allow_html=True)

        for idx, item in enumerate(eval_list):
            p_text = item.get("original_prompt", "")
            o_score = item.get("overall_score", 0)
            q_tier = item.get("quality_tier", "Evaluation")
            time_str = item.get("created_at_formatted", "Recently")
            inp_type = item.get("input_type", "text").capitalize()
            dim_scores = item.get("dimension_scores", {})

            # Tier color formatting
            if o_score >= 80:
                tier_bg, tier_fg, tier_border = "#ECFDF5", "#065F46", "#A7F3D0"
            elif o_score >= 55:
                tier_bg, tier_fg, tier_border = "#FFFBEB", "#92400E", "#FDE68A"
            else:
                tier_bg, tier_fg, tier_border = "#FEF2F2", "#991B1B", "#FECACA"

            card_col, btn_col = st.columns([8.2, 1.8])
            with card_col:
                st.markdown(f"""
                <div style="background:#FFFFFF; border:1.5px solid #E2E8F0; border-radius:14px; padding:16px 18px; margin-bottom:12px; box-shadow:0 1px 3px rgba(0,0,0,0.02);">
                    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="font-size:0.75rem; font-weight:700; background:#F1F5F9; color:#475569; padding:2px 8px; border-radius:6px;">{inp_type}</span>
                            <span style="font-size:0.75rem; color:#94A3B8;">🕒 {time_str}</span>
                        </div>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="background:{tier_bg}; color:{tier_fg}; border:1px solid {tier_border}; font-size:0.75rem; font-weight:700; padding:2px 10px; border-radius:999px;">{q_tier}</span>
                            <span style="font-size:1.15rem; font-weight:800; color:#0F172A;">{o_score}<span style="font-size:0.75rem; color:#94A3B8;">/100</span></span>
                        </div>
                    </div>
                    <div style="font-size:0.92rem; font-weight:600; color:#1E293B; line-height:1.45; margin-bottom:12px; word-break:break-word;">
                        "{p_text}"
                    </div>
                    <div style="display:flex; flex-wrap:wrap; align-items:center; gap:6px 12px; font-size:0.75rem; color:#475569; border-top:1px solid #F1F5F9; padding-top:10px;">
                        <span>✍️ Grammar: <b>{dim_scores.get('grammar', 0)}/10</b></span> •
                        <span>📖 Readability: <b>{dim_scores.get('readability', 0)}/10</b></span> •
                        <span>🎯 Specificity: <b>{dim_scores.get('specificity', 0)}/10</b></span> •
                        <span>🌐 Context: <b>{dim_scores.get('context', 0)}/10</b></span> •
                        <span>🧩 Completeness: <b>{dim_scores.get('completeness', 0)}/10</b></span> •
                        <span>🔍 Clarity: <b>{dim_scores.get('ambiguity', 0)}/10</b></span> •
                        <span>📏 Constraints: <b>{dim_scores.get('constraints', 0)}/10</b></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with btn_col:
                st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
                if st.button("⚡ Re-Evaluate", key=f"btn_re_eval_{idx}", use_container_width=True):
                    st.session_state.user_prompt = p_text
                    st.session_state.step = 1
                    st.session_state.current_nav_view = "eval"
                    st.session_state.evaluation_result = None
                    st.session_state.ai_analysis = None
                    st.session_state.optimized_prompt = None
                    st.rerun()
