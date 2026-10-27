"""
PromptCraft - Prompt Quality Evaluation & Learning System
---------------------------------------------------------
Progressive Step-by-Step Evaluation Dashboard matching exact SaaS specification:
- Step 1: Enter Your Prompt (Text / Image / Voice tabs)
- Step 2: Reference Material (Optional RAG Document Ingestion)
- Step 3: Prompt Evaluation (Master 7-Parameter Weighted Scoring & Gauge)
- Step 4: AI Prompt Analysis (Strengths, Weaknesses, Causes, Suggested Improvements)
- Step 5: Optimized Prompt (Side-by-side comparison with Gemini rewrite + RAG)
"""

import sys
import importlib
import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# Ensure repository root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Launch background AI model pre-warming (non-blocking thread)
from backend.prewarmer import start_background_prewarming
start_background_prewarming()

# Cached 3D Emoji Assets (Loads once, cached across reruns)
@st.cache_data
def _load_asset_b64(filename: str) -> str:
    asset_file = ROOT_DIR / "assets" / filename
    if asset_file.exists():
        with open(asset_file, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

VOICE_EMOJI_B64 = _load_asset_b64("voice_emoji_centered.png")
IMAGE_EMOJI_B64 = _load_asset_b64("image_emoji_centered.png")
TEXT_EMOJI_B64 = _load_asset_b64("text_emoji_centered.png")
BRAIN_LOGO_B64 = _load_asset_b64("promptcraft_brain_logo.png")
TOP_TIER_EMOJI_B64 = _load_asset_b64("top_tier_thumbs_up.png")

# Fast, lightweight backend imports (heavy sub-dependencies are now lazy + pre-warmed)
import utils.helpers
from utils.helpers import copy_to_system_clipboard, inject_client_clipboard_copy, embed_script_component
from backend.evaluation_engine import evaluate_prompt
from backend.document_processor import process_document
from backend.rag_engine import get_rag_manager
from backend.improvement_engine import analyze_weaknesses_and_improvements
import backend.prompt_rewriter
from backend.prompt_rewriter import rewrite_and_optimize_prompt, classify_prompt_archetype, ARCHETYPES
import database.repositories
import backend.auth_service
import backend.auth_ui
from backend.auth_ui import render_auth_page
from backend.ocr_service import extract_text_from_image
from backend.whisper_service import transcribe_audio
from backend.history_ui import render_history_view
from backend.saved_prompts_ui import render_saved_prompts_view
from database.repositories import save_evaluation, save_optimization, save_user_saved_prompt
from database.mongodb import prewarm_mongo_connection

# Pre-warm MongoDB connection asynchronously so Sign In / Sign Up is instantaneous
prewarm_mongo_connection()



# Streamlit Page Config
st.set_page_config(
    page_title="PromptCraft - Prompt Quality Evaluation & Learning System",
    page_icon=str(ROOT_DIR / "assets" / "favicon.png"),
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for SaaS UI matching the mockup
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background-color: #F8FAFC !important;
    color: #0F172A !important;
}

/* Ensure all text across main content area is clear and dark */
.stApp p, .stApp span, .stApp label, .stApp div:not([data-testid="stSidebar"] *) {
    color: inherit;
}

/* =========================================================================
   CLEAN LOADING STATE & SPINNER STYLING
   ========================================================================= */

/* Suppress Streamlit's blue/purple skeleton placeholder bars */
[data-testid="stSkeleton"],
.stSkeleton {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    background: transparent !important;
}

/* Spinner & Loading Status High-Contrast Clean Styling */
div[data-testid="stSpinner"],
.stSpinner,
div.stSpinner {
    background: #FFFFFF !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 14px 20px !important;
    margin: 14px 0 !important;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04) !important;
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
}

div[data-testid="stSpinner"] p,
div[data-testid="stSpinner"] span,
div[data-testid="stSpinner"] div,
.stSpinner p,
.stSpinner span,
.stSpinner div {
    color: #0F172A !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: -0.01em !important;
}

div[data-testid="stSpinner"] svg {
    stroke: #2563EB !important;
    fill: #2563EB !important;
}

header[data-testid="stHeader"] {
    background-color: transparent !important;
    height: 2.5rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #0F172A !important;
    color: #F8FAFC !important;
    border-right: 1px solid #1E293B;
}

.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 0 18px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 16px;
}
.sidebar-brand-logo-img {
    width: 56px;
    height: 56px;
    object-fit: contain;
    filter: drop-shadow(0 4px 14px rgba(37, 99, 235, 0.45));
    flex-shrink: 0;
}
.sidebar-brand-icon {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, #2563EB, #1D4ED8);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    flex-shrink: 0;
    box-shadow: 0 4px 14px rgba(29, 100, 236, 0.4);
}
.sidebar-brand-text {
    display: flex;
    flex-direction: column;
}
.brand-title {
    font-size: 1.48rem;
    font-weight: 800;
    color: #FFFFFF;
    line-height: 1.15;
    letter-spacing: -0.01em;
}
.brand-subtitle {
    font-size: 0.8rem;
    font-weight: 600;
    color: #60A5FA;
    line-height: 1.35;
    margin-top: 3px;
    letter-spacing: 0.1px;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 500;
    color: #94A3B8;
    margin-bottom: 4px;
    text-decoration: none;
}
.nav-item:hover {
    background-color: #1E293B;
    color: #FFFFFF;
}
.nav-item.active {
    background: linear-gradient(90deg, rgba(29, 100, 236, 0.18), rgba(139, 92, 246, 0.18));
    color: #60A5FA;
    font-weight: 600;
    border-left: 3px solid #2563EB;
}

/* Stepper */
.stepper-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.step-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.82rem;
    font-weight: 600;
    color: #64748B;
}
.step-item.active {
    color: #2563EB;
}
.step-item.completed {
    color: #10B981;
}
.step-circle {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.72rem;
    font-weight: 700;
    background: #F1F5F9;
    color: #64748B;
    border: 1px solid #CBD5E1;
}
.step-item.active .step-circle {
    background: linear-gradient(180deg, #2563EB 0%, #1D4ED8 100%);
    color: #FFFFFF;
    border-color: #2563EB;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);
}
.step-item.completed .step-circle {
    background: #10B981;
    color: #FFFFFF;
    border-color: #10B981;
}
.step-divider {
    flex: 1;
    height: 2px;
    background: #E2E8F0;
    margin: 0 8px;
}
.step-divider.active {
    background: #10B981;
}

/* Cards */
.step-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.step-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 4px;
}
.step-subtitle {
    font-size: 0.85rem;
    color: #64748B;
    margin-bottom: 14px;
}

/* 3 Equal-Length Input Tab Blocks (Exact 1:1:1 length, high contrast, zero fade) */
div[data-testid="stHorizontalBlock"]:has(button[key*="tab_btn_"]) {
    gap: 12px !important;
    margin-bottom: 16px !important;
}

div.stButton > button[key*="tab_btn_"],
.tabs-buttons-wrapper .stButton > button {
    height: 48px !important;
    border-radius: 12px !important;
    font-size: 1.02rem !important;
    letter-spacing: 0.02em !important;
    font-weight: 700 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border: 1px solid #1D4ED8 !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

div.stButton > button[key*="tab_btn_"] p,
div.stButton > button[key*="tab_btn_"] span,
.tabs-buttons-wrapper .stButton > button p,
.tabs-buttons-wrapper .stButton > button span {
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 1.02rem !important;
    letter-spacing: 0.02em !important;
}

div.stButton > button[key*="tab_btn_"]:hover,
.tabs-buttons-wrapper .stButton > button:hover {
    background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
    background-color: #1D4ED8 !important;
    border-color: #1E40AF !important;
    color: #FFFFFF !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.48) !important;
}

div.stButton > button[key*="tab_btn_"][kind="primary"],
div.stButton > button[key*="tab_btn_"][data-testid="baseButton-primary"],
.tabs-buttons-wrapper .stButton > button[kind="primary"],
.tabs-buttons-wrapper .stButton > button[data-testid="baseButton-primary"] {
    border: 2px solid #FFFFFF !important;
    box-shadow: 0 0 0 3px rgba(147, 197, 253, 0.45), 0 4px 16px rgba(37, 99, 235, 0.5) !important;
}


/* Step 2 File Uploader Dropzone Styling */
div[data-testid="stFileUploader"] {
    background: #FFFFFF !important;
    border: 1.5px dashed #CBD5E1 !important;
    border-radius: 14px !important;
    padding: 14px 18px !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02) !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stFileUploader"]:hover {
    border-color: #2563EB !important;
    background: #F8FAFC !important;
}

div[data-testid="stFileUploader"] section {
    background: transparent !important;
    padding: 4px !important;
}

div[data-testid="stFileUploader"] section > input + div {
    color: #334155 !important;
}

div[data-testid="stFileUploader"] button {
    background: #FFFFFF !important;
    color: #1E293B !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}

div[data-testid="stFileUploader"] button:hover {
    border-color: #2563EB !important;
    color: #2563EB !important;
    background: #EFF6FF !important;
}

/* =========================================================================
   VOICE PROMPT MICROPHONE CARD (EXACT USER SPECIFICATION)
   ========================================================================= */
.voice-card-title {
    font-size: 1rem;
    font-weight: 700;
    color: #1E293B;
    margin-top: 4px;
    margin-bottom: 12px;
    text-align: center;
    letter-spacing: -0.01em;
}

/* =========================================================================
   VOICE PROMPT MICROPHONE CARD (EXACT USER SPECIFICATION)
   ========================================================================= */
.voice-card-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #1E293B;
    margin-top: 4px;
    margin-bottom: 12px;
    text-align: center;
    letter-spacing: -0.01em;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stAudioInput"]),
div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stFileUploader"]),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.text-prompt-img) {
    border-radius: 18px !important;
    background: #FFFFFF !important;
    border: 1.5px solid #E2E8F0 !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
    padding: 24px 24px 28px 24px !important;
    transition: all 0.25s ease !important;
    margin: 0 auto 16px auto !important;
    max-width: 530px !important;
    width: 100% !important;
    box-sizing: border-box !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
    overflow: visible !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stAudioInput"]):hover,
div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stFileUploader"]):hover,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.text-prompt-img):hover {
    border-color: #CBD5E1 !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.07) !important;
}

.voice-card-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    width: 100%;
}

.voice-mic-badge {
    width: 88px;
    height: 88px;
    border-radius: 50%;
    background: radial-gradient(circle, #FFF7ED 0%, #FFEDD5 65%, #FED7AA 100%);
    border: 2px solid #FFEDD5;
    box-shadow: 0 4px 18px rgba(249, 115, 22, 0.18);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 4px auto 12px auto;
    transition: transform 0.2s ease;
    overflow: hidden;
}

.voice-mic-badge:hover {
    transform: scale(1.06);
}

.voice-mic-img {
    width: 70px;
    height: 70px;
    object-fit: contain;
    display: block;
    margin: auto;
    filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.08));
}

.image-prompt-img {
    width: 76px;
    height: 76px;
    object-fit: contain;
    display: block;
    margin: auto;
    filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.08));
}

.text-prompt-img {
    width: 80px;
    height: 80px;
    object-fit: contain;
    display: block;
    margin: auto;
    filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.08));
}

/* Custom styling for Image Prompt Dropzone inside the card */
div[data-testid="stFileUploader"] {
    width: 100% !important;
    margin: 4px auto 0 auto !important;
    padding: 0 !important;
}

div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
    background: #F8FAFC !important;
    border: 1.5px dashed #CBD5E1 !important;
    border-radius: 14px !important;
    padding: 16px 14px !important;
    text-align: center !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #EE5A24 !important;
    background: #FFF7ED !important;
}

div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] button {
    background: linear-gradient(135deg, #FF6A00 0%, #EE5A24 100%) !important;
    background-color: #EE5A24 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    height: 42px !important;
    padding: 0 24px !important;
    box-shadow: 0 4px 14px rgba(238, 90, 36, 0.35) !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] button:hover {
    background: linear-gradient(135deg, #F97316 0%, #EA580C 100%) !important;
    box-shadow: 0 6px 18px rgba(238, 90, 36, 0.5) !important;
    transform: translateY(-1px) !important;
}

div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] span {
    color: #475569 !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
}

div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] small {
    color: #94A3B8 !important;
    font-size: 0.8rem !important;
}

.voice-waveform-preview {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    margin-bottom: 12px;
}

.voice-waveform-preview .wave-dot {
    width: 3.5px;
    height: 3.5px;
    border-radius: 50%;
    background-color: #94A3B8;
    display: inline-block;
    opacity: 0.8;
}

.voice-waveform-preview .wave-bar {
    width: 2.5px;
    height: 14px;
    border-radius: 2px;
    background-color: #64748B;
    display: inline-block;
    margin: 0 2px;
}

.voice-instruction-label {
    font-size: 0.9rem;
    font-weight: 600;
    color: #334155;
    margin-bottom: 14px;
    text-align: center;
}

/* Transform Streamlit's native stAudioInput into the Orange Start Recording Button */
div[data-testid="stAudioInput"] {
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    margin: 0 auto !important;
    padding: 0 !important;
    overflow: visible !important;
}

div[data-testid="stAudioInput"] > div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    height: auto !important;
    min-height: 52px !important;
    padding: 2px 0 4px 0 !important;
    overflow: visible !important;
}

div[data-testid="stAudioInput"] > div > div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: wrap !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 12px !important;
    width: 100% !important;
    margin: 4px 0 !important;
    overflow: visible !important;
}

/* Hide idle waveform / empty spacer dots in idle state */
div[data-testid="stAudioInput"] > div > div:nth-child(3),
div[data-testid="stAudioInput"] [data-testid="stAudioInputWaveSurfer"] {
    display: none !important;
}

div[data-testid="stAudioInput"] span {
    overflow: visible !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Style the Record / Action Button into the prominent Orange button */
div[data-testid="stAudioInput"] button[data-testid="stAudioInputActionButton"] {
    background: linear-gradient(135deg, #FF6A00 0%, #EE5A24 100%) !important;
    background-color: #EE5A24 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    height: 44px !important;
    min-height: 44px !important;
    padding: 0 18px !important;
    width: auto !important;
    min-width: 175px !important;
    max-width: 215px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    box-shadow: 0 4px 14px rgba(238, 90, 36, 0.38) !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    margin: 2px 0 !important;
    position: relative !important;
}

div[data-testid="stAudioInput"] button[data-testid="stAudioInputActionButton"]:hover {
    background: linear-gradient(135deg, #F97316 0%, #EA580C 100%) !important;
    box-shadow: 0 6px 20px rgba(238, 90, 36, 0.55) !important;
    transform: translateY(-1px) !important;
}

div[data-testid="stAudioInput"] button[data-testid="stAudioInputActionButton"] svg {
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
    width: 19px !important;
    height: 19px !important;
    display: inline-block !important;
}

div[data-testid="stAudioInput"] button[data-testid="stAudioInputActionButton"][aria-label="Record"]::after {
    content: "Start Recording";
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    letter-spacing: 0.01em !important;
    margin-left: 6px !important;
}

div[data-testid="stAudioInput"] button[data-testid="stAudioInputActionButton"][aria-label="Stop recording"] {
    background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%) !important;
    border-color: #DC2626 !important;
    box-shadow: 0 4px 18px rgba(220, 38, 38, 0.5) !important;
    animation: pulseMic 1.3s infinite alternate !important;
}

@keyframes pulseMic {
    0% { transform: scale(1); box-shadow: 0 4px 14px rgba(220, 38, 38, 0.4); }
    100% { transform: scale(1.03); box-shadow: 0 6px 22px rgba(220, 38, 38, 0.65); }
}

div[data-testid="stAudioInput"] button[data-testid="stAudioInputActionButton"][aria-label="Stop recording"]::after {
    content: "Stop Recording";
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    margin-left: 6px !important;
}

div[data-testid="stAudioInput"] button[data-testid="stAudioInputActionButton"][aria-label="Play"]::after {
    content: "Play Spoken Voice";
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    margin-left: 6px !important;
}

div[data-testid="stAudioInput"] button[data-testid="stAudioInputActionButton"][aria-label="Pause"]::after {
    content: "Pause";
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    margin-left: 6px !important;
}

div[data-testid="stAudioInput"] [data-testid="stAudioInputWaveformTimeCode"] {
    display: none !important;
}

div[data-testid="stAudioInput"]:has(button[aria-label="Stop recording"]) [data-testid="stAudioInputWaveformTimeCode"],
div[data-testid="stAudioInput"]:has(button[aria-label="Play"]) [data-testid="stAudioInputWaveformTimeCode"],
div[data-testid="stAudioInput"]:has(button[aria-label="Pause"]) [data-testid="stAudioInputWaveformTimeCode"] {
    display: block !important;
    font-family: monospace !important;
    color: #EA580C !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    margin-top: 10px !important;
    margin-bottom: 2px !important;
    text-align: center !important;
    width: 100% !important;
}

div.stButton > button[key="btn_eval_opt"] {
    background: linear-gradient(180deg, #2563EB 0%, #1D4ED8 100%) !important;
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border: none !important;
    height: 48px !important;
    border-radius: 12px !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.35) !important;
    transition: all 0.2s ease !important;
}

div.stButton > button[key="btn_eval_opt"]:hover {
    background: #1D4ED8 !important;
    background-color: #1D4ED8 !important;
    box-shadow: 0 6px 22px rgba(37, 99, 235, 0.48) !important;
    transform: translateY(-1px) !important;
}

div.stButton > button[key="btn_eval_opt"] p {
    color: #FFFFFF !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
}

div.stButton > button[key*="btn_del_"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    font-size: 1.25rem !important;
    padding: 4px 8px !important;
    color: #EF4444 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}

div.stButton > button[key*="btn_del_"]:hover {
    background: #FEE2E2 !important;
    border-radius: 8px !important;
    transform: scale(1.1) !important;
}

/* Ensure all widget labels are dark, bold, and 100% visible */
label[data-testid="stWidgetLabel"],
div[data-testid="stWidgetLabel"],
label[data-testid="stWidgetLabel"] p,
div[data-testid="stWidgetLabel"] p {
    color: #0F172A !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
}

/* Step 3: Evaluation Score Showcase (Modern Glassmorphic SaaS Hero) */
.score-showcase-container {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 22px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
    margin-top: 10px;
}

.score-hero-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 22px 16px;
    background: linear-gradient(165deg, #FFFFFF 0%, #F8FAFC 100%);
    border-radius: 14px;
    border: 1.5px solid #E2E8F0;
    text-align: center;
    height: 100%;
    box-sizing: border-box;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}

.score-hero-card.strong {
    border-color: #A7F3D0;
    box-shadow: 0 8px 24px -4px rgba(16, 185, 129, 0.18);
}
.score-hero-card.moderate {
    border-color: #FDE68A;
    box-shadow: 0 8px 24px -4px rgba(245, 158, 11, 0.18);
}
.score-hero-card.weak {
    border-color: #FECACA;
    box-shadow: 0 8px 24px -4px rgba(239, 68, 68, 0.18);
}

.score-hero-header {
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748B;
    margin-bottom: 12px;
}

.radial-gauge-container {
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 4px auto 14px auto;
}

.radial-gauge-ring {
    width: 130px;
    height: 130px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
    transition: all 0.5s ease;
}

.radial-gauge-inner {
    width: 106px;
    height: 106px;
    background: #FFFFFF;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.04);
}

.tier-pill-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 0.84rem;
    font-weight: 700;
    border: 1px solid;
    margin-bottom: 6px;
    letter-spacing: -0.01em;
}

.tier-pill-badge.strong {
    background: linear-gradient(180deg, #ECFDF5 0%, #D1FAE5 100%);
    color: #065F46;
    border-color: #6EE7B7;
}

.tier-pill-badge.moderate {
    background: linear-gradient(180deg, #FFFBEB 0%, #FEF3C7 100%);
    color: #92400E;
    border-color: #FCD34D;
}

.tier-pill-badge.weak {
    background: linear-gradient(180deg, #FEF2F2 0%, #FEE2E2 100%);
    color: #991B1B;
    border-color: #FCA5A5;
}

.score-stat-footer {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #F1F5F9;
    font-size: 0.72rem;
    color: #64748B;
    font-weight: 600;
    width: 100%;
}

/* Parameter Breakdown List Header */
.param-list-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #F1F5F9;
}

.param-list-title-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
}

.param-list-title {
    font-size: 0.96rem;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -0.01em;
}

.param-list-badge {
    font-size: 0.68rem;
    font-weight: 700;
    background: #EFF6FF;
    color: #2563EB;
    padding: 2px 8px;
    border-radius: 999px;
    border: 1px solid #DBEAFE;
    letter-spacing: 0.04em;
}

.legend-chips-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
}

.legend-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 600;
    border: 1px solid;
}

.legend-chip.strong {
    background: #ECFDF5;
    color: #065F46;
    border-color: #A7F3D0;
}

.legend-chip.moderate {
    background: #FFFBEB;
    color: #92400E;
    border-color: #FDE68A;
}

.legend-chip.weak {
    background: #FEF2F2;
    color: #991B1B;
    border-color: #FECACA;
}

.legend-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
}

/* Parameter Card Rows */
.param-card-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #FFFFFF;
    border: 1px solid #F1F5F9;
    border-radius: 12px;
    padding: 8px 14px;
    margin-bottom: 7px;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.param-card-row:hover {
    border-color: #CBD5E1;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
    transform: translateY(-1px);
}

.param-left-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 155px;
    min-width: 155px;
}

.param-icon-chip {
    font-size: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    border-radius: 8px;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.param-name-box {
    display: flex;
    flex-direction: column;
}

.param-card-name {
    font-size: 0.84rem;
    font-weight: 700;
    color: #1E293B;
    line-height: 1.2;
}

.param-card-weight {
    font-size: 0.66rem;
    color: #64748B;
    font-weight: 600;
}

.param-bar-wrapper {
    flex: 1;
    margin: 0 16px;
}

.param-progress-track {
    height: 10px;
    background: #F1F5F9;
    border-radius: 999px;
    overflow: hidden;
    position: relative;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05);
}

.param-progress-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.param-score-pill {
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 800;
    min-width: 52px;
    text-align: center;
    border: 1px solid;
    letter-spacing: 0.01em;
}

.param-score-pill.strong {
    background: #ECFDF5;
    color: #059669;
    border-color: #A7F3D0;
}

.param-score-pill.moderate {
    background: #FFFBEB;
    color: #D97706;
    border-color: #FDE68A;
}

.param-score-pill.weak {
    background: #FEF2F2;
    color: #DC2626;
    border-color: #FECACA;
}

/* 4 Diagnostic Sections (2 Boxes Per Frame - 2x2 Grid) */
.diag-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin-top: 14px;
    width: 100%;
    align-items: stretch;
}
.diag-card {
    border-radius: 14px;
    padding: 18px 18px;
    border: 1px solid;
    height: 100%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.03);
    transition: all 0.25s ease;
}
.diag-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(0, 0, 0, 0.06);
}
.diag-card.strengths {
    background: linear-gradient(180deg, #F0FDF4 0%, #FFFFFF 100%);
    border-color: #86EFAC;
    border-top: 4px solid #10B981;
}
.diag-card.weaknesses {
    background: linear-gradient(180deg, #FEF2F2 0%, #FFFFFF 100%);
    border-color: #FECACA;
    border-top: 4px solid #EF4444;
}
.diag-card.causes {
    background: linear-gradient(180deg, #F0F9FF 0%, #FFFFFF 100%);
    border-color: #BAE6FD;
    border-top: 4px solid #0EA5E9;
}
.diag-card.improvements {
    background: linear-gradient(180deg, #FFFBEB 0%, #FFFFFF 100%);
    border-color: #FDE68A;
    border-top: 4px solid #F59E0B;
}

.diag-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(0,0,0,0.06);
}
.diag-title {
    font-size: 0.92rem;
    font-weight: 800;
    display: flex;
    align-items: center;
    gap: 7px;
}
.diag-card.strengths .diag-title { color: #166534; }
.diag-card.weaknesses .diag-title { color: #991B1B; }
.diag-card.causes .diag-title { color: #075985; }
.diag-card.improvements .diag-title { color: #92400E; }

.diag-pill-badge {
    font-size: 0.7rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 20px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
.diag-card.strengths .diag-pill-badge {
    background: #DCFCE7;
    color: #15803D;
    border: 1px solid #BBF7D0;
}
.diag-card.weaknesses .diag-pill-badge {
    background: #FEE2E2;
    color: #B91C1C;
    border: 1px solid #FECACA;
}
.diag-card.causes .diag-pill-badge {
    background: #E0F2FE;
    color: #0369A1;
    border: 1px solid #BAE6FD;
}
.diag-card.improvements .diag-pill-badge {
    background: #FEF3C7;
    color: #B45309;
    border: 1px solid #FDE68A;
}

.diag-item {
    font-size: 0.88rem;
    line-height: 1.55;
    margin-bottom: 12px;
    display: flex;
    align-items: flex-start;
    gap: 12px;
    word-break: break-word;
    overflow-wrap: break-word;
}
.diag-item:last-child {
    margin-bottom: 0;
}
.diag-item-icon-box {
    width: 22px;
    height: 22px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.78rem;
    font-weight: 800;
    flex-shrink: 0;
    margin-top: 1px;
}
.diag-card.strengths .diag-item-icon-box {
    background: #DCFCE7;
    color: #166534;
}
.diag-card.weaknesses .diag-item-icon-box {
    background: #FEE2E2;
    color: #991B1B;
}
.diag-card.causes .diag-item-icon-box {
    background: #E0F2FE;
    color: #075985;
}
.diag-card.improvements .diag-item-icon-box {
    background: #FEF3C7;
    color: #92400E;
}

.diag-item-body {
    flex: 1;
    min-width: 0;
}
.diag-param-chip {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 4px;
    margin-bottom: 3px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}
.diag-card.strengths .diag-param-chip { background: #DCFCE7; color: #15803D; }
.diag-card.weaknesses .diag-param-chip { background: #FEE2E2; color: #B91C1C; }
.diag-card.causes .diag-param-chip { background: #E0F2FE; color: #0369A1; }
.diag-card.improvements .diag-param-chip { background: #FEF3C7; color: #B45309; }

.diag-item-text {
    font-size: 0.82rem;
    color: #334155;
    line-height: 1.45;
}
.diag-card.strengths .diag-item-text { color: #14532D; }
.diag-card.weaknesses .diag-item-text { color: #7F1D1D; }
.diag-card.causes .diag-item-text { color: #0C4A6E; }
.diag-card.improvements .diag-item-text { color: #78350F; }

/* Step 5 Comparison (Sleek SaaS AI Theme - Distinct Violet/Purple Palette) */
.compare-card {
    border-radius: 14px;
    padding: 18px 16px;
    border: 1px solid;
    height: 100%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.03);
    transition: all 0.25s ease;
}
.compare-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(0, 0, 0, 0.06);
}
.compare-card.original {
    background: linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 100%);
    border-color: #CBD5E1;
    border-top: 4px solid #64748B;
}
.compare-card.optimized {
    background: linear-gradient(180deg, #F5F3FF 0%, #FFFFFF 100%);
    border-color: #BFDBFE;
    border-top: 4px solid #1D4ED8;
    box-shadow: 0 4px 14px rgba(139, 92, 246, 0.08);
}
.compare-card.optimized:hover {
    box-shadow: 0 10px 25px rgba(139, 92, 246, 0.16);
}
.compare-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(0,0,0,0.06);
}
.compare-title {
    font-size: 0.92rem;
    font-weight: 800;
    display: flex;
    align-items: center;
    gap: 7px;
}
.compare-card.original .compare-title { color: #334155; }
.compare-card.optimized .compare-title { color: #5B21B6; }

.compare-pill-badge {
    font-size: 0.7rem;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 20px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
.compare-card.original .compare-pill-badge {
    background: #F1F5F9;
    color: #475569;
    border: 1px solid #E2E8F0;
}
.compare-card.optimized .compare-pill-badge {
    background: #EFF6FF;
    color: #1E40AF;
    border: 1px solid #BFDBFE;
}

.compare-body {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.compare-content-text {
    font-size: 0.88rem;
    line-height: 1.55;
    color: #334155;
    white-space: pre-wrap;
    word-break: break-word;
    background: rgba(255, 255, 255, 0.7);
    border-radius: 10px;
    padding: 12px 14px;
    border: 1px solid rgba(0, 0, 0, 0.04);
}
.compare-card.optimized .compare-content-text {
    color: #1E1B4B;
    background: #FFFFFF;
    border: 1px solid #EFF6FF;
    font-weight: 500;
}

.compare-enhancements-box {
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px dashed #BFDBFE;
}
.compare-enhancements-title {
    font-size: 0.72rem;
    font-weight: 700;
    color: #1E40AF;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 5px;
}
.compare-enhancement-item {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    font-size: 0.78rem;
    color: #4C1D95;
    line-height: 1.4;
    margin-bottom: 4px;
}
.compare-enhancement-bullet {
    color: #1D4ED8;
    font-weight: 800;
    font-size: 0.75rem;
}

.compare-arrow-connector {
    display: flex;
    align-items: center;
    justify-content: center;
    padding-top: 16px;
}
.compare-arrow-circle {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #1D4ED8, #2563EB);
    color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    font-weight: 800;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.35);
    border: 2px solid #FFFFFF;
}

/* Sidebar "How It Works" Card */
.sidebar-how-card {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 14px;
    margin-top: 20px;
    margin-bottom: 15px;
}
.sidebar-how-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: #F8FAFC;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 7px;
}
.sidebar-how-step {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 11px;
    font-size: 0.78rem;
    color: #CBD5E1;
    line-height: 1.38;
}
.sidebar-how-step:last-child {
    margin-bottom: 0;
}
.sidebar-how-icon {
    width: 22px;
    height: 22px;
    border-radius: 6px;
    background: rgba(29, 100, 236, 0.22);
    color: #A5B4FC;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    flex-shrink: 0;
}
.sidebar-notice {
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 8px;
    padding: 10px;
    font-size: 0.73rem;
    color: #FCD34D;
    line-height: 1.38;
    margin-top: 12px;
}
.sidebar-notice strong {
    color: #FDE68A;
    display: block;
    margin-bottom: 2px;
}

/* Clean White Prompt Entry Box */
div[data-testid="stTextArea"] textarea,
div[data-baseweb="textarea"] textarea,
div[data-baseweb="textarea"] {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 10px !important;
    font-size: 0.95rem !important;
    line-height: 1.55 !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stTextArea"] textarea:focus,
div[data-baseweb="textarea"]:focus-within {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(29, 100, 236, 0.18) !important;
}

div[data-testid="stTextArea"] textarea::placeholder {
    color: #94A3B8 !important;
}

/* =========================================================================
   COMPREHENSIVE BUTTON STYLING - EXACT SAME ROYAL BLUE AS BRAND LOGO
   Logo Gradient: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)
   ========================================================================= */

/* Base Streamlit Button Resets & Unified Royal Blue Palette */
div.stButton > button,
button[data-testid="baseButton-primary"],
button[data-testid="baseButton-secondary"],
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-secondary"],
button[kind="primary"],
button[kind="secondary"],
div[data-testid="stSidebar"] div.stButton > button,
div[data-testid="stSidebar"] button,
.sidebar-nav-wrapper .stButton > button,
.sidebar-logout-wrapper button,
.tabs-buttons-wrapper .stButton > button,
div[data-testid="stFormSubmitButton"] > button,
div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border: 1px solid #1D4ED8 !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 1.02rem !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    height: 44px !important;
    min-height: 44px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    padding: 0 14px !important;
    vertical-align: middle !important;
}

/* Ensure Step 5 comparison columns align at the top */
div[data-testid="stHorizontalBlock"]:has(.compare-card) {
    align-items: flex-start !important;
}

/* Ensure modal close buttons never get a background, height, or blue strip */
div[data-testid="stDialog"] button[aria-label="Close"],
div[data-testid="stDialog"] button[data-testid*="header"],
div[data-testid="stDialog"] [data-testid="stDialogHeader"],
div[data-testid="stDialog"] [data-testid="stModalHeader"],
button[aria-label="Close"],
button[data-testid="baseButton-header"],
button[data-testid="stBaseButton-header"] {
    display: none !important;
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    width: 0 !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Ensure ALL button text and icons are 100% bright white, crisp, and properly sized */
div.stButton > button p,
div.stButton > button span,
div.stButton > button div,
button[data-testid="baseButton-primary"] p,
button[data-testid="baseButton-secondary"] p,
button[data-testid="stBaseButton-primary"] p,
button[data-testid="stBaseButton-secondary"] p,
button[kind="primary"] p,
button[kind="secondary"] p,
button[data-testid="baseButton-primary"] span,
button[data-testid="baseButton-secondary"] span,
button[data-testid="stBaseButton-primary"] span,
button[data-testid="stBaseButton-secondary"] span,
button[kind="primary"] span,
button[kind="secondary"] span,
div[data-testid="stSidebar"] button p,
div[data-testid="stSidebar"] button span,
.sidebar-nav-wrapper button p,
.sidebar-nav-wrapper button span,
.sidebar-logout-wrapper button p,
.sidebar-logout-wrapper button span,
.tabs-buttons-wrapper button p,
.tabs-buttons-wrapper button span,
div[data-testid="stFormSubmitButton"] > button p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 1.02rem !important;
    letter-spacing: 0.02em !important;
    line-height: 1.35 !important;
    -webkit-font-smoothing: antialiased !important;
}

/* Sidebar Nav & Logout Buttons: Generous spacing, larger text, no truncation */
div[data-testid="stSidebar"] div.stButton > button,
.sidebar-nav-wrapper .stButton > button,
.sidebar-logout-wrapper button {
    padding: 0 8px !important;
    white-space: nowrap !important;
}
div[data-testid="stSidebar"] button p,
div[data-testid="stSidebar"] button span,
.sidebar-nav-wrapper button p,
.sidebar-nav-wrapper button span,
.sidebar-logout-wrapper button p,
.sidebar-logout-wrapper button span {
    font-size: 1.02rem !important;
    letter-spacing: 0.02em !important;
    font-weight: 700 !important;
    white-space: nowrap !important;
}

/* Hover State across all buttons */
div.stButton > button:hover,
button[data-testid="baseButton-primary"]:hover,
button[data-testid="baseButton-secondary"]:hover,
button[data-testid="stBaseButton-primary"]:hover,
button[data-testid="stBaseButton-secondary"]:hover,
button[kind="primary"]:hover,
button[kind="secondary"]:hover,
div[data-testid="stSidebar"] div.stButton > button:hover,
div[data-testid="stSidebar"] button:hover,
.sidebar-nav-wrapper .stButton > button:hover,
.sidebar-logout-wrapper button:hover,
.tabs-buttons-wrapper .stButton > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
    background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
    background-color: #1D4ED8 !important;
    border-color: #1E40AF !important;
    color: #FFFFFF !important;
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.48) !important;
    transform: translateY(-1px) !important;
}

/* Active Highlight Ring (For Selected Nav item or Active Input Tab) */
button[data-testid="baseButton-primary"],
button[data-testid="stBaseButton-primary"],
button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"],
.stButton > button[kind="primary"] {
    border: 2px solid #FFFFFF !important;
    box-shadow: 0 0 0 3px rgba(147, 197, 253, 0.45), 0 4px 16px rgba(37, 99, 235, 0.5) !important;
}

div.stButton > button:active,
button:active {
    transform: translateY(0px) !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3) !important;
}

/* Hide default redundant Streamlit input instructions */
div[data-testid="InputInstructions"] {
    display: none !important;
}

/* Polished Live Character Counter */
.char-counter-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 4px;
    padding: 2px 0;
    user-select: none;
    min-height: 40px;
}

.char-counter-text {
    font-size: 0.84rem;
    font-weight: 500;
    color: #64748B;
    display: flex;
    align-items: center;
    gap: 5px;
    letter-spacing: 0.01em;
    line-height: 1.35;
    transition: color 0.15s ease;
}

.char-counter-progress-bar {
    width: 140px;
    height: 4px;
    background-color: #E2E8F0;
    border-radius: 999px;
    overflow: hidden;
}

.char-counter-progress-fill {
    height: 100%;
    background-color: #2563EB;
    border-radius: 999px;
    transition: width 0.1s ease, background-color 0.2s ease;
}

/* Background live monitoring component styling */
iframe[title="streamlit.components.v1.html"],
iframe[title="st.iframe"] {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def render_live_monitor_component():
    """Injects client-side real-time live prompt word & character monitoring via iframe with parent access."""
    js_code = """
    <script>
    (function() {
        function setupLiveCounter() {
            let parentDoc;
            try {
                parentDoc = (window.parent && window.parent.document) ? window.parent.document : null;
            } catch (err) {
                parentDoc = null;
            }
            if (!parentDoc) return;

            const textarea = parentDoc.querySelector('div[data-testid="stTextArea"] textarea');
            const containers = parentDoc.querySelectorAll('.char-counter-container');
            if (!textarea || containers.length === 0) return;

            function formatNum(n) {
                return (n || 0).toLocaleString();
            }

            function countWords(str) {
                const trimmed = (str || "").trim();
                if (!trimmed) return 0;
                return trimmed.split(/\\s+/).length;
            }

            function updateDisplays() {
                const maxLimit = 2000;
                let val = textarea.value || "";
                if (val.length > maxLimit) {
                    val = val.substring(0, maxLimit);
                    textarea.value = val;
                }

                const chars = val.length;
                const words = countWords(val);
                const pct = Math.min(100, Math.round((chars / maxLimit) * 1000) / 10);
                const wordLabel = words === 1 ? '1 word' : formatNum(words) + ' words';
                const charLabel = formatNum(chars) + '/' + formatNum(maxLimit) + ' characters';

                containers.forEach(container => {
                    const textEl = container.querySelector('.char-counter-text');
                    const fillEl = container.querySelector('.char-counter-progress-fill');
                    if (!textEl) return;

                    if (chars >= maxLimit) {
                        textEl.innerHTML = '<span style="color:#DC2626; font-weight:700;">🛑 ' + wordLabel + ' • ' + formatNum(maxLimit) + '/' + formatNum(maxLimit) + ' characters (limit reached)</span>';
                        if (fillEl) {
                            fillEl.style.width = '100%';
                            fillEl.style.backgroundColor = '#DC2626';
                        }
                    } else if (chars >= Math.floor(maxLimit * 0.9)) {
                        const rem = maxLimit - chars;
                        textEl.innerHTML = '<span style="color:#D97706; font-weight:700;">⚠️ ' + wordLabel + ' • ' + charLabel + ' (' + formatNum(rem) + ' left)</span>';
                        if (fillEl) {
                            fillEl.style.width = pct + '%';
                            fillEl.style.backgroundColor = '#F59E0B';
                        }
                    } else {
                        textEl.innerHTML = '<span style="font-weight:600; color:#334155;">' + wordLabel + '</span> <span style="color:#94A3B8; margin:0 4px;">•</span> <span style="color:#64748B;">' + charLabel + '</span>';
                        if (fillEl) {
                            fillEl.style.width = pct + '%';
                            fillEl.style.backgroundColor = '#2563EB';
                        }
                    }
                });
            }

            // Bind listeners if not already bound on this textarea element
            if (!textarea.__pcLiveAttached) {
                textarea.__pcLiveAttached = true;
                textarea.addEventListener('input', updateDisplays);
                textarea.addEventListener('keyup', updateDisplays);
                textarea.addEventListener('paste', () => setTimeout(updateDisplays, 25));
                textarea.addEventListener('cut', () => setTimeout(updateDisplays, 25));
                textarea.addEventListener('change', updateDisplays);
            }

            // Bind instant client-side clipboard copy on the Copy button
            const copyBtns = parentDoc.querySelectorAll('div.stButton button');
            copyBtns.forEach(btn => {
                const btnText = (btn.innerText || btn.textContent || '').trim();
                if (btnText.includes('Copy Optimized Prompt') && !btn.__pcCopyBound) {
                    btn.__pcCopyBound = true;
                    btn.addEventListener('click', function() {
                        const optCard = parentDoc.querySelector('.compare-card.optimized .compare-content-text');
                        if (optCard) {
                            const val = (optCard.innerText || optCard.textContent || '').trim();
                            if (val) {
                                try {
                                    if (navigator.clipboard && navigator.clipboard.writeText) {
                                        navigator.clipboard.writeText(val);
                                    }
                                } catch(e) {}
                                try {
                                    const ta = parentDoc.createElement('textarea');
                                    ta.value = val;
                                    ta.style.position = 'fixed';
                                    ta.style.opacity = '0';
                                    ta.style.left = '-9999px';
                                    parentDoc.body.appendChild(ta);
                                    ta.focus();
                                    ta.select();
                                    parentDoc.execCommand('copy');
                                    parentDoc.body.removeChild(ta);
                                } catch(e) {}
                            }
                        }
                    });
                }
            });

            // Sync display immediately
            updateDisplays();
        }

        setInterval(setupLiveCounter, 120);
        setupLiveCounter();

        // Continuous Keep-Alive Heartbeat: Pings Streamlit server every 20s
        // Prevents browser tab sleeping, NAT drop, and Tornado WebSocket idle timeout
        function pingServerHeartbeat() {
            try {
                fetch('/_stcore/health', { method: 'GET', cache: 'no-store' }).catch(() => {});
            } catch(e) {}
        }
        setInterval(pingServerHeartbeat, 20000);
        pingServerHeartbeat();

        let pDoc;
        try { pDoc = (window.parent && window.parent.document) ? window.parent.document : document; } catch(e) { pDoc = document; }
        if (pDoc) {
            pDoc.addEventListener('visibilitychange', function() {
                if (pDoc.visibilityState === 'visible') pingServerHeartbeat();
            });
        }
    })();
    </script>
    """
    embed_script_component(js_code, height=0)

def render_char_counter_html(current_len: int, max_limit: int = 2000, container_id: str = "main", word_count: int = 0) -> str:
    """Renders a polished character & word count UI with live progress indicator."""
    current_len = max(0, min(current_len, max_limit))
    word_count = max(0, word_count)
    pct = min(100.0, round((current_len / max_limit) * 100, 1))
    
    word_label = f"{word_count:,} word" if word_count == 1 else f"{word_count:,} words"
    char_label = f"{current_len:,}/{max_limit:,} characters"
    
    if current_len >= max_limit:
        color = "#DC2626"
        label = f"🛑 <strong>{word_label} • {char_label} (limit reached)</strong>"
        bar_color = "#DC2626"
    elif current_len >= int(max_limit * 0.9):
        rem = max_limit - current_len
        color = "#D97706"
        label = f"⚠️ <strong>{word_label} • {char_label} ({rem:,} left)</strong>"
        bar_color = "#F59E0B"
    else:
        color = "#64748B"
        label = f"<span style='font-weight:600; color:#334155;'>{word_label}</span> <span style='color:#94A3B8; margin:0 4px;'>•</span> <span style='color:#64748B;'>{char_label}</span>"
        bar_color = "#2563EB"
        
    return f"""
    <div class="char-counter-container" id="char-counter-{container_id}">
        <div class="char-counter-text" style="color: {color};">{label}</div>
        <div class="char-counter-progress-bar">
            <div class="char-counter-progress-fill" style="width: {pct}%; background-color: {bar_color};"></div>
        </div>
    </div>
    """
def clean_cause_text(cause_str: str) -> str:
    """Strips any accidental suggestion/instruction phrasing from cause text."""
    if not cause_str:
        return ""
    text = cause_str.strip()
    # Strip recommendation clauses if appended
    for sep in [". Consider ", ". Try ", ". Tell the AI ", ". Explain who ", ". Please ", ". You should "]:
        if sep in text:
            text = text.split(sep)[0].strip()
            if not text.endswith("."):
                text += "."
    # Strip recommendation prefixes
    for prefix in [
        "Consider adding ", "Consider specifying ", "Consider ",
        "Try adding ", "Try to ", "Try ",
        "Tell the AI to ", "Tell the AI how ", "Tell the AI ",
        "Explain who this is for and why it is needed: ", "Explain who this is for and why it is needed",
        "Explain who this is for: ", "Explain who ",
        "Please add ", "Please specify "
    ]:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()
            if text:
                text = text[0].upper() + text[1:]
    return text


# Initialize Session State Variables
if "is_authenticated" not in st.session_state or not st.session_state.is_authenticated:
    saved_email = st.query_params.get("user")
    if saved_email:
        from backend.auth_service import _load_users
        all_users = _load_users()
        if saved_email in all_users:
            u_info = all_users[saved_email]
            st.session_state.is_authenticated = True
            st.session_state.current_user = {"name": u_info.get("name", "User"), "email": saved_email}
        elif saved_email == "demo@promptcraft.ai":
            st.session_state.is_authenticated = True
            st.session_state.current_user = {"name": "Demo User", "email": "demo@promptcraft.ai"}
        else:
            st.session_state.is_authenticated = False
    else:
        st.session_state.is_authenticated = False

if "auth_view" not in st.session_state:
    st.session_state.auth_view = "login"

if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "step" not in st.session_state:
    st.session_state.step = 1

if "user_prompt" not in st.session_state:
    st.session_state.user_prompt = ""

if "uploaded_doc" not in st.session_state:
    st.session_state.uploaded_doc = None

if "doc_text" not in st.session_state:
    st.session_state.doc_text = ""

if "evaluation_result" not in st.session_state:
    st.session_state.evaluation_result = None

if "ai_analysis" not in st.session_state:
    st.session_state.ai_analysis = None

if "optimized_prompt" not in st.session_state:
    st.session_state.optimized_prompt = None

if "saved_prompts_list" not in st.session_state:
    st.session_state.saved_prompts_list = []

if "image_session_id" not in st.session_state:
    st.session_state.image_session_id = 0

if "voice_session_id" not in st.session_state:
    st.session_state.voice_session_id = 0

if "ocr_extracted_text" not in st.session_state:
    st.session_state.ocr_extracted_text = ""

if "voice_transcribed_text" not in st.session_state:
    st.session_state.voice_transcribed_text = ""

if "last_uploaded_img_name" not in st.session_state:
    st.session_state.last_uploaded_img_name = None

if "last_transcribed_audio_hash" not in st.session_state:
    st.session_state.last_transcribed_audio_hash = None

def reset_prompt_temporary_states(clear_user_prompt: bool = False):
    """Clears temporary extraction/transcription inputs so Image & Voice tabs remain empty when unused."""
    st.session_state.ocr_extracted_text = ""
    st.session_state.last_uploaded_img_name = None
    st.session_state.image_session_id = st.session_state.get("image_session_id", 0) + 1
    
    st.session_state.voice_transcribed_text = ""
    st.session_state.last_transcribed_audio_hash = None
    st.session_state.voice_session_id = st.session_state.get("voice_session_id", 0) + 1
    
    if clear_user_prompt:
        st.session_state.user_prompt = ""
        st.session_state.uploaded_doc = None
        st.session_state.doc_text = ""
        st.session_state.evaluation_result = None
        st.session_state.ai_analysis = None
        st.session_state.optimized_prompt = None

# Auth Gate: Render Login/Signup if not logged in
if not st.session_state.is_authenticated:
    render_auth_page()
    st.stop()

# Real-time live prompt monitoring initialization
render_live_monitor_component()


# Sidebar Navigation
with st.sidebar:
    st.html(f"""
    <div class="sidebar-brand">
        <img src="data:image/png;base64,{BRAIN_LOGO_B64}" alt="PromptCraft Logo" class="sidebar-brand-logo-img" />
        <div class="sidebar-brand-text">
            <div class="brand-title">PromptCraft</div>
            <div class="brand-subtitle">Prompt Quality Evaluation & Learning System</div>
        </div>
    </div>
    """)
    
    # User profile and logout
    user_name = st.session_state.current_user.get("name", "User") if st.session_state.current_user else "User"
    user_email = st.session_state.current_user.get("email", "user@promptcraft.ai") if st.session_state.current_user else ""
    user_initial = user_name[0].upper() if user_name else "U"
    
    st.html(f"""
    <div style="display:flex; align-items:center; justify-content:space-between; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:8px 12px; margin-bottom:12px;">
        <div style="display:flex; align-items:center; gap:10px; min-width:0;">
            <div style="width:30px; height:30px; border-radius:50%; background:linear-gradient(135deg, #0284C7, #2563EB); display:flex; align-items:center; justify-content:center; font-weight:700; color:#FFFFFF; font-size:0.8rem; flex-shrink:0;">{user_initial}</div>
            <div style="display:flex; flex-direction:column; min-width:0; overflow:hidden;">
                <span style="font-size:0.82rem; font-weight:700; color:#FFFFFF; line-height:1.2; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">{user_name}</span>
                <span style="font-size:0.68rem; color:#94A3B8; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">{user_email}</span>
            </div>
        </div>
    </div>
    """)
    
    st.html('<div class="sidebar-logout-wrapper">')
    if st.button("🚪 Log Out", key="btn_sidebar_logout", use_container_width=True):
        st.session_state.is_authenticated = False
        st.session_state.current_user = None
        if "user" in st.query_params:
            del st.query_params["user"]
        st.rerun()
    st.html('</div>')

    if "current_nav_view" not in st.session_state:
        st.session_state.current_nav_view = "eval"
        
    st.markdown("<div style='margin-top: 10px; margin-bottom: 8px;'></div>", unsafe_allow_html=True)
    st.html('<div class="sidebar-nav-wrapper">')
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("⚡ Evaluate", key="nav_btn_eval", use_container_width=True, type="primary" if st.session_state.current_nav_view == "eval" else "secondary"):
            st.session_state.current_nav_view = "eval"
            st.rerun()
    with col_nav2:
        if st.button("🕒 History", key="nav_btn_history", use_container_width=True, type="primary" if st.session_state.current_nav_view == "history" else "secondary"):
            st.session_state.current_nav_view = "history"
            st.rerun()
    
    st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)
    if st.button("💾 Saved Prompts", key="nav_btn_saved_prompts", use_container_width=True, type="primary" if st.session_state.current_nav_view == "saved_prompts" else "secondary"):
        st.session_state.current_nav_view = "saved_prompts"
        st.rerun()
    st.html('</div>')
    
    st.html("""
    <div class="sidebar-how-card">
        <div class="sidebar-how-title">
            <span>💡</span> <span>How It Works</span>
        </div>
        
        <div class="sidebar-how-step">
            <div class="sidebar-how-icon">🔍</div>
            <span>Enter your prompt in any format you prefer.</span>
        </div>
        
        <div class="sidebar-how-step">
            <div class="sidebar-how-icon">📎</div>
            <span>Add reference material (optional).</span>
        </div>
        
        <div class="sidebar-how-step">
            <div class="sidebar-how-icon">⚙️</div>
            <span>Evaluate your prompt using our evaluation engine.</span>
        </div>
        
        <div class="sidebar-how-step">
            <div class="sidebar-how-icon">🧠</div>
            <span>Get AI analysis with strengths, weaknesses, causes & improvements.</span>
        </div>
        
        <div class="sidebar-how-step">
            <div class="sidebar-how-icon">🚀</div>
            <span>View optimized prompt and use it for better results.</span>
        </div>
    </div>
    """)


# If user selected Evaluation History view
if st.session_state.get("current_nav_view") == "history":
    render_history_view(user_email)
    st.stop()

# If user selected Saved Prompts view
if st.session_state.get("current_nav_view") == "saved_prompts":
    render_saved_prompts_view(user_email)
    st.stop()

# Top Header Bar for New Evaluation
st.markdown("<h2 style='margin:0 0 14px 0; color:#0F172A; font-weight:800; font-size:1.5rem;'>New Evaluation</h2>", unsafe_allow_html=True)


# Main Content Area
main_container = st.container()
with main_container:
    # -------------------------------------------------------------
    # TOP STEPPER BAR
    # -------------------------------------------------------------
    cur_step = 5 if st.session_state.step >= 3 else st.session_state.step
    st.html(f"""
    <div class="stepper-container">
        <div class="step-item {'completed' if cur_step > 1 else ('active' if cur_step == 1 else '')}">
            <div class="step-circle">{'✓' if cur_step > 1 else '1'}</div>
            <span>Prompt</span>
        </div>
        <div class="step-divider {'active' if cur_step > 1 else ''}"></div>
        <div class="step-item {'completed' if cur_step > 2 else ('active' if cur_step == 2 else '')}">
            <div class="step-circle">{'✓' if cur_step > 2 else '2'}</div>
            <span>Reference</span>
        </div>
        <div class="step-divider {'active' if cur_step > 2 else ''}"></div>
        <div class="step-item {'completed' if cur_step > 3 else ('active' if cur_step == 3 else '')}">
            <div class="step-circle">{'✓' if cur_step > 3 else '3'}</div>
            <span>Evaluate</span>
        </div>
        <div class="step-divider {'active' if cur_step > 4 else ''}"></div>
        <div class="step-item {'completed' if cur_step > 4 else ('active' if cur_step == 4 else '')}">
            <div class="step-circle">{'✓' if cur_step > 4 else '4'}</div>
            <span>AI Analysis</span>
        </div>
        <div class="step-divider {'active' if cur_step == 5 else ''}"></div>
        <div class="step-item {'completed' if cur_step == 5 else ''}">
            <div class="step-circle">{'✓' if cur_step == 5 else '5'}</div>
            <span>Optimized Prompt</span>
        </div>
    </div>
    """)

    # -------------------------------------------------------------
    # STEP 1: Enter Your Prompt
    # -------------------------------------------------------------
    st.html("""
    <div class="step-card" style="margin-bottom: 8px;">
        <div class="step-title">1. Enter Your Prompt</div>
        <div class="step-subtitle">Choose how you want to provide your prompt: direct text, image screenshot (OCR), or live microphone dictation.</div>
    </div>
    """)
    
    if st.session_state.step == 1:
        if "active_prompt_tab" not in st.session_state:
            st.session_state.active_prompt_tab = "text"
            
        cur_tab = st.session_state.active_prompt_tab
        
        # -------------------------------------------------------------
        # 3 Equal-Length Tab Blocks (Exact 1:1:1 length, 100% visible text)
        # -------------------------------------------------------------
        st.html('<div class="tabs-buttons-wrapper">')
        tab_col1, tab_col2, tab_col3 = st.columns(3)
        with tab_col1:
            if st.button("📝 Text Input", key="tab_btn_text", use_container_width=True, type="primary" if cur_tab == "text" else "secondary"):
                st.session_state.active_prompt_tab = "text"
                st.rerun()
        with tab_col2:
            if st.button("🖼️ Image Input", key="tab_btn_image", use_container_width=True, type="primary" if cur_tab == "image" else "secondary"):
                st.session_state.active_prompt_tab = "image"
                img_key = f"uploader_img_prompt_{st.session_state.get('image_session_id', 0)}"
                if not st.session_state.get(img_key):
                    st.session_state.ocr_extracted_text = ""
                st.rerun()
        with tab_col3:
            if st.button("🎙️ Live Voice", key="tab_btn_voice", use_container_width=True, type="primary" if cur_tab == "voice" else "secondary"):
                st.session_state.active_prompt_tab = "voice"
                voice_key = f"voice_mic_input_{st.session_state.get('voice_session_id', 0)}"
                if not st.session_state.get(voice_key):
                    st.session_state.voice_transcribed_text = ""
                    st.session_state.last_transcribed_audio_hash = None
                st.rerun()
        st.html('</div>')
                
        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
        
        # -------------------------------------------------------------
        # 1. TEXT INPUT VIEW
        # -------------------------------------------------------------
        if cur_tab == "text":
            st.html("""
            <div class="voice-card-title">Write or enter your prompt</div>
            """)
            
            _, text_col, _ = st.columns([0.65, 2.0, 0.65])
            with text_col:
                with st.container(border=True):
                    st.html(f"""
                    <div class="voice-card-inner">
                        <div class="voice-mic-badge">
                            <img src="data:image/png;base64,{TEXT_EMOJI_B64}" alt="Text Prompt Emoji" class="text-prompt-img" />
                        </div>
                        
                        <div class="voice-waveform-preview">
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                            <span class="wave-bar"></span>
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                        </div>
                        
                        <div class="voice-instruction-label">Type or paste your prompt below</div>
                    </div>
                    """)
                    
                    prompt_input = st.text_area(
                        label="Prompt Text",
                        value=st.session_state.user_prompt or "Explain machine learning with some good examples.",
                        height=130,
                        max_chars=2000,
                        placeholder="Enter your prompt here...",
                        key="direct_text_prompt_input",
                        label_visibility="collapsed"
                    )
                    char_count = len(prompt_input) if prompt_input else 0
                    word_count = len(prompt_input.strip().split()) if prompt_input and prompt_input.strip() else 0
                    col_cnt, col_btn = st.columns([6, 4])
                    with col_cnt:
                        st.html(render_char_counter_html(char_count, 2000, "text", word_count=word_count))
                        render_live_monitor_component()
                    with col_btn:
                        if st.button("Use This Prompt →", key="btn_use_prompt_text", use_container_width=True, type="primary"):
                            cleaned_prompt = prompt_input.strip() if prompt_input else ""
                            if not cleaned_prompt:
                                st.warning("Please enter a valid prompt before continuing.")
                            elif len(cleaned_prompt) < 3:
                                st.warning("Prompt is too short (minimum 3 characters required).")
                            elif len(cleaned_prompt) > 2000:
                                st.error("Prompt exceeds the maximum allowed length of 2,000 characters.")
                            else:
                                st.session_state.user_prompt = cleaned_prompt[:2000]
                                st.session_state.evaluation_result = None
                                st.session_state.ai_analysis = None
                                st.session_state.optimized_prompt = None
                                st.session_state.step = 2
                                reset_prompt_temporary_states(clear_user_prompt=False)
                                st.rerun()

        # -------------------------------------------------------------
        # 2. UPLOAD IMAGE INPUT VIEW (OCR Extraction)
        # -------------------------------------------------------------
        elif cur_tab == "image":
            st.html("""
            <div class="voice-card-title">Upload your prompt using image</div>
            """)
            
            _, img_col, _ = st.columns([0.65, 2.0, 0.65])
            with img_col:
                with st.container(border=True):
                    st.html(f"""
                    <div class="voice-card-inner">
                        <div class="voice-mic-badge">
                            <img src="data:image/png;base64,{IMAGE_EMOJI_B64}" alt="Image Prompt Emoji" class="image-prompt-img" />
                        </div>
                        
                        <div class="voice-waveform-preview">
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                            <span class="wave-bar"></span>
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                        </div>
                        
                        <div class="voice-instruction-label">Click the button or drag and drop your image</div>
                    </div>
                    """)
                    
                    img_widget_key = f"uploader_img_prompt_{st.session_state.get('image_session_id', 0)}"
                    img_file = st.file_uploader(
                        "Upload prompt image (PNG, JPG, JPEG, WEBP)",
                        type=["png", "jpg", "jpeg", "webp", "bmp"],
                        key=img_widget_key,
                        label_visibility="collapsed"
                    )
                    
                    if not img_file:
                        st.session_state.last_uploaded_img_name = None
                        st.session_state.ocr_extracted_text = ""
                    else:
                        if st.session_state.get("last_uploaded_img_name") != img_file.name:
                            st.session_state.last_uploaded_img_name = img_file.name
                            st.session_state.ocr_extracted_text = ""
                        st.image(img_file, caption=f"📷 {img_file.name}", use_container_width=True)
                        if st.button("🔍 Extract Text from Image", key="btn_run_ocr", use_container_width=True, type="primary"):
                            with st.spinner("⚡ Extracting text from image via OCR Engine..."):
                                ocr_res = extract_text_from_image(img_file)
                                if ocr_res["status"] == "success":
                                    img_text_key = f"input_img_prompt_{st.session_state.get('image_session_id', 0)}"
                                    st.session_state.ocr_extracted_text = ocr_res["extracted_text"]
                                    st.session_state[img_text_key] = ocr_res["extracted_text"]
                                    st.toast("Text extracted successfully! 📸", icon="📸")
                                    st.rerun()
                                elif ocr_res["status"] == "warning":
                                    st.warning(ocr_res["error"])
                                else:
                                    st.error(ocr_res["error"])
            
            # Review and edit box for image extraction
            st.html("""
            <div style="display:flex; align-items:center; gap:6px; font-size:0.92rem; font-weight:700; color:#0F172A; margin-top:14px; margin-bottom:6px;">
                <span>✏️</span> <span>Extracted Prompt Review & Edit</span>
            </div>
            """)
            img_text_key = f"input_img_prompt_{st.session_state.get('image_session_id', 0)}"
            if img_text_key not in st.session_state:
                st.session_state[img_text_key] = st.session_state.get("ocr_extracted_text", "")
            
            img_prompt_val = st.text_area(
                label="Extracted Prompt Review",
                height=140,
                max_chars=2000,
                placeholder="Extracted text from image will appear here. Review and edit before evaluating...",
                key=img_text_key,
                label_visibility="collapsed",
                help="Review and modify the extracted text if any OCR correction is needed."
            )
            img_char_count = len(img_prompt_val) if img_prompt_val else 0
            img_word_count = len(img_prompt_val.strip().split()) if img_prompt_val and img_prompt_val.strip() else 0
            c1_img, c2_img = st.columns([7, 3])
            with c1_img:
                st.html(render_char_counter_html(img_char_count, 2000, "image", word_count=img_word_count))
                render_live_monitor_component()
            with c2_img:
                if st.button("Use This Prompt →", key="btn_use_img_prompt", use_container_width=True, type="primary"):
                    cleaned_img_prompt = img_prompt_val.strip() if img_prompt_val else ""
                    if not cleaned_img_prompt:
                        st.warning("Please extract or enter a prompt before proceeding.")
                    elif len(cleaned_img_prompt) < 3:
                        st.warning("Prompt is too short (minimum 3 characters required).")
                    elif len(cleaned_img_prompt) > 2000:
                        st.error("Prompt exceeds the maximum allowed length of 2,000 characters.")
                    else:
                        st.session_state.user_prompt = cleaned_img_prompt[:2000]
                        st.session_state.evaluation_result = None
                        st.session_state.ai_analysis = None
                        st.session_state.optimized_prompt = None
                        st.session_state.step = 2
                        reset_prompt_temporary_states(clear_user_prompt=False)
                        st.rerun()

        # -------------------------------------------------------------
        # 3. LIVE VOICE INPUT VIEW (Microphone Recording & Whisper Transcription)
        # -------------------------------------------------------------
        elif cur_tab == "voice":
            st.html("""
            <div class="voice-card-title">Speak your prompt using microphone</div>
            """)
            
            _, mic_col, _ = st.columns([0.65, 2.0, 0.65])
            with mic_col:
                with st.container(border=True):
                    st.html(f"""
                    <div class="voice-card-inner">
                        <div class="voice-mic-badge">
                            <img src="data:image/png;base64,{VOICE_EMOJI_B64}" alt="Voice Prompt Emoji" class="voice-mic-img" />
                        </div>
                        
                        <div class="voice-waveform-preview">
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                            <span class="wave-bar"></span>
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                            <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                        </div>
                        
                        <div class="voice-instruction-label">Click the button and start speaking</div>
                    </div>
                    """)
                    
                    voice_widget_key = f"voice_mic_input_{st.session_state.get('voice_session_id', 0)}"
                    audio_data = st.audio_input("Record Voice Prompt", key=voice_widget_key, label_visibility="collapsed")
            
            # If no audio is currently recorded, review box must be empty
            if audio_data is None:
                st.session_state.voice_transcribed_text = ""
                st.session_state.last_transcribed_audio_hash = None
            else:
                audio_bytes = audio_data.getvalue()
                audio_hash = hash(audio_bytes)
                if st.session_state.get("last_transcribed_audio_hash") != audio_hash:
                    with st.spinner("⚡ Transcribing your voice with Whisper / Gemini Audio..."):
                        trans_res = transcribe_audio(audio_bytes)
                        st.session_state.last_transcribed_audio_hash = audio_hash
                        if trans_res["status"] == "success":
                            voice_text_key = f"input_voice_prompt_{st.session_state.get('voice_session_id', 0)}"
                            st.session_state.voice_transcribed_text = trans_res["text"]
                            st.session_state[voice_text_key] = trans_res["text"]
                            st.toast("Voice prompt transcribed successfully! 🎙️", icon="🎙️")
                            st.rerun()
                        else:
                            st.error(trans_res["error"])

            # Review and edit box for voice prompt
            st.html("""
            <div style="display:flex; align-items:center; gap:6px; font-size:0.92rem; font-weight:700; color:#0F172A; margin-top:14px; margin-bottom:6px;">
                <span>✏️</span> <span>Voice Prompt Review & Edit</span>
            </div>
            """)
            voice_text_key = f"input_voice_prompt_{st.session_state.get('voice_session_id', 0)}"
            if voice_text_key not in st.session_state:
                st.session_state[voice_text_key] = st.session_state.get("voice_transcribed_text", "")
                
            voice_prompt_val = st.text_area(
                label="Voice Prompt Review & Edit",
                height=140,
                max_chars=2000,
                placeholder="Your transcribed spoken words will appear here automatically. You can edit, fix typos, or add details...",
                key=voice_text_key,
                label_visibility="collapsed",
                help="Edit any misheard words here directly."
            )
            voice_char_count = len(voice_prompt_val) if voice_prompt_val else 0
            voice_word_count = len(voice_prompt_val.strip().split()) if voice_prompt_val and voice_prompt_val.strip() else 0
            c1_v, c2_v = st.columns([7, 3])
            with c1_v:
                st.html(render_char_counter_html(voice_char_count, 2000, "voice", word_count=voice_word_count))
                render_live_monitor_component()
            with c2_v:
                if st.button("Use This Prompt →", key="btn_use_voice_prompt", use_container_width=True, type="primary"):
                    cleaned_voice_prompt = voice_prompt_val.strip() if voice_prompt_val else ""
                    if not cleaned_voice_prompt:
                        st.warning("Please record your voice or enter a prompt before proceeding.")
                    elif len(cleaned_voice_prompt) < 3:
                        st.warning("Prompt is too short (minimum 3 characters required).")
                    elif len(cleaned_voice_prompt) > 2000:
                        st.error("Prompt exceeds the maximum allowed length of 2,000 characters.")
                    else:
                        st.session_state.user_prompt = cleaned_voice_prompt[:2000]
                        st.session_state.evaluation_result = None
                        st.session_state.ai_analysis = None
                        st.session_state.optimized_prompt = None
                        st.session_state.step = 2
                        reset_prompt_temporary_states(clear_user_prompt=False)
                        st.rerun()
    else:
        # Summary box with Edit Prompt button
        lock_col1, lock_col2 = st.columns([8.5, 1.5])
        with lock_col1:
            st.info(f"**Prompt**: {st.session_state.user_prompt}")
        with lock_col2:
            if st.button("Edit Prompt", key="btn_edit_prompt"):
                st.session_state.step = 1
                st.session_state.evaluation_result = None
                st.session_state.ai_analysis = None
                st.session_state.optimized_prompt = None
                st.session_state.active_prompt_tab = "text"
                reset_prompt_temporary_states(clear_user_prompt=False)
                st.rerun()

    # -------------------------------------------------------------
    # STEP 2: Reference Material (Optional)
    # -------------------------------------------------------------
    if st.session_state.step >= 2:
        # Helper to load cached base64 image strings
        def _get_b64_asset(asset_path: str) -> str:
            import base64
            p = Path(asset_path)
            if not p.is_absolute():
                p = Path(__file__).resolve().parent / asset_path
            if p.exists():
                with open(p, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            return ""

        pdf_3d_b64 = _get_b64_asset("assets/icon_pdf_3d.png")
        img_3d_b64 = _get_b64_asset("assets/icon_image_3d.png")
        docx_3d_b64 = _get_b64_asset("assets/icon_docx_3d.png")

        # Step 2 Header
        st.html("""
        <div class="step-card" style="margin-top: 14px; margin-bottom: 16px;">
            <div class="step-title">2. Reference Material (Optional)</div>
            <div class="step-subtitle" style="margin-bottom: 0;">Upload reference documents to provide additional context.</div>
        </div>
        """)
        
        if st.session_state.step == 2:
            if "ref_upload_tab" not in st.session_state:
                st.session_state.ref_upload_tab = "pdf"
                
            cur_tab = st.session_state.ref_upload_tab
            
            # CSS for exact 3D card layout and invisible click trigger
            st.markdown("""
            <style>
            div[data-testid="stColumn"]:has(.ref-card-pdf-col),
            div[data-testid="stColumn"]:has(.ref-card-img-col),
            div[data-testid="stColumn"]:has(.ref-card-docx-col) {
                position: relative !important;
            }

            div[data-testid="stColumn"]:has(.ref-card-pdf-col) div.stButton,
            div[data-testid="stColumn"]:has(.ref-card-img-col) div.stButton,
            div[data-testid="stColumn"]:has(.ref-card-docx-col) div.stButton {
                margin-top: -74px !important;
                height: 74px !important;
                min-height: 74px !important;
                position: relative !important;
                z-index: 20 !important;
                padding: 0 !important;
                margin-bottom: 0 !important;
            }

            div[data-testid="stColumn"]:has(.ref-card-pdf-col) div.stButton > button,
            div[data-testid="stColumn"]:has(.ref-card-img-col) div.stButton > button,
            div[data-testid="stColumn"]:has(.ref-card-docx-col) div.stButton > button {
                height: 74px !important;
                min-height: 74px !important;
                width: 100% !important;
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
                opacity: 0.0001 !important;
                cursor: pointer !important;
                border-radius: 14px !important;
                padding: 0 !important;
                margin: 0 !important;
            }

            div[data-testid="stColumn"]:has(.ref-card-pdf-col):hover .ref-3d-card,
            div[data-testid="stColumn"]:has(.ref-card-img-col):hover .ref-3d-card,
            div[data-testid="stColumn"]:has(.ref-card-docx-col):hover .ref-3d-card {
                transform: translateY(-2px);
                border-color: #60A5FA !important;
                box-shadow: 0 6px 20px rgba(29, 100, 236, 0.16) !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # ---------------------------------------------------------
            # 3 Exact 3D Reference Cards (Matching Original Design)
            # ---------------------------------------------------------
            col_pdf, col_img, col_docx = st.columns(3)
            
            with col_pdf:
                is_p = (cur_tab == "pdf")
                border_p = "#2563EB" if is_p else "#E2E8F0"
                bg_p = "#EFF6FF" if is_p else "#FFFFFF"
                shadow_p = "0 4px 16px rgba(37, 99, 235, 0.18)" if is_p else "0 1px 4px rgba(0,0,0,0.02)"
                badge_p = '<span style="color:#2563EB; font-size:10px; font-weight:800; background:#E0E7FF; padding:2px 8px; border-radius:999px; letter-spacing:0.03em;">ACTIVE</span>' if is_p else ''
                
                st.markdown("<div class='ref-card-pdf-col'></div>", unsafe_allow_html=True)
                st.html(f"""
                <div class="ref-3d-card" style="background:{bg_p}; border:2px solid {border_p}; border-radius:14px; padding:12px 14px; display:flex; align-items:center; gap:14px; box-shadow:{shadow_p}; min-height:74px; height:74px; box-sizing:border-box; transition:all 0.2s ease; cursor:pointer;">
                    <img src="data:image/png;base64,{pdf_3d_b64}" style="width:46px; height:46px; object-fit:contain; filter:drop-shadow(0 4px 8px rgba(225,29,72,0.22)); flex-shrink:0;" />
                    <div style="flex-grow:1; min-width:0;">
                        <div style="display:flex; align-items:center; justify-content:space-between; gap:4px;">
                            <span style="font-weight:800; font-size:0.96rem; color:#0F172A; white-space:nowrap;">Upload PDF</span>
                            {badge_p}
                        </div>
                        <div style="font-size:0.78rem; color:#64748B; margin-top:2px;">Supports PDF files</div>
                    </div>
                </div>
                """)
                if st.button(" ", key="btn_click_pdf", use_container_width=True):
                    st.session_state.ref_upload_tab = "pdf"
                    st.rerun()

            with col_img:
                is_i = (cur_tab == "image")
                border_i = "#2563EB" if is_i else "#E2E8F0"
                bg_i = "#EFF6FF" if is_i else "#FFFFFF"
                shadow_i = "0 4px 16px rgba(37, 99, 235, 0.18)" if is_i else "0 1px 4px rgba(0,0,0,0.02)"
                badge_i = '<span style="color:#2563EB; font-size:10px; font-weight:800; background:#E0E7FF; padding:2px 8px; border-radius:999px; letter-spacing:0.03em;">ACTIVE</span>' if is_i else ''
                
                st.markdown("<div class='ref-card-img-col'></div>", unsafe_allow_html=True)
                st.html(f"""
                <div class="ref-3d-card" style="background:{bg_i}; border:2px solid {border_i}; border-radius:14px; padding:12px 14px; display:flex; align-items:center; gap:14px; box-shadow:{shadow_i}; min-height:74px; height:74px; box-sizing:border-box; transition:all 0.2s ease; cursor:pointer;">
                    <img src="data:image/png;base64,{img_3d_b64}" style="width:46px; height:46px; object-fit:contain; filter:drop-shadow(0 4px 8px rgba(16,185,129,0.22)); flex-shrink:0;" />
                    <div style="flex-grow:1; min-width:0;">
                        <div style="display:flex; align-items:center; justify-content:space-between; gap:4px;">
                            <span style="font-weight:800; font-size:0.96rem; color:#0F172A; white-space:nowrap;">Upload Image</span>
                            {badge_i}
                        </div>
                        <div style="font-size:0.78rem; color:#64748B; margin-top:2px;">Supports JPG, PNG</div>
                    </div>
                </div>
                """)
                if st.button(" ", key="btn_click_img", use_container_width=True):
                    st.session_state.ref_upload_tab = "image"
                    st.rerun()

            with col_docx:
                is_d = (cur_tab == "docx")
                border_d = "#2563EB" if is_d else "#E2E8F0"
                bg_d = "#EFF6FF" if is_d else "#FFFFFF"
                shadow_d = "0 4px 16px rgba(37, 99, 235, 0.18)" if is_d else "0 1px 4px rgba(0,0,0,0.02)"
                badge_d = '<span style="color:#2563EB; font-size:10px; font-weight:800; background:#E0E7FF; padding:2px 8px; border-radius:999px; letter-spacing:0.03em;">ACTIVE</span>' if is_d else ''
                
                st.markdown("<div class='ref-card-docx-col'></div>", unsafe_allow_html=True)
                st.html(f"""
                <div class="ref-3d-card" style="background:{bg_d}; border:2px solid {border_d}; border-radius:14px; padding:12px 14px; display:flex; align-items:center; gap:14px; box-shadow:{shadow_d}; min-height:74px; height:74px; box-sizing:border-box; transition:all 0.2s ease; cursor:pointer;">
                    <img src="data:image/png;base64,{docx_3d_b64}" style="width:44px; height:44px; object-fit:contain; filter:drop-shadow(0 4px 8px rgba(37,99,235,0.22)); flex-shrink:0;" />
                    <div style="flex-grow:1; min-width:0;">
                        <div style="display:flex; align-items:center; justify-content:space-between; gap:4px;">
                            <span style="font-weight:800; font-size:0.96rem; color:#0F172A; white-space:nowrap;">Upload DOCX</span>
                            {badge_d}
                        </div>
                        <div style="font-size:0.78rem; color:#64748B; margin-top:2px;">Supports DOCX files</div>
                    </div>
                </div>
                """)
                if st.button(" ", key="btn_click_docx", use_container_width=True):
                    st.session_state.ref_upload_tab = "docx"
                    st.rerun()

            st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
            
            # ---------------------------------------------------------
            # Active File Uploader Dropzone
            # ---------------------------------------------------------
            if cur_tab == "pdf":
                uploaded_file = st.file_uploader(
                    "Upload PDF reference document",
                    type=["pdf"],
                    key="uploader_pdf_doc",
                    label_visibility="collapsed"
                )
            elif cur_tab == "image":
                uploaded_file = st.file_uploader(
                    "Upload Image reference document",
                    type=["png", "jpg", "jpeg", "webp"],
                    key="uploader_img_doc",
                    label_visibility="collapsed"
                )
            else:
                uploaded_file = st.file_uploader(
                    "Upload DOCX / TXT reference document",
                    type=["docx", "txt"],
                    key="uploader_docx_doc",
                    label_visibility="collapsed"
                )
                
            if uploaded_file is not None:
                if st.session_state.get("last_processed_doc_name") != uploaded_file.name:
                    with st.spinner("Processing reference document..."):
                        doc_res = process_document(uploaded_file, uploaded_file.name)
                        if doc_res["status"] == "success":
                            st.session_state.uploaded_doc = uploaded_file
                            st.session_state.last_processed_doc_name = uploaded_file.name
                            st.session_state.doc_text = doc_res.get("extracted_text") or doc_res.get("text", "")
                            st.session_state.doc_file_type = doc_res.get("file_type", cur_tab)
                            st.session_state.doc_file_size = getattr(uploaded_file, "size", 0)
                        else:
                            st.error(f"Error parsing document: {doc_res.get('error', 'Unknown error')}")

            # ---------------------------------------------------------
            # Uploaded References Section Card (Exact matching media_1789842769416.png)
            # ---------------------------------------------------------
            if st.session_state.get("uploaded_doc"):
                doc_obj = st.session_state.uploaded_doc
                doc_name = getattr(doc_obj, "name", "Reference_Document.pdf")
                doc_size_bytes = getattr(doc_obj, "size", len(st.session_state.get("doc_text", "").encode("utf-8")))
                if doc_size_bytes >= 1024 * 1024:
                    size_text = f"{round(doc_size_bytes / (1024 * 1024), 1)} MB"
                else:
                    size_text = f"{round(doc_size_bytes / 1024, 1)} KB"
                    
                ext_lower = doc_name.rsplit(".", 1)[-1].lower() if "." in doc_name else "pdf"
                if ext_lower == "pdf":
                    doc_badge_b64 = pdf_3d_b64
                elif ext_lower in ["png", "jpg", "jpeg", "webp"]:
                    doc_badge_b64 = img_3d_b64
                else:
                    doc_badge_b64 = docx_3d_b64

                st.html("""
                <div style="font-size: 1rem; font-weight: 700; color: #0F172A; margin-top: 16px; margin-bottom: 8px;">
                    Uploaded References
                </div>
                """)
                
                ref_item_col1, ref_item_col2 = st.columns([9.2, 0.8])
                with ref_item_col1:
                    st.html(f"""
                    <div style="background:#FFFFFF; border:1.5px solid #E2E8F0; border-radius:14px; padding:12px 18px; display:flex; align-items:center; gap:16px; box-shadow:0 1px 4px rgba(0,0,0,0.02);">
                        <img src="data:image/png;base64,{doc_badge_b64}" style="width:46px; height:46px; object-fit:contain; filter:drop-shadow(0 4px 8px rgba(0,0,0,0.08)); flex-shrink:0;" />
                        <div>
                            <div style="font-weight:700; font-size:0.95rem; color:#0F172A; word-break:break-all;">{doc_name}</div>
                            <div style="font-size:0.8rem; color:#64748B; margin-top:3px;">{size_text} • Uploaded just now</div>
                        </div>
                    </div>
                    """)
                with ref_item_col2:
                    st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️", key="btn_del_uploaded_doc_ref", help="Remove reference document"):
                        st.session_state.uploaded_doc = None
                        st.session_state.last_processed_doc_name = None
                        st.session_state.doc_text = ""
                        st.session_state.doc_file_size = 0
                        st.rerun()

            st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
            
            # ---------------------------------------------------------
            # Full-Width Evaluate & Optimize Button
            # ---------------------------------------------------------
            if st.button("🚀 Evaluate & Optimize Prompt", key="btn_eval_opt", use_container_width=True, type="primary"):
                # Prominent Animated Buffering & Progress Indicator
                status_placeholder = st.empty()
                with status_placeholder.container():
                    st.html("""
                    <div style="background: linear-gradient(135deg, #EFF6FF 0%, #F0F7FF 100%); border: 1.5px solid #DBEAFE; border-radius: 12px; padding: 18px 22px; margin: 16px 0; box-shadow: 0 4px 20px rgba(37, 99, 235, 0.12);">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div style="width: 14px; height: 14px; border-radius: 50%; background: #2563EB; box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.25);"></div>
                                <span style="font-size: 1rem; font-weight: 800; color: #1E1B4B; letter-spacing: -0.01em;">⚡ Evaluating Prompt Across 7 Orthogonal Analyzers & Gemini 3.7 Flash...</span>
                            </div>
                            <span style="font-size: 0.76rem; font-weight: 800; color: #2563EB; background: #E0E7FF; padding: 3px 10px; border-radius: 999px; letter-spacing: 0.04em;">PROCESSING</span>
                        </div>
                        <div style="font-size: 0.85rem; color: #3730A3; line-height: 1.5; margin-bottom: 12px;">
                            <strong>Multi-Stage Pipeline Active:</strong> Computing quantitative scores across 7 orthogonal dimensions (Grammar, Readability, Specificity, Context, Completeness, Clarity, Constraints), diagnosing structural weaknesses, and synthesizing an AI-optimized prompt rewrite.
                        </div>
                        <div style="width: 100%; height: 6px; background: #E0E7FF; border-radius: 999px; overflow: hidden;">
                            <div style="width: 100%; height: 100%; background: linear-gradient(90deg, #2563EB, #1D4ED8, #EC4899); border-radius: 999px;"></div>
                        </div>
                    </div>
                    """)
                
                # 1. Run Quantitative Evaluation (~1.5s)
                eval_res = evaluate_prompt(st.session_state.user_prompt)
                st.session_state.evaluation_result = eval_res
                
                # 2. Ingest Document into RAG if present
                rag_context = ""
                c_user = st.session_state.get("current_user", {})
                u_email = c_user.get("email", "demo@promptcraft.ai") if c_user else "demo@promptcraft.ai"
                
                if st.session_state.doc_text:
                    rag_mgr = get_rag_manager()
                    rag_mgr.clear()
                    doc_name = getattr(st.session_state.uploaded_doc, "name", "reference_document")
                    rag_mgr.add_document(
                        doc_name=doc_name,
                        full_text=st.session_state.doc_text,
                        user_email=u_email,
                        file_type=getattr(st.session_state, "doc_file_type", "pdf"),
                        file_size_bytes=getattr(st.session_state, "doc_file_size", 0)
                    )
                    retrieved_chunks = rag_mgr.retrieve_relevant_chunks(st.session_state.user_prompt, user_email=u_email, top_k=3)
                    rag_context = rag_mgr.format_context_for_prompt(retrieved_chunks)
                st.session_state.rag_context = rag_context
                
                # Live Stage 2 Progress: AI Diagnosis
                with status_placeholder.container():
                    st.html("""
                    <div style="background: linear-gradient(135deg, #EFF6FF 0%, #F0F7FF 100%); border: 1.5px solid #DBEAFE; border-radius: 12px; padding: 18px 22px; margin: 16px 0; box-shadow: 0 4px 20px rgba(37, 99, 235, 0.12);">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div style="width: 14px; height: 14px; border-radius: 50%; background: #2563EB; box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.25);"></div>
                                <span style="font-size: 1rem; font-weight: 800; color: #1E1B4B; letter-spacing: -0.01em;">🤖 Stage 2/3: Diagnosing Strengths, Weaknesses & Root Causes with AI...</span>
                            </div>
                            <span style="font-size: 0.76rem; font-weight: 800; color: #2563EB; background: #E0E7FF; padding: 3px 10px; border-radius: 999px; letter-spacing: 0.04em;">ANALYZING</span>
                        </div>
                        <div style="font-size: 0.85rem; color: #3730A3; line-height: 1.5; margin-bottom: 12px;">
                            <strong>AI Diagnosis:</strong> Identifying root causes across ambiguity, structural completeness, and prompt guardrails.
                        </div>
                        <div style="width: 100%; height: 6px; background: #E0E7FF; border-radius: 999px; overflow: hidden;">
                            <div style="width: 66%; height: 100%; background: linear-gradient(90deg, #2563EB, #6366F1); border-radius: 999px;"></div>
                        </div>
                    </div>
                    """)
                
                # 3. Run AI Diagnosis (~3s)
                diagnosis = analyze_weaknesses_and_improvements(
                    st.session_state.user_prompt,
                    eval_res
                )
                st.session_state.ai_analysis = diagnosis

                # Live Stage 3 Progress: Archetype Optimization
                with status_placeholder.container():
                    st.html("""
                    <div style="background: linear-gradient(135deg, #ECFDF5 0%, #F0FDF4 100%); border: 1.5px solid #A7F3D0; border-radius: 12px; padding: 18px 22px; margin: 16px 0; box-shadow: 0 4px 20px rgba(16, 185, 129, 0.12);">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div style="width: 14px; height: 14px; border-radius: 50%; background: #10B981; box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.25);"></div>
                                <span style="font-size: 1rem; font-weight: 800; color: #064E3B; letter-spacing: -0.01em;">✨ Stage 3/3: Crafting Your High-Impact Optimized Prompt...</span>
                            </div>
                            <span style="font-size: 0.76rem; font-weight: 800; color: #059669; background: #D1FAE5; padding: 3px 10px; border-radius: 999px; letter-spacing: 0.04em;">OPTIMIZING</span>
                        </div>
                        <div style="font-size: 0.85rem; color: #065F46; line-height: 1.5; margin-bottom: 12px;">
                            <strong>Prompt Optimization:</strong> Refining clarity, sharpening tone, and structuring key details for the best response (Target Score: 90+).
                        </div>
                        <div style="width: 100%; height: 6px; background: #D1FAE5; border-radius: 999px; overflow: hidden;">
                            <div style="width: 100%; height: 100%; background: linear-gradient(90deg, #10B981, #059669); border-radius: 999px;"></div>
                        </div>
                    </div>
                    """)

                # 4. Run Prompt Optimization (~3.5s)
                rewrite_res = rewrite_and_optimize_prompt(
                    original_prompt=st.session_state.user_prompt,
                    evaluation_payload=eval_res,
                    reference_context=rag_context,
                    ai_analysis=diagnosis
                )
                st.session_state.optimized_prompt = rewrite_res

                # 5. Persist to MongoDB
                try:
                    eval_doc_id = save_evaluation(
                        user_email=u_email,
                        prompt=st.session_state.user_prompt,
                        eval_result=eval_res,
                        input_type=st.session_state.get("active_prompt_tab", "text")
                    )
                    if eval_doc_id and rewrite_res:
                        save_optimization(
                            eval_id=eval_doc_id,
                            user_email=u_email,
                            optimized_prompt=rewrite_res.get("optimized_prompt", ""),
                            explanation=rewrite_res.get("explanation", "")
                        )
                except Exception as _db_err:
                    print(f"[MongoDB Save Note]: {_db_err}")

                # Clean transition to full evaluation dashboard
                status_placeholder.empty()
                st.session_state.step = 3
                st.rerun()
        else:
            if st.session_state.uploaded_doc:
                doc_name = getattr(st.session_state.uploaded_doc, "name", "Reference Document")
                ext_lower = doc_name.rsplit(".", 1)[-1].lower() if "." in doc_name else "pdf"
                if ext_lower == "pdf":
                    badge_b64 = pdf_3d_b64
                elif ext_lower in ["png", "jpg", "jpeg", "webp"]:
                    badge_b64 = img_3d_b64
                else:
                    badge_b64 = docx_3d_b64
                doc_size_kb = round(getattr(st.session_state.uploaded_doc, "size", 0) / 1024, 1)
                st.html(f"""
                <div style="display:flex; align-items:center; gap:12px; background:#F8FAFC; border:1.5px solid #E2E8F0; padding:10px 16px; border-radius:12px; margin-bottom:12px;">
                    <img src="data:image/png;base64,{badge_b64}" style="width:36px; height:36px; object-fit:contain; filter:drop-shadow(0 2px 4px rgba(0,0,0,0.06));" />
                    <div>
                        <div style="font-size:0.9rem; font-weight:700; color:#0F172A;">{doc_name}</div>
                        <div style="font-size:0.75rem; color:#64748B;">{doc_size_kb} KB • Reference Material Ingested</div>
                    </div>
                </div>
                """)

    # -------------------------------------------------------------
    # STEP 3: Prompt Evaluation Results
    # -------------------------------------------------------------
    if st.session_state.step >= 3 and st.session_state.evaluation_result:
        res = st.session_state.evaluation_result
        score = res["overall_score"]
        tier = res["quality_tier"]
        breakdown = res["scoring"]["breakdown"]
        
        # Calculate metric distribution counts
        strong_count = sum(1 for p in breakdown.values() if float(p.get("score", 0)) >= 8.0)
        mod_count = sum(1 for p in breakdown.values() if 5.0 <= float(p.get("score", 0)) < 8.0)
        weak_count = sum(1 for p in breakdown.values() if float(p.get("score", 0)) < 5.0)
        
        # SVG Radial circumference calculation (r = 54 -> C = 339.29)
        svg_r = 54
        svg_c = 2 * 3.14159265 * svg_r
        svg_dashoffset = svg_c * (1 - (score / 100))
        
        # Color & Tier styling
        if score >= 70:
            stroke_grad_start, stroke_grad_end = "#10B981", "#059669"
            tier_class = "strong"
            tier_icon = "🌟"
        elif score >= 50:
            stroke_grad_start, stroke_grad_end = "#F59E0B", "#D97706"
            tier_class = "moderate"
            tier_icon = "⚠️"
        else:
            stroke_grad_start, stroke_grad_end = "#EF4444", "#DC2626"
            tier_class = "weak"
            tier_icon = "🔴"
            
        PARAM_DISPLAY_NAMES = {
            "grammar": "Grammar",
            "readability": "Readability",
            "specificity": "Specificity",
            "context": "Context",
            "completeness": "Completeness",
            "ambiguity": "Clarity",
            "constraints": "Constraints"
        }
        
        PARAM_ICONS = {
            "grammar": "✍️",
            "readability": "📖",
            "specificity": "🎯",
            "context": "🌐",
            "completeness": "🧩",
            "ambiguity": "🔍",
            "constraints": "📏"
        }
        
        PARAM_WEIGHTS_LABEL = {
            "grammar": "1.0x Weight",
            "readability": "1.0x Weight",
            "specificity": "2.0x Weight",
            "context": "1.5x Weight",
            "completeness": "2.0x Weight",
            "ambiguity": "1.0x Weight",
            "constraints": "1.5x Weight"
        }

        st.html("""
        <div class="step-card" style="margin-top:10px;">
            <div class="step-title">3. Prompt Evaluation</div>
            <div class="step-subtitle">Comprehensive assessment across 7 Orthogonal Quality Parameters & Tiered Weighted Model.</div>
        </div>
        """)
        
        gauge_col, bars_col = st.columns([3.4, 6.6])
        
        with gauge_col:
            st.html(f"""
            <div class="score-hero-card {tier_class}">
                <div class="score-hero-header">Overall Quality Score</div>
                <div class="radial-gauge-container">
                    <div class="radial-gauge-ring" style="background: conic-gradient({stroke_grad_start} {score * 3.6}deg, #E2E8F0 {score * 3.6}deg 360deg);">
                        <div class="radial-gauge-inner">
                            <div style="font-size:2.5rem; font-weight:800; color:#0F172A; line-height:1; letter-spacing:-0.03em;">{score}</div>
                            <div style="font-size:0.75rem; font-weight:700; color:#64748B; margin-top:2px;">/ 100</div>
                        </div>
                    </div>
                </div>
                <div class="tier-pill-badge {tier_class}">
                    <span>{tier_icon}</span>
                    <span>{tier}</span>
                </div>
                <div class="score-stat-footer">
                    <span>⚖️ Weighted Model</span>
                    <span>•</span>
                    <span>{strong_count}/7 Strong</span>
                </div>
            </div>
            """)
            
        with bars_col:
            st.html("""
            <div class="param-list-header">
                <div class="param-list-title-wrap">
                    <span class="param-list-title">Parameter Breakdown</span>
                    <span class="param-list-badge">7 DIMENSIONS</span>
                </div>
                <div class="legend-chips-wrap">
                    <span class="legend-chip strong"><span class="legend-dot" style="background:#10B981;"></span> 8–10 Strong</span>
                    <span class="legend-chip moderate"><span class="legend-dot" style="background:#F59E0B;"></span> 5–7.9 Moderate</span>
                    <span class="legend-chip weak"><span class="legend-dot" style="background:#EF4444;"></span> 0–4.9 Weak</span>
                </div>
            </div>
            """)
            
            bars_html = ""
            for p_key, p_info in breakdown.items():
                p_score = float(p_info.get("score", 0))
                pct = int(p_score * 10)
                
                # Dynamic Score-Range Classification:
                if p_score >= 8.0:
                    pill_class = "strong"
                    fill_grad = "linear-gradient(90deg, #10B981 0%, #059669 100%)"
                elif p_score >= 5.0:
                    pill_class = "moderate"
                    fill_grad = "linear-gradient(90deg, #F59E0B 0%, #D97706 100%)"
                else:
                    pill_class = "weak"
                    fill_grad = "linear-gradient(90deg, #EF4444 0%, #DC2626 100%)"
                    
                icon = PARAM_ICONS.get(p_key, "📌")
                weight_lbl = PARAM_WEIGHTS_LABEL.get(p_key, "1.0x")
                label = PARAM_DISPLAY_NAMES.get(p_key, p_info.get("label", p_key.capitalize()))
                disp_val = int(p_score) if p_score.is_integer() else p_score
                
                bars_html += f"""
                <div class="param-card-row">
                    <div class="param-left-meta">
                        <div class="param-icon-chip">{icon}</div>
                        <div class="param-name-box">
                            <span class="param-card-name">{label}</span>
                            <span class="param-card-weight">{weight_lbl}</span>
                        </div>
                    </div>
                    <div class="param-bar-wrapper">
                        <div class="param-progress-track">
                            <div class="param-progress-fill" style="width: {pct}%; background: {fill_grad};"></div>
                        </div>
                    </div>
                    <div class="param-score-pill {pill_class}">{disp_val}/10</div>
                </div>
                """
            st.html(bars_html)

    # -------------------------------------------------------------
    # STEP 4: AI Prompt Analysis (Strengths, Weaknesses, Causes, Improvements)
    # -------------------------------------------------------------
    if st.session_state.step >= 3 and st.session_state.ai_analysis:
        ai_data = st.session_state.ai_analysis
        eval_res = st.session_state.evaluation_result or {}
        scoring = eval_res.get("scoring", {})
        breakdown = scoring.get("breakdown", {})
        
        strengths_items_html = []
        weaknesses_items_html = []
        causes_items_html = []
        improvements_items_html = []
        
        # Friendly description helpers for strong parameters
        STRONG_DESCRIPTIONS = {
            "Grammar & Syntax": "Grammar, punctuation, and syntax are clear and correct.",
            "Readability & Fluency": "Sentence structure is natural, concise, and easy to read.",
            "Specificity & Depth": "Includes concrete technical terms, parameters, and details.",
            "Context & Background": "Provides helpful project background and target audience details.",
            "Completeness": "Contains all fundamental components including task and structure.",
            "Clarity / Low Ambiguity": "Uses unambiguous, direct words with zero vague terms.",
            "Constraints & Guardrails": "Sets explicit rules, word boundaries, or output formatting."
        }

        # Build from structured parameter_analysis
        if "parameter_analysis" in ai_data and ai_data["parameter_analysis"]:
            for item in ai_data["parameter_analysis"]:
                p_name = item.get("parameter", "Parameter")
                p_status = item.get("status", "Weak")
                p_score = float(item.get("score", 0))
                p_weakness = item.get("weakness")
                p_cause = item.get("cause")
                p_imp = item.get("improvement")
                
                # Check if strong
                if p_status == "Strong" or p_score >= 7.0:
                    desc = p_imp if (p_imp and "maintain" not in p_imp.lower() and "criteria fully met" not in p_imp.lower()) else STRONG_DESCRIPTIONS.get(p_name, "Prompt meets high quality standards.")
                    strengths_items_html.append(f"""
                    <div class="diag-item">
                        <div class="diag-item-icon-box">✓</div>
                        <div class="diag-item-body">
                            <span class="diag-param-chip">{p_name}</span>
                            <div class="diag-item-text">{desc}</div>
                        </div>
                    </div>
                    """)
                else:
                    # Weakness
                    if p_weakness:
                        weaknesses_items_html.append(f"""
                        <div class="diag-item">
                            <div class="diag-item-icon-box">✕</div>
                            <div class="diag-item-body">
                                <span class="diag-param-chip">{p_name}</span>
                                <div class="diag-item-text">{p_weakness}</div>
                            </div>
                        </div>
                        """)
                    
                    # Cause (Strict pure root cause only)
                    if p_cause:
                        clean_c = clean_cause_text(p_cause)
                        if clean_c:
                            causes_items_html.append(f"""
                            <div class="diag-item">
                                <div class="diag-item-icon-box">🔍</div>
                                <div class="diag-item-body">
                                    <span class="diag-param-chip">{p_name}</span>
                                    <div class="diag-item-text">{clean_c}</div>
                                </div>
                            </div>
                            """)
                    
                    # Improvement (Actionable guidance)
                    if p_imp and "maintain" not in p_imp.lower() and "criteria fully met" not in p_imp.lower():
                        improvements_items_html.append(f"""
                        <div class="diag-item">
                            <div class="diag-item-icon-box">💡</div>
                            <div class="diag-item-body">
                                <span class="diag-param-chip">{p_name}</span>
                                <div class="diag-item-text">{p_imp}</div>
                            </div>
                        </div>
                        """)
        
        # Fallback safety if any list is empty
        if not strengths_items_html:
            strengths_items_html.append("""
            <div class="diag-item">
                <div class="diag-item-icon-box">✓</div>
                <div class="diag-item-body">
                    <span class="diag-param-chip">Core Intent</span>
                    <div class="diag-item-text">The basic topic and objective are stated.</div>
                </div>
            </div>
            """)
            
        if not weaknesses_items_html:
            weaknesses_items_html.append("""
            <div class="diag-item">
                <div class="diag-item-icon-box">✓</div>
                <div class="diag-item-body">
                    <span class="diag-param-chip">All Parameters</span>
                    <div class="diag-item-text">No major weaknesses or flaws detected in this prompt.</div>
                </div>
            </div>
            """)
            
        if not causes_items_html:
            causes_items_html.append("""
            <div class="diag-item">
                <div class="diag-item-icon-box">•</div>
                <div class="diag-item-body">
                    <span class="diag-param-chip">Evaluation Passed</span>
                    <div class="diag-item-text">All quality checks met or exceeded the required standards.</div>
                </div>
            </div>
            """)
            
        if not improvements_items_html:
            improvements_items_html.append("""
            <div class="diag-item">
                <div class="diag-item-icon-box">🚀</div>
                <div class="diag-item-body">
                    <span class="diag-param-chip">Best Practice</span>
                    <div class="diag-item-text">Keep using this well-defined prompt structure for your AI queries.</div>
                </div>
            </div>
            """)

        st.html("""
        <div class="step-card" style="margin-top:14px;">
            <div class="step-title">4. AI Prompt Analysis</div>
            <div class="step-subtitle">Clear AI-powered breakdown of what is working well, what is missing, and how to improve it.</div>
        </div>
        """)
        
        s_html = "".join(strengths_items_html)
        w_html = "".join(weaknesses_items_html)
        c_html = "".join(causes_items_html)
        i_html = "".join(improvements_items_html)
        
        st.html(f"""
        <div class="diag-grid">
            <div class="diag-card strengths">
                <div class="diag-header">
                    <div class="diag-title"><span>✨</span> <span>Strengths</span></div>
                    <span class="diag-pill-badge">{len(strengths_items_html)} Strong</span>
                </div>
                {s_html}
            </div>
            <div class="diag-card weaknesses">
                <div class="diag-header">
                    <div class="diag-title"><span>⚠️</span> <span>Weaknesses / Flaws</span></div>
                    <span class="diag-pill-badge">{len(weaknesses_items_html)} Areas</span>
                </div>
                {w_html}
            </div>
            <div class="diag-card causes">
                <div class="diag-header">
                    <div class="diag-title"><span>🔍</span> <span>Root Causes</span></div>
                    <span class="diag-pill-badge">Why It Occurred</span>
                </div>
                {c_html}
            </div>
            <div class="diag-card improvements">
                <div class="diag-header">
                    <div class="diag-title"><span>💡</span> <span>Suggested Improvements</span></div>
                    <span class="diag-pill-badge">Actionable Fixes</span>
                </div>
                {i_html}
            </div>
        </div>
        """)

    # -------------------------------------------------------------
    # STEP 5: Optimized Prompt
    # -------------------------------------------------------------
    if st.session_state.step >= 3 and st.session_state.optimized_prompt:
        opt_data = st.session_state.optimized_prompt
        optimized_text = opt_data.get("optimized_prompt", "")
        enhancements = opt_data.get("key_enhancements", [])
        is_already_opt = opt_data.get("already_optimized", False)
        status_msg = opt_data.get("status_message", "✨ This prompt is already optimized and meets high quality standards. You can use it directly with AI for accurate, high-quality results.")
        arch_badge = opt_data.get("detected_archetype")
        if not arch_badge or arch_badge == "✨ General Task":
            arch_key = classify_prompt_archetype(st.session_state.user_prompt)
            arch_info = ARCHETYPES.get(arch_key, ARCHETYPES["educational"])
            arch_badge = f"{arch_info['icon']} {arch_info['name']}"
        
        if is_already_opt:
            st.html(f"""
            <div class="step-card" style="margin-top:14px; border: 1.5px solid #10B981; background: linear-gradient(135deg, #ECFDF5 0%, #FFFFFF 100%);">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
                    <div style="display:flex; align-items:flex-start; gap:12px;">
                        <img src="data:image/png;base64,{TOP_TIER_EMOJI_B64}" alt="Top Tier Thumbs Up" style="width:48px; height:48px; object-fit:contain; flex-shrink:0; margin-top:2px; filter:drop-shadow(0 2px 8px rgba(16,185,129,0.25));" />
                        <div>
                            <div style="font-size:1.05rem; font-weight:800; color:#065F46;">Prompt is Already Top-Tier & Optimized</div>
                            <div style="font-size:0.85rem; color:#047857; margin-top:4px; line-height:1.45;">
                                {status_msg}
                            </div>
                        </div>
                    </div>
                    <div style="background:#DCFCE7; color:#166534; border:1px solid #86EFAC; padding:4px 12px; border-radius:999px; font-size:0.8rem; font-weight:700;">
                        🏷️ Archetype: {arch_badge}
                    </div>
                </div>
            </div>
            """)
            
            st.html(f"""
            <div class="compare-card optimized" style="margin-top:10px;">
                <div class="compare-header" style="background:#F0FDF4;">
                    <div class="compare-title"><span style="color:#10B981;">✨</span> <span style="color:#065F46;">Production-Ready Prompt</span></div>
                    <span class="compare-pill-badge" style="background:#DCFCE7; color:#166534; border-color:#86EFAC;">🏷️ {arch_badge}</span>
                </div>
                <div class="compare-body">
                    <div class="compare-content-text" style="font-size:0.95rem; line-height:1.6; color:#0F172A;">{optimized_text}</div>
                </div>
            </div>
            """)
        else:
            st.html(f"""
            <div class="step-card" style="margin-top:14px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                        <div class="step-title">5. Optimized Prompt</div>
                        <div class="step-subtitle">Production-grade rewritten prompt resolving all detected weaknesses while preserving your exact intent.</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #EEF2FF, #E0E7FF); color:#3730A3; border: 1.5px solid #C7D2FE; padding: 6px 14px; border-radius: 999px; font-size: 0.82rem; font-weight: 800; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 1px 3px rgba(79, 70, 229, 0.08);">
                        <span>🏷️ Detected Archetype:</span> <span>{arch_badge}</span>
                    </div>
                </div>
            </div>
            """)
            
            # 1. Full-Width Horizontal Original Prompt Card
            st.html(f"""
            <div class="compare-card original" style="width:100%; margin-bottom: 0px;">
                <div class="compare-header">
                    <div class="compare-title"><span>📝</span> <span>Original Prompt</span></div>
                    <span class="compare-pill-badge">Draft Input</span>
                </div>
                <div class="compare-body">
                    <div class="compare-content-text" style="font-size:0.95rem; line-height:1.6;">{st.session_state.user_prompt}</div>
                </div>
            </div>
            """)
            
            # 2. Centered Downward Transition Indicator
            st.html("""
            <div style="display:flex; justify-content:center; align-items:center; margin: 14px 0;">
                <div style="display:inline-flex; align-items:center; gap:8px; background:linear-gradient(135deg, #EEF2FF, #E0E7FF); border: 1.5px solid #C7D2FE; padding: 6px 20px; border-radius: 999px; box-shadow: 0 2px 8px rgba(79, 70, 229, 0.10);">
                    <span style="font-size:1rem; line-height:1;">✨</span>
                    <span style="font-size:0.84rem; font-weight:700; color:#3730A3; letter-spacing:0.01em;">Improved for clearer, more accurate results</span>
                    <span style="font-size:0.95rem; line-height:1; margin-left:2px;">⬇️</span>
                </div>
            </div>
            """)
            
            # 3. Full-Width Horizontal Optimized Prompt Card
            enhancements_html = ""
            if enhancements:
                enh_items = "".join([
                    f'<div class="compare-enhancement-item" style="font-size:0.84rem; margin-bottom:6px;"><span class="compare-enhancement-bullet" style="color:#2563EB;">✦</span> <span style="color:#1E293B;">{e}</span></div>'
                    for e in enhancements
                ])
                enhancements_html = f"""
                <div class="compare-enhancements-box" style="margin-top:14px; padding-top:12px; border-top:1px dashed #BFDBFE;">
                    <div class="compare-enhancements-title" style="font-size:0.78rem; color:#1D4ED8; margin-bottom:8px;"><span>⚡</span> <span>Key Enhancements Applied</span></div>
                    {enh_items}
                </div>
                """

            st.html(f"""
            <div class="compare-card optimized" style="width:100%;">
                <div class="compare-header">
                    <div class="compare-title"><span style="color:#2563EB;">✨</span> <span style="color:#1E3A8A;">Optimized Prompt</span></div>
                    <span class="compare-pill-badge" style="background:#EEF2FF; color:#1D4ED8; border:1px solid #BFDBFE; font-weight:700;">🏷️ {arch_badge}</span>
                </div>
                <div class="compare-body">
                    <div class="compare-content-text" style="font-size:0.98rem; line-height:1.65; color:#0F172A; font-weight:500;">{optimized_text}</div>
                    {enhancements_html}
                </div>
            </div>
            """)
            
        st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
        
        act_col1, act_col2, act_col3 = st.columns([1, 1, 1])
        with act_col1:
            if st.button("📋 Copy Optimized Prompt", key="btn_copy_prompt", use_container_width=True):
                copy_to_system_clipboard(optimized_text)
                inject_client_clipboard_copy(optimized_text)
                st.toast("✅ Optimized Prompt copied to clipboard!", icon="📋")
        with act_col2:
            if st.button("💾 Save Prompt", key="btn_save_prompt", use_container_width=True):
                eval_res = st.session_state.evaluation_result or {}
                enhancements = opt_data.get("key_enhancements", [])
                o_score = int(eval_res.get("overall_score", 0))
                
                # Persist to MongoDB Atlas
                save_user_saved_prompt(
                    user_email=user_email,
                    original_prompt=st.session_state.user_prompt,
                    optimized_prompt=optimized_text,
                    overall_score=o_score,
                    key_enhancements=enhancements
                )
                
                # Update session state cache
                st.session_state.saved_prompts_list.append({
                    "original": st.session_state.user_prompt,
                    "optimized": optimized_text,
                    "score": o_score,
                    "enhancements": enhancements,
                    "time": "Just now"
                })
                st.toast("✅ Optimized prompt saved to your collection!", icon="💾")
                st.success("Prompt saved to your Saved Prompts library! Access it anytime from the sidebar.")
        with act_col3:
            if st.button("🔄 Test Another Prompt", key="btn_new_eval", use_container_width=True, type="primary"):
                st.session_state.step = 1
                reset_prompt_temporary_states(clear_user_prompt=True)
                st.session_state.active_prompt_tab = "text"
                st.rerun()
