"""
Authentication UI for PromptCraft - Prompt Quality Evaluation & Learning System
-------------------------------------------------------------------------------
Renders the exact glassmorphic Login & Sign-Up screens matching the design specification.
"""

import base64
import importlib
from pathlib import Path
import streamlit as st
import backend.auth_service
if not hasattr(backend.auth_service, "reset_user_password"):
    importlib.reload(backend.auth_service)
from backend.auth_service import authenticate_user, register_user, reset_user_password
try:
    from utils.helpers import embed_script_component
except Exception:
    def embed_script_component(html_code: str, height: int = 0):
        try:
            if hasattr(st, "_main") and hasattr(st._main, "_html"):
                return st._main._html(html_code, height=height)
        except Exception:
            pass
        import streamlit.components.v1 as components
        return components.html(html_code, height=height)

ROOT_DIR = Path(__file__).resolve().parent.parent
BRAIN_LOGO_PATH = ROOT_DIR / "assets" / "promptcraft_brain_logo.png"

def _get_brain_logo_b64() -> str:
    if BRAIN_LOGO_PATH.exists():
        with open(BRAIN_LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

BRAIN_LOGO_B64 = _get_brain_logo_b64()

WORDMARK_PATH = ROOT_DIR / "assets" / "promptcraft_wordmark.png"

def _get_wordmark_b64() -> str:
    if WORDMARK_PATH.exists():
        with open(WORDMARK_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

WORDMARK_B64 = _get_wordmark_b64()


def render_auth_css():
    """Injects high-fidelity CSS for the glassmorphic Login & Sign-Up screens."""
    st.html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Ambient background on the entire screen */
    .stApp {
        background: radial-gradient(circle at 10% 15%, rgba(219, 234, 254, 0.85) 0%, transparent 40%),
                    radial-gradient(circle at 90% 10%, rgba(237, 233, 254, 0.85) 0%, transparent 40%),
                    radial-gradient(circle at 85% 85%, rgba(224, 231, 255, 0.8) 0%, transparent 40%),
                    radial-gradient(circle at 15% 85%, rgba(240, 249, 255, 0.8) 0%, transparent 40%),
                    #F0F4F9 !important;
        min-height: 100vh;
    }
    
    /* Hide default header and sidebar in auth mode */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Centered Main Container */
    .main .block-container, [data-testid="stMainBlockContainer"] {
        max-width: 980px !important;
        margin: 1.5rem auto !important;
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    
    /* Glassmorphism Outer Card Wrapper around the columns */
    [data-testid="stHorizontalBlock"] {
        background: rgba(255, 255, 255, 0.76) !important;
        backdrop-filter: blur(28px) !important;
        -webkit-backdrop-filter: blur(28px) !important;
        border: 1.5px solid rgba(255, 255, 255, 0.9) !important;
        border-radius: 28px !important;
        box-shadow: 0 25px 60px -15px rgba(99, 102, 241, 0.12), 0 0 1px 1px rgba(255, 255, 255, 0.9) inset !important;
        padding: 36px 32px !important;
        align-items: stretch !important;
    }
    
    /* LEFT BRANDING COLUMN STYLING */
    .auth-brand {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 18px;
    }
    .auth-brand-logo-img {
        width: 60px;
        height: 60px;
        object-fit: contain;
        filter: drop-shadow(0 4px 14px rgba(37, 99, 235, 0.35));
        flex-shrink: 0;
    }
    .auth-brand-wordmark-img {
        height: 32px;
        width: auto;
        max-width: 220px;
        object-fit: contain;
        display: block;
        margin-bottom: 2px;
    }
    .auth-brand-icon {
        width: 44px;
        height: 44px;
        background: linear-gradient(135deg, #0284C7 0%, #6366F1 50%, #8B5CF6 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        color: #FFFFFF;
        box-shadow: 0 6px 18px rgba(99, 102, 241, 0.35);
        flex-shrink: 0;
    }
    .auth-brand-name {
        font-size: 1.4rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
    }
    .auth-brand-subtitle {
        font-size: 0.88rem;
        font-weight: 600;
        color: #475569;
        margin-top: 3px;
        letter-spacing: -0.01em;
    }
    
    .auth-hero-title {
        font-size: 2rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.15;
        margin-bottom: 8px;
    }
    .auth-hero-gradient {
        background: linear-gradient(135deg, #0284C7 0%, #4F46E5 60%, #7C3AED 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .auth-hero-desc {
        font-size: 0.85rem;
        color: #64748B;
        line-height: 1.5;
        margin-bottom: 20px;
    }
    
    .auth-feature-list {
        display: flex;
        flex-direction: column;
        gap: 11px;
        margin-bottom: 18px;
    }
    .auth-feature-item {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .auth-feature-icon {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: #EEF2FF;
        border: 1px solid #E0E7FF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 15px;
        color: #4F46E5;
        flex-shrink: 0;
        box-shadow: 0 2px 6px rgba(99, 102, 241, 0.08);
    }
    .auth-feature-title {
        font-size: 0.84rem;
        font-weight: 700;
        color: #1E293B;
        line-height: 1.2;
    }
    .auth-feature-subtitle {
        font-size: 0.72rem;
        color: #64748B;
        margin-top: 1px;
    }
    
    .auth-illustration-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 6px;
    }
    
    .auth-tagline {
        font-size: 0.66rem;
        font-weight: 800;
        letter-spacing: 2.2px;
        color: #94A3B8;
        text-transform: uppercase;
        margin-top: 14px;
    }
    
    /* RIGHT FORM CARD STYLING */
    div[data-testid="stForm"] {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04) !important;
        padding: 28px 24px 22px 24px !important;
        margin-bottom: 0px !important;
    }
    
    .auth-form-title {
        font-size: 1.45rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.2;
        margin-bottom: 4px;
    }
    .auth-form-subtitle {
        font-size: 0.82rem;
        color: #64748B;
        margin-bottom: 16px;
    }
    
    /* Force crisp white input background across all Streamlit theme defaults */
    div[data-testid="stTextInput"] > div,
    div[data-testid="stTextInput"] div[data-baseweb="base-input"],
    div[data-testid="stTextInput"] div[data-baseweb="input"],
    div[data-testid="stTextInput"] input {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 10px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
    }
    div[data-testid="stTextInput"] input {
        border: none !important;
        padding: 9px 12px !important;
    }
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.18) !important;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: #94A3B8 !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextInput"] label p {
        color: #334155 !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        margin-bottom: 3px !important;
    }
    
    /* Password Eye Icon styling */
    div[data-testid="stTextInput"] button {
        color: #64748B !important;
        background: transparent !important;
        border: none !important;
    }
    
    /* Checkbox Styling */
    div[data-testid="stCheckbox"] label p {
        color: #475569 !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
    }
    
    /* Secondary Google Button */
    div.stButton > button[key="google_login_btn"],
    div.stButton > button[key="google_signup_btn"] {
        background: #FFFFFF !important;
        color: #334155 !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        padding: 9px 18px !important;
        border: 1.5px solid #CBD5E1 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
        width: 100% !important;
    }
    div.stButton > button[key="google_login_btn"]:hover,
    div.stButton > button[key="google_signup_btn"]:hover {
        background: #F8FAFC !important;
        border-color: #94A3B8 !important;
        color: #0F172A !important;
    }

    /* Secondary Switch Buttons (e.g. "Sign Up", "Sign In Instead", "Go to Login Page") */
    div.stButton:not(form div.stButton) > button,
    div.stButton:not([data-testid="stFormSubmitButton"]) > button {
        background: #C7D2FE !important;
        background-color: #C7D2FE !important;
        color: #1E40AF !important;
        border: 1px solid #BFDBFE !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        height: 44px !important;
        min-height: 44px !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.12) !important;
        width: 100% !important;
        margin-top: 6px !important;
        transition: all 0.2s ease !important;
        opacity: 1 !important;
    }
    div.stButton:not(form div.stButton) > button:hover,
    div.stButton:not([data-testid="stFormSubmitButton"]) > button:hover {
        background: #A5B4FC !important;
        background-color: #A5B4FC !important;
        color: #1E3A8A !important;
        border-color: #93C5FD !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.22) !important;
        transform: translateY(-1px) !important;
    }
    div.stButton:not(form div.stButton) > button p,
    div.stButton:not(form div.stButton) > button span,
    div.stButton:not([data-testid="stFormSubmitButton"]) > button p,
    div.stButton:not([data-testid="stFormSubmitButton"]) > button span {
        color: #1E40AF !important;
        font-weight: 700 !important;
    }

    /* Primary Submit Button: Rich Royal Blue Gradient (Guaranteed Specificity) */
    div[data-testid="stFormSubmitButton"] > button,
    div[data-testid="stFormSubmitButton"] button,
    form div[data-testid="stFormSubmitButton"] button,
    div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        font-size: 0.98rem !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        padding: 12px 20px !important;
        border: 1px solid #1D4ED8 !important;
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.35) !important;
        width: 100% !important;
        margin-top: 8px !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.01em !important;
    }
    div[data-testid="stFormSubmitButton"] button p,
    div[data-testid="stFormSubmitButton"] button span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
        background-color: #1D4ED8 !important;
        box-shadow: 0 6px 22px rgba(37, 99, 235, 0.48) !important;
        transform: translateY(-1px) !important;
    }
    div[data-testid="stFormSubmitButton"] button:active,
    div[data-testid="stFormSubmitButton"] button.is-processing {
        opacity: 0.55 !important;
        filter: brightness(0.92) !important;
        cursor: wait !important;
        transform: scale(0.99) !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.2) !important;
    }
    
    .auth-divider {
        display: flex;
        align-items: center;
        text-align: center;
        margin: 14px 0;
        color: #94A3B8;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .auth-divider::before, .auth-divider::after {
        content: '';
        flex: 1;
        border-bottom: 1px solid #E2E8F0;
    }
    .auth-divider:not(:empty)::before {
        margin-right: .75em;
    }
    .auth-divider:not(:empty)::after {
        margin-left: .75em;
    }

    /* =========================================================================
       REGISTRATION SUCCESSFUL MODAL & CARD (MATCHING USER'S SPECIFICATION)
       ========================================================================= */
    div[data-testid="stDialog"] {
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        background-color: rgba(15, 23, 42, 0.45) !important;
    }
    
    /* Completely hide and eliminate any dialog header, close button, or blue strip */
    div[data-testid="stDialog"] [data-testid="stDialogHeader"],
    div[data-testid="stDialog"] [data-testid="stModalHeader"],
    div[data-testid="stDialog"] button[aria-label="Close"],
    div[data-testid="stDialog"] button[data-testid*="header"],
    div[data-testid="stDialog"] button[data-testid*="Close"],
    div[data-testid="stDialog"] > div[role="dialog"] > div:first-child:not(:has(.reg-success-container)),
    div[data-testid="stDialog"] > div[role="dialog"] > div:first-child:has(button[aria-label="Close"]),
    div[data-testid="stDialog"] button[aria-label="Close"],
    div[data-testid="stDialog"] button:not(.stButton > button) {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0 !important;
        max-height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        pointer-events: none !important;
        position: absolute !important;
        top: -9999px !important;
        left: -9999px !important;
        width: 0 !important;
    }
    
    div[data-testid="stDialog"] > div[role="dialog"] {
        border-radius: 22px !important;
        background: #FFFFFF !important;
        box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.25), 0 0 0 1px rgba(226, 232, 240, 0.8) !important;
        border: none !important;
        padding: 38px 32px 30px 32px !important;
        max-width: 420px !important;
        width: 90% !important;
        text-align: center !important;
        margin: auto !important;
    }
    
    .reg-success-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 0;
    }
    
    .reg-success-icon {
        font-size: 56px;
        line-height: 1;
        margin-bottom: 18px;
        display: inline-block;
        filter: drop-shadow(0 4px 12px rgba(234, 179, 8, 0.25));
    }
    
    .reg-success-heading {
        font-size: 1.48rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 10px;
        letter-spacing: -0.015em;
        line-height: 1.25;
    }
    
    .reg-success-message {
        font-size: 0.90rem;
        color: #64748B;
        line-height: 1.55;
        margin-bottom: 22px;
        max-width: 320px;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Action button inside dialog & success card */
    div[data-testid="stDialog"] div.stButton > button,
    div.stButton > button[key="btn_card_goto_login"],
    div.stButton > button[key="btn_card_goto_login_reset"],
    div.stButton > button[key="btn_modal_goto_login"],
    div.stButton > button[key="btn_modal_goto_login_reset"] {
        background: linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 100%) !important;
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        font-size: 1.02rem !important;
        font-weight: 700 !important;
        height: 44px !important;
        min-height: 44px !important;
        border: 1px solid #1E3A8A !important;
        box-shadow: 0 4px 14px rgba(30, 58, 138, 0.35) !important;
        width: 100% !important;
        letter-spacing: 0.01em !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[data-testid="stDialog"] div.stButton > button p,
    div[data-testid="stDialog"] div.stButton > button span,
    div.stButton > button[key="btn_card_goto_login"] p,
    div.stButton > button[key="btn_card_goto_login"] span,
    div.stButton > button[key="btn_card_goto_login_reset"] p,
    div.stButton > button[key="btn_card_goto_login_reset"] span,
    div.stButton > button[key="btn_modal_goto_login"] p,
    div.stButton > button[key="btn_modal_goto_login"] span,
    div.stButton > button[key="btn_modal_goto_login_reset"] p,
    div.stButton > button[key="btn_modal_goto_login_reset"] span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.02rem !important;
    }
    div[data-testid="stDialog"] div.stButton > button:hover,
    div.stButton > button[key="btn_card_goto_login"]:hover,
    div.stButton > button[key="btn_card_goto_login_reset"]:hover,
    div.stButton > button[key="btn_modal_goto_login"]:hover,
    div.stButton > button[key="btn_modal_goto_login_reset"]:hover {
        background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%) !important;
        box-shadow: 0 6px 20px rgba(30, 58, 138, 0.45) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Forgot password hyperlink styling */
    .auth-forgot-link {
        color: #2563EB !important;
        font-size: 0.92rem !important;
        font-weight: 700 !important;
        text-decoration: underline !important;
        cursor: pointer !important;
        transition: color 0.15s ease !important;
        display: inline-block !important;
        white-space: nowrap !important;
    }
    .auth-forgot-link:hover {
        color: #1D4ED8 !important;
        text-decoration: underline !important;
    }
    
    /* Completely hide background trigger button for Forgot Password */
    .st-key-btn_pc_act_forgot {
        display: none !important;
        position: absolute !important;
        left: -9999px !important;
        top: -9999px !important;
        width: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
        overflow: hidden !important;
    }
    
    /* Fallback Success Card */
    .reg-success-card {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04) !important;
        padding: 40px 28px !important;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    </style>
    """)


@st.dialog(" ", width="small")
def show_registration_success_modal():
    """Renders the modal dialog matching the user's reference design."""
    st.html("""
    <div class="reg-success-container">
        <div class="reg-success-icon">🎉</div>
        <div class="reg-success-heading">Registration Successful!</div>
        <div class="reg-success-message">
            Your account has been created successfully.<br>
            Please log in with your credentials to access your dashboard.
        </div>
    </div>
    """)
    if st.button("Go to Login Page", key="btn_modal_goto_login", use_container_width=True):
        st.session_state.show_reg_dialog = False
        st.session_state.auth_view = "login"
        st.rerun()


@st.dialog(" ", width="small")
def show_password_reset_success_modal():
    """Renders the modal dialog for successful password reset matching reference design."""
    st.html("""
    <div class="reg-success-container">
        <div class="reg-success-icon">🎉</div>
        <div class="reg-success-heading">Password Reset Successfully!</div>
        <div class="reg-success-message">
            Your password has been updated successfully.<br>
            Please log in with your new credentials to access your dashboard.
        </div>
    </div>
    """)
    if st.button("Go to Login Page", key="btn_modal_goto_login_reset", use_container_width=True):
        st.session_state.show_reset_dialog = False
        st.session_state.auth_view = "login"
        st.rerun()


def render_auth_page():
    """Renders the Login, Forgot Password, Sign-Up, or Success views based on st.session_state.auth_view."""
    render_auth_css()
    
    # URL Query param support
    if "auth_view" in st.query_params:
        qv = str(st.query_params["auth_view"]).lower()
        if qv in ["login", "signup", "forgot_password", "reset_success"]:
            st.session_state.auth_view = qv
        del st.query_params["auth_view"]

    # Client-side instant visual feedback for submit buttons
    embed_script_component("""
    <script>
    (function() {
        function setupAuthSubmitListener() {
            let doc;
            try {
                doc = (window.parent && window.parent.document) ? window.parent.document : null;
            } catch (e) {
                doc = null;
            }
            if (!doc) return;

            const submitBtns = doc.querySelectorAll('div[data-testid="stFormSubmitButton"] button');
            submitBtns.forEach(btn => {
                const text = (btn.innerText || btn.textContent || '').trim();
                if ((text.includes('Sign In') || text.includes('Sign Up') || text.includes('Reset Password')) && !btn.__pcSubmitBound) {
                    btn.__pcSubmitBound = true;
                    btn.addEventListener('click', function() {
                        btn.classList.add('is-processing');
                        btn.style.opacity = '0.50';
                        btn.style.filter = 'brightness(0.92)';
                        btn.style.cursor = 'wait';
                        if (text.includes('Sign In')) btn.innerText = 'Signing In... ⏳';
                        else if (text.includes('Sign Up')) btn.innerText = 'Creating Account... ⏳';
                        else if (text.includes('Reset Password')) btn.innerText = 'Resetting Password... ⏳';
                    });
                }
            });
            // Instantly hide the pc_act_forgot button in the DOM
            const hiddenBtns = Array.from(doc.querySelectorAll('button')).filter(el => (el.innerText || el.textContent || '').includes('pc_act_forgot'));
            hiddenBtns.forEach(hb => {
                const wrap = hb.closest('[data-testid="stElementContainer"]') || hb.closest('.stButton') || hb;
                wrap.style.setProperty('display', 'none', 'important');
                wrap.style.setProperty('position', 'absolute', 'important');
                wrap.style.setProperty('left', '-9999px', 'important');
                wrap.style.setProperty('width', '0', 'important');
                wrap.style.setProperty('height', '0', 'important');
                wrap.style.setProperty('margin', '0', 'important');
                wrap.style.setProperty('padding', '0', 'important');
            });

            const forgotLinks = doc.querySelectorAll('.auth-forgot-link');
            forgotLinks.forEach(l => {
                if (!l.__pcBound) {
                    l.__pcBound = true;
                    l.addEventListener('click', function(e) {
                        e.preventDefault();
                        const b = Array.from(doc.querySelectorAll('button')).find(el => (el.innerText || el.textContent || '').includes('pc_act_forgot'));
                        if (b) {
                            b.click();
                        } else {
                            const url = new URL(window.location.href);
                            url.searchParams.set('auth_view', 'forgot_password');
                            window.location.href = url.toString();
                        }
                    });
                }
            });
        }
        setInterval(setupAuthSubmitListener, 80);
        setupAuthSubmitListener();

        // Continuous Keep-Alive Heartbeat: Pings Streamlit server every 20s
        // Prevents browser tab sleeping, NAT drop, and Tornado WebSocket idle timeout
        function pingServerHeartbeat() {
            try {
                fetch('/_stcore/health', { method: 'GET', cache: 'no-store' }).catch(() => {});
            } catch(e) {}
        }
        setInterval(pingServerHeartbeat, 20000);
        pingServerHeartbeat();

        if (doc) {
            doc.addEventListener('visibilitychange', function() {
                if (doc.visibilityState === 'visible') pingServerHeartbeat();
            });
        }
    })();
    </script>
    """, height=0)
    
    if st.session_state.get("show_reg_dialog"):
        show_registration_success_modal()
    if st.session_state.get("show_reset_dialog"):
        show_password_reset_success_modal()
    
    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "login"
        
    auth_view = st.session_state.auth_view
    
    left_col, right_col = st.columns([1.12, 1.0], gap="large")
    
    # =========================================================================
    # LEFT COLUMN: Branding, Features, 3D Graphic & Tagline
    # =========================================================================
    with left_col:
        st.html(f"""
        <div class="auth-brand">
            <img src="data:image/png;base64,{BRAIN_LOGO_B64}" alt="PromptCraft Logo" class="auth-brand-logo-img" />
            <div>
                <img src="data:image/png;base64,{WORDMARK_B64}" alt="PromptCraft" class="auth-brand-wordmark-img" />
                <div class="auth-brand-subtitle">Prompt Quality Evaluation and Learning System</div>
            </div>
        </div>
        
        <div class="auth-hero-title">
            Better Prompts.<br>
            <span class="auth-hero-gradient">Smarter Results.</span>
        </div>
        
        <div class="auth-hero-desc">
            Evaluate your prompts, get AI-powered insights, and learn to create higher quality prompts.
        </div>
        
        <div class="auth-feature-list">
            <div class="auth-feature-item">
                <div class="auth-feature-icon">🎙️</div>
                <div>
                    <div class="auth-feature-title">Multi-Modal Input</div>
                    <div class="auth-feature-subtitle">Text, Image & Live Voice</div>
                </div>
            </div>
            <div class="auth-feature-item">
                <div class="auth-feature-icon">⚙️</div>
                <div>
                    <div class="auth-feature-title">7-Dimensional Evaluation</div>
                    <div class="auth-feature-subtitle">Grammar, Readability, Specificity...</div>
                </div>
            </div>
            <div class="auth-feature-item">
                <div class="auth-feature-icon">🔀</div>
                <div>
                    <div class="auth-feature-title">RAG-Powered Analysis</div>
                    <div class="auth-feature-subtitle">Contextual insights with real data</div>
                </div>
            </div>
            <div class="auth-feature-item">
                <div class="auth-feature-icon">🎓</div>
                <div>
                    <div class="auth-feature-title">Personalized Learning</div>
                    <div class="auth-feature-subtitle">Improve with every prompt</div>
                </div>
            </div>
        </div>
        
        <div class="auth-illustration-container">
            <svg width="220" height="100" viewBox="0 0 240 110" fill="none" xmlns="http://www.w3.org/2000/svg">
                <!-- Base Hologram Platform -->
                <ellipse cx="120" cy="85" rx="100" ry="22" fill="url(#haloGrad)" opacity="0.6"/>
                <ellipse cx="120" cy="85" rx="80" ry="16" stroke="url(#lineGrad)" stroke-width="1.5" stroke-dasharray="4 3"/>
                
                <!-- Isometric Computer / Terminal Layer -->
                <path d="M60 70 L120 40 L180 70 L120 100 Z" fill="url(#platGrad1)" stroke="#38BDF8" stroke-width="1.2"/>
                <path d="M75 62 L120 40 L165 62 L120 84 Z" fill="url(#platGrad2)" stroke="#818CF8" stroke-width="1"/>
                
                <!-- Holographic Floating Screen -->
                <path d="M90 48 L120 32 L150 48 L120 64 Z" fill="#0284C7" fill-opacity="0.25" stroke="#38BDF8" stroke-width="1.5"/>
                <rect x="110" y="24" width="20" height="20" rx="4" transform="rotate(45 110 24)" fill="url(#chipGrad)" stroke="#A5B4FC" stroke-width="1.5"/>
                
                <!-- Glowing circuit lines -->
                <line x1="85" y1="70" x2="65" y2="80" stroke="#38BDF8" stroke-width="1.5" stroke-linecap="round"/>
                <circle cx="65" cy="80" r="3" fill="#38BDF8"/>
                <line x1="155" y1="70" x2="175" y2="80" stroke="#818CF8" stroke-width="1.5" stroke-linecap="round"/>
                <circle cx="175" cy="80" r="3" fill="#818CF8"/>
                
                <!-- Glowing Core Center Icon -->
                <circle cx="120" cy="38" r="6" fill="#38BDF8"/>
                <circle cx="120" cy="38" r="3" fill="#FFFFFF"/>

                <!-- Gradients -->
                <defs>
                    <radialGradient id="haloGrad" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(120 85) rotate(90) scale(22 100)">
                        <stop stop-color="#38BDF8" stop-opacity="0.4"/>
                        <stop offset="1" stop-color="#6366F1" stop-opacity="0"/>
                    </radialGradient>
                    <linearGradient id="lineGrad" x1="40" y1="85" x2="200" y2="85" gradientUnits="userSpaceOnUse">
                        <stop stop-color="#38BDF8"/>
                        <stop offset="0.5" stop-color="#818CF8"/>
                        <stop offset="1" stop-color="#C084FC"/>
                    </linearGradient>
                    <linearGradient id="platGrad1" x1="60" y1="40" x2="180" y2="100" gradientUnits="userSpaceOnUse">
                        <stop stop-color="#0284C7" stop-opacity="0.8"/>
                        <stop offset="1" stop-color="#312E81" stop-opacity="0.9"/>
                    </linearGradient>
                    <linearGradient id="platGrad2" x1="75" y1="40" x2="165" y2="84" gradientUnits="userSpaceOnUse">
                        <stop stop-color="#38BDF8" stop-opacity="0.6"/>
                        <stop offset="1" stop-color="#4F46E5" stop-opacity="0.7"/>
                    </linearGradient>
                    <linearGradient id="chipGrad" x1="110" y1="24" x2="130" y2="44" gradientUnits="userSpaceOnUse">
                        <stop stop-color="#38BDF8"/>
                        <stop offset="1" stop-color="#6366F1"/>
                    </linearGradient>
                </defs>
            </svg>
        </div>
        
        <div class="auth-tagline">
            EVALUATE &nbsp;•&nbsp; UNDERSTAND &nbsp;•&nbsp; IMPROVE
        </div>
        """)

    # =========================================================================
    # RIGHT COLUMN: Login / Sign Up Form Card
    # =========================================================================
    with right_col:
        # Invisible background WebSocket transition button for Forgot Password
        if st.button("pc_act_forgot", key="btn_pc_act_forgot"):
            st.session_state.auth_view = "forgot_password"
            st.rerun()

        if auth_view == "login":
            with st.form(key="login_form"):
                st.html("""
                <div class="auth-form-title">Welcome Back 👋</div>
                <div class="auth-form-subtitle">Sign in to continue to PromptCraft</div>
                """)
                
                email_default = st.session_state.get("login_email", st.session_state.get("registered_email", ""))
                email = st.text_input("Email Address", value=email_default, placeholder="Enter your email", key="login_email")
                password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
                
                col_rem, col_forgot = st.columns([0.88, 1.12])
                with col_rem:
                    st.checkbox("Remember me", value=True, key="login_rem")
                with col_forgot:
                    st.html("""
                    <div style="text-align: right; padding-top: 3px; white-space: nowrap;">
                        <a href="#" class="auth-forgot-link" onclick="const b = Array.from(window.parent.document.querySelectorAll('button')).find(el => (el.innerText || el.textContent || '').includes('pc_act_forgot')); if (b) { b.click(); } return false;">Forgot password?</a>
                    </div>
                    """)
                
                submit_login = st.form_submit_button("Sign In  ➔", use_container_width=True)
                
            if submit_login:
                success, user_data, msg = authenticate_user(email, password)
                if success and user_data:
                    st.session_state.is_authenticated = True
                    st.session_state.current_user = user_data
                    st.query_params["user"] = user_data.get("email", "")
                    st.toast(f"Welcome back, {user_data.get('name', 'User')}!", icon="⚡")
                    st.rerun()
                else:
                    st.error(msg)
                    
            with st.container():
                st.html('<div class="auth-switch-marker"></div><div style="margin-top: 18px; margin-bottom: 8px; text-align: center; font-size: 0.84rem; color: #64748B;">Don\'t have an account?</div>')
                if st.button("Sign Up", key="btn_goto_signup", use_container_width=True):
                    st.session_state.auth_view = "signup"
                    st.rerun()

        elif auth_view == "forgot_password":
            # =================================================================
            # FORGOT / RESET PASSWORD VIEW
            # =================================================================
            with st.form(key="forgot_password_form"):
                st.html("""
                <div class="auth-form-title">Reset Password 🔐</div>
                <div class="auth-form-subtitle">Enter your registered email and choose a new password.</div>
                """)
                
                email_default = st.session_state.get("login_email", st.session_state.get("registered_email", ""))
                email = st.text_input("Email Address", value=email_default, placeholder="Enter your registered email", key="reset_email_input")
                new_password = st.text_input("New Password", type="password", placeholder="Enter new password (min. 4 characters)", key="reset_new_password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your new password", key="reset_confirm_password")
                
                st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                submit_reset = st.form_submit_button("Reset Password  ➔", use_container_width=True)
                
            if submit_reset:
                if not email.strip():
                    st.error("Please enter your email address.")
                elif "@" not in email or "." not in email:
                    st.error("Please provide a valid email address.")
                elif not new_password or not confirm_password:
                    st.error("Please enter and confirm your new password.")
                elif len(new_password) < 4:
                    st.error("Password must be at least 4 characters long.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match. Please verify and re-enter.")
                else:
                    success, msg = reset_user_password(email, new_password)
                    if success:
                        st.session_state.login_email = email.strip().lower()
                        st.session_state.show_reset_dialog = True
                        st.session_state.auth_view = "reset_success"
                        st.toast("Password reset successfully! 🎉", icon="🔐")
                        st.rerun()
                    else:
                        st.error(msg)
                        
            with st.container():
                st.html('<div class="auth-switch-marker"></div><div style="margin-top: 18px; margin-bottom: 8px; text-align: center; font-size: 0.84rem; color: #64748B;">Remember your password?</div>')
                if st.button("Back to Login", key="btn_goto_login_from_reset", use_container_width=True):
                    st.session_state.auth_view = "login"
                    st.rerun()

        elif auth_view == "reset_success":
            # =================================================================
            # PASSWORD RESET SUCCESS VIEW (MATCHING REGISTRATION SUCCESS DESIGN)
            # =================================================================
            st.html("""
            <div class="reg-success-card">
                <div class="reg-success-icon">🎉</div>
                <div class="reg-success-heading">Password Reset Successfully!</div>
                <div class="reg-success-message">
                    Your password has been updated successfully.<br>
                    Please log in with your new credentials to access your dashboard.
                </div>
            </div>
            """)
            st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
            if st.button("Go to Login Page", key="btn_card_goto_login_reset", use_container_width=True):
                st.session_state.show_reset_dialog = False
                st.session_state.auth_view = "login"
                st.rerun()

        elif auth_view == "registration_success":
            # =================================================================
            # REGISTRATION SUCCESSFUL VIEW (MATCHING USER SCREENSHOT)
            # =================================================================
            st.html("""
            <div class="reg-success-card">
                <div class="reg-success-icon">🎉</div>
                <div class="reg-success-heading">Registration Successful!</div>
                <div class="reg-success-message">
                    Your account has been created successfully.<br>
                    Please log in with your credentials to access your dashboard.
                </div>
            </div>
            """)
            st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
            if st.button("Go to Login Page", key="btn_card_goto_login", use_container_width=True):
                st.session_state.show_reg_dialog = False
                st.session_state.auth_view = "login"
                st.rerun()
            
        else:
            # =================================================================
            # SIGN UP VIEW
            # =================================================================
            with st.form(key="signup_form"):
                st.html("""
                <div class="auth-form-title">Create Your Account</div>
                <div class="auth-form-subtitle">Join PromptCraft and start your journey.</div>
                """)
                
                full_name = st.text_input("Full Name", placeholder="Enter your name", key="signup_name")
                email = st.text_input("Email Address", placeholder="Enter your email", key="signup_email")
                password = st.text_input("Password", type="password", placeholder="Create a password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password", key="signup_confirm_password")
                
                submit_signup = st.form_submit_button("Sign Up  ➔", use_container_width=True)
                
            if submit_signup:
                if not full_name.strip():
                    st.error("Please enter your full name.")
                elif not email.strip() or "@" not in email:
                    st.error("Please enter a valid email address.")
                elif len(password) < 4:
                    st.error("Password must be at least 4 characters long.")
                elif password != confirm_password:
                    st.error("Passwords do not match. Please re-enter your password.")
                else:
                    success, msg = register_user(full_name, email, password)
                    if success:
                        st.session_state.registered_email = email.strip().lower()
                        st.session_state.login_email = email.strip().lower()
                        st.session_state.show_reg_dialog = True
                        st.session_state.auth_view = "registration_success"
                        st.rerun()
                    else:
                        st.error(msg)
                        
            with st.container():
                st.html('<div class="auth-switch-marker"></div><div style="margin-top: 18px; margin-bottom: 8px; text-align: center; font-size: 0.84rem; color: #64748B;">Already have an account?</div>')
                if st.button("Sign In Instead", key="btn_goto_login", use_container_width=True):
                    st.session_state.auth_view = "login"
                    st.rerun()
