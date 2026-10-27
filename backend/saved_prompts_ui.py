"""
PromptCraft Saved Prompts UI
----------------------------
Renders user's saved prompts library with Like, Copy, Test, and Delete actions.
Only displays the clean saved prompts without clutter.
"""

import html
import json
import streamlit as st
try:
    from utils.helpers import copy_to_system_clipboard, inject_client_clipboard_copy, embed_script_component
except Exception:
    import sys
    def copy_to_system_clipboard(text: str) -> bool:
        if not text: return False
        if sys.platform == "win32":
            try:
                import subprocess
                subprocess.run(["clip"], input=text.encode("utf-16le"), check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                return True
            except Exception: pass
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except Exception: pass
        return False
    def embed_script_component(html_code: str, height: int = 0):
        try:
            if hasattr(st, "_main") and hasattr(st._main, "_html"):
                return st._main._html(html_code, height=height)
        except Exception: pass
        import streamlit.components.v1 as components
        return components.html(html_code, height=height)
    def inject_client_clipboard_copy(text: str):
        pass
from database.repositories import (
    get_user_saved_prompts,
    delete_saved_prompt
)
from database.mongodb import get_database


def toggle_like_saved_prompt(prompt_id: str, user_email: str) -> bool:
    """Toggles the liked / favorite status of a saved prompt in MongoDB Atlas."""
    db = get_database()
    if db is None:
        return False
    try:
        from bson import ObjectId
        query = {"user_email": user_email.strip().lower()}
        try:
            query["_id"] = ObjectId(prompt_id)
        except Exception:
            query["_id"] = prompt_id

        doc = db.saved_prompts.find_one(query)
        if doc:
            current_status = doc.get("is_liked", False)
            new_status = not current_status
            db.saved_prompts.update_one(query, {"$set": {"is_liked": new_status}})
            return new_status
        return False
    except Exception as e:
        print(f"[MongoDB] Error toggling liked prompt: {e}")
        return False



def render_saved_prompts_view(user_email: str):
    """Renders the Saved Prompts library view."""
    st.html("""
    <div style="margin-bottom: 20px;">
        <h2 style="font-size: 1.5rem; font-weight: 800; color: #0F172A; margin: 0 0 4px 0;">💾 Saved Prompts Library</h2>
        <div style="font-size: 0.88rem; color: #64748B;">Your personal collection of saved prompts with quick actions to Like, Copy, Test, and Manage.</div>
    </div>
    """)

    # Initialize liked prompts in session state
    if "liked_saved_prompts" not in st.session_state:
        st.session_state.liked_saved_prompts = set()

    # 1. Fetch saved prompts from MongoDB (with fallback to session_state)
    db_saved = get_user_saved_prompts(user_email)
    
    # Merge with any session_state items if not in DB
    saved_list = db_saved
    if not saved_list and "saved_prompts_list" in st.session_state and st.session_state.saved_prompts_list:
        saved_list = []
        for idx, item in enumerate(st.session_state.saved_prompts_list):
            saved_list.append({
                "id": f"session_{idx}",
                "original_prompt": item.get("original", ""),
                "optimized_prompt": item.get("optimized", ""),
                "overall_score": item.get("score", 0),
                "is_liked": item.get("is_liked", False),
                "created_at_formatted": item.get("time", "Recently")
            })

    # Sync any pre-existing is_liked from DB into session state
    for item in saved_list:
        iid = str(item.get("id", ""))
        if item.get("is_liked") and iid:
            st.session_state.liked_saved_prompts.add(iid)

    total_count = len(saved_list)
    liked_count = sum(1 for it in saved_list if str(it.get("id")) in st.session_state.liked_saved_prompts or it.get("is_liked"))

    # 2. Stats & Search Bar
    c_stat, c_search = st.columns([5, 5])
    with c_stat:
        st.html(f"""
        <div style="display:flex; gap:12px;">
            <div style="background:#FFFFFF; border:1.5px solid #E2E8F0; border-radius:12px; padding:10px 16px; display:flex; align-items:center; gap:12px; flex:1; box-shadow:0 1px 3px rgba(0,0,0,0.02);">
                <div style="width:36px; height:36px; border-radius:10px; background:linear-gradient(135deg, #6366F1, #8B5CF6); display:flex; align-items:center; justify-content:center; color:#FFFFFF; font-size:1.1rem; font-weight:800;">💾</div>
                <div>
                    <div style="font-size:0.72rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.04em;">Total Saved</div>
                    <div style="font-size:1.25rem; font-weight:800; color:#0F172A; line-height:1.2;">{total_count}</div>
                </div>
            </div>
            <div style="background:#FFFFFF; border:1.5px solid #E2E8F0; border-radius:12px; padding:10px 16px; display:flex; align-items:center; gap:12px; flex:1; box-shadow:0 1px 3px rgba(0,0,0,0.02);">
                <div style="width:36px; height:36px; border-radius:10px; background:linear-gradient(135deg, #EC4899, #F43F5E); display:flex; align-items:center; justify-content:center; color:#FFFFFF; font-size:1.1rem; font-weight:800;">❤️</div>
                <div>
                    <div style="font-size:0.72rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.04em;">Liked</div>
                    <div style="font-size:1.25rem; font-weight:800; color:#0F172A; line-height:1.2;">{liked_count}</div>
                </div>
            </div>
        </div>
        """)

    with c_search:
        search_query = st.text_input(
            "Search saved prompts",
            placeholder="🔍 Search saved prompts by keyword...",
            label_visibility="collapsed",
            key="saved_prompts_search_input"
        )

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    # Filter by search if provided
    if search_query.strip():
        q = search_query.strip().lower()
        saved_list = [
            item for item in saved_list
            if q in item.get("optimized_prompt", "").lower() or q in item.get("original_prompt", "").lower()
        ]

    # 3. Empty State
    if not saved_list:
        if search_query.strip():
            st.html(f"""
            <div style="background:#FFFFFF; border:1.5px dashed #CBD5E1; border-radius:16px; padding:36px 20px; text-align:center; margin-top:10px;">
                <div style="font-size:2rem; margin-bottom:8px;">🔍</div>
                <div style="font-size:1.1rem; font-weight:700; color:#1E293B;">No matching prompts found</div>
                <div style="font-size:0.85rem; color:#64748B; max-width:420px; margin:6px auto 0 auto;">
                    No saved prompts matched "{html.escape(search_query)}". Try searching for another keyword.
                </div>
            </div>
            """)
        else:
            st.html("""
            <div style="background:#FFFFFF; border:1.5px dashed #CBD5E1; border-radius:16px; padding:40px 20px; text-align:center; margin-top:10px;">
                <div style="font-size:2.5rem; margin-bottom:10px;">💾</div>
                <div style="font-size:1.15rem; font-weight:700; color:#1E293B;">No Saved Prompts Yet</div>
                <div style="font-size:0.88rem; color:#64748B; max-width:460px; margin:8px auto 20px auto; line-height:1.5;">
                    When you evaluate or optimize a prompt in the <b>⚡ Evaluate</b> tab, click the <b>💾 Save Prompt</b> button to store it in this collection!
                </div>
            </div>
            """)
            
            c_center = st.columns([3.5, 3, 3.5])
            with c_center[1]:
                if st.button("⚡ Go to Evaluator", key="btn_go_eval_from_empty", use_container_width=True):
                    st.session_state.current_nav_view = "eval"
                    st.session_state.step = 1
                    st.rerun()
        return

    # 4. Prompt Card List
    st.html(f"""
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px;">
        <span style="font-size:1.02rem; font-weight:800; color:#0F172A;">Saved Prompts ({len(saved_list)})</span>
        <span style="font-size:0.78rem; font-weight:600; color:#4F46E5; background:#EEF2FF; border:1px solid #C7D2FE; padding:3px 10px; border-radius:999px;">Saved Collection</span>
    </div>
    """)

    for idx, item in enumerate(saved_list):
        item_id = str(item.get("id", f"item_{idx}"))
        prompt_text = item.get("optimized_prompt") or item.get("original_prompt", "")
        score = int(item.get("overall_score", 0))
        time_str = str(item.get("created_at_formatted", "Recently"))
        is_liked = (item_id in st.session_state.liked_saved_prompts) or bool(item.get("is_liked", False))

        # Score pill colors
        if score >= 80:
            score_bg, score_fg = "#ECFDF5", "#065F46"
        elif score >= 55:
            score_bg, score_fg = "#FFFBEB", "#92400E"
        else:
            score_bg, score_fg = "#FEF2F2", "#991B1B"

        # Escape prompt text
        escaped_prompt = html.escape(prompt_text)

        # Heart badge if liked
        liked_badge = '<span style="font-size: 0.72rem; font-weight: 700; background: #FEE2E2; color: #DC2626; padding: 2px 8px; border-radius: 6px;">❤️ Liked</span>' if is_liked else ""

        # Render clean prompt card containing ONLY the saved prompt
        card_html = f"""
        <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 14px; padding: 18px 20px; margin-bottom: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; border-bottom: 1px solid #F1F5F9; padding-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 0.78rem; font-weight: 700; background: #EDE9FE; color: #6D28D9; padding: 3px 10px; border-radius: 6px;">✨ Saved Prompt #{idx+1}</span>
                    {liked_badge}
                    <span style="font-size: 0.75rem; color: #94A3B8;">🕒 {time_str}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span style="font-size: 0.75rem; color: #64748B;">Score:</span>
                    <span style="background: {score_bg}; color: {score_fg}; font-size: 0.82rem; font-weight: 800; padding: 2px 10px; border-radius: 999px;">{score}/100</span>
                </div>
            </div>

            <div style="background: #FAF5FF; border: 1.5px solid #DDD6FE; color: #1E1B4B; font-weight: 500; font-size: 0.94rem; line-height: 1.6; border-radius: 10px; padding: 16px; white-space: pre-wrap; word-break: break-word;">{escaped_prompt}</div>
        </div>
        """

        st.html(card_html)

        # Action Buttons Row: Like, Copy, Test, Delete (Exact 1:1:1:1 alignment)
        b_like, b_copy, b_test, b_del = st.columns(4)
        
        with b_like:
            like_label = "❤️ Liked" if is_liked else "🤍 Like"
            if st.button(like_label, key=f"btn_like_saved_{item_id}_{idx}", use_container_width=True):
                if is_liked:
                    st.session_state.liked_saved_prompts.discard(item_id)
                    if not item_id.startswith("session_"):
                        toggle_like_saved_prompt(item_id, user_email)
                    st.toast("Removed from liked prompts.", icon="🤍")
                else:
                    st.session_state.liked_saved_prompts.add(item_id)
                    if not item_id.startswith("session_"):
                        toggle_like_saved_prompt(item_id, user_email)
                    st.toast("Prompt added to favorites! ❤️", icon="❤️")
                st.rerun()

        with b_copy:
            if st.button("📋 Copy", key=f"btn_copy_saved_{item_id}_{idx}", use_container_width=True):
                copy_to_system_clipboard(prompt_text)
                inject_client_clipboard_copy(prompt_text)
                st.toast("Copied prompt to clipboard! 📋", icon="📋")

        with b_test:
            if st.button("⚡ Test", key=f"btn_test_saved_{item_id}_{idx}", use_container_width=True):
                st.session_state.user_prompt = prompt_text
                st.session_state.step = 1
                st.session_state.current_nav_view = "eval"
                st.session_state.evaluation_result = None
                st.session_state.ai_analysis = None
                st.session_state.optimized_prompt = None
                st.toast("Loaded prompt into Evaluator! ⚡", icon="⚡")
                st.rerun()

        with b_del:
            if st.button("🗑️ Delete", key=f"btn_del_saved_{item_id}_{idx}", use_container_width=True):
                # Delete from MongoDB
                if not item_id.startswith("session_"):
                    delete_saved_prompt(item_id, user_email)
                # Also remove from session_state list if present
                if "saved_prompts_list" in st.session_state:
                    st.session_state.saved_prompts_list = [
                        p for p in st.session_state.saved_prompts_list
                        if p.get("optimized") != prompt_text and p.get("original") != prompt_text
                    ]
                st.session_state.liked_saved_prompts.discard(item_id)
                st.toast("Saved prompt deleted. 🗑️", icon="🗑️")
                st.rerun()

        st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)
