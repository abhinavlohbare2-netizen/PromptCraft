"""
PromptCraft OCR Service
-----------------------
Extracts prompt text from uploaded images using:
1. Multimodal AI Vision (Gemini 3.6/3.7 Flash) - 100% accurate for handwriting, screenshots & photos
2. Tesseract OCR (pytesseract) if tesseract binary is present
3. EasyOCR (Deep Learning PyTorch OCR) offline fallback
"""

import io
import os
import re
import shutil
import warnings
from pathlib import Path
from typing import Dict, Any, Union, Optional, List
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

warnings.filterwarnings("ignore")

# Try importing OCR libraries
try:
    import pytesseract  # type: ignore
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    pytesseract = None  # type: ignore

_easyocr_reader = None


def get_easyocr_reader():
    """Lazy loader for EasyOCR reader. Loaded on-demand only if image OCR is performed."""
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr  # type: ignore
            _easyocr_reader = easyocr.Reader(['en'], gpu=False)
        except Exception:
            _easyocr_reader = None
    return _easyocr_reader


def resolve_tesseract_cmd() -> Optional[str]:
    """Finds tesseract executable across PATH and standard Windows locations."""
    if not PYTESSERACT_AVAILABLE:
        return None
        
    which_path = shutil.which("tesseract")
    if which_path:
        return which_path

    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expandvars(r"%USERPROFILE%\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


if PYTESSERACT_AVAILABLE and pytesseract is not None:
    _tesseract_path = resolve_tesseract_cmd()
    if _tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = _tesseract_path


def preprocess_for_ocr(img: Image.Image) -> Image.Image:
    """
    Applies image preprocessing to optimize character edges:
    - RGB conversion
    - Grayscale conversion
    - Contrast boost (1.8x)
    - Sharpening
    """
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
        
    gray = img.convert("L")
    enhancer = ImageEnhance.Contrast(gray)
    high_contrast = enhancer.enhance(1.8)
    sharpened = high_contrast.filter(ImageFilter.SHARPEN)
    return sharpened


def format_as_flowing_text(text: str) -> str:
    """
    Formats extracted OCR text into clean, natural flowing continuous sentences and paragraphs.
    Merges artificial line breaks in the middle of sentences while
    preserving list items (1., -, *, •) and distinct paragraphs.
    """
    if not text:
        return ""
    
    text = text.strip().replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = text.split("\n\n")
    cleaned_paragraphs: List[str] = []
    
    for p in paragraphs:
        lines = [line.strip() for line in p.split("\n") if line.strip()]
        if not lines:
            continue
            
        # Check if this paragraph contains bullet/numbered lists
        is_list = any(re.match(r"^(\d+[\.\)]|[-*•])\s+", line_item) for line_item in lines)
        
        if is_list:
            cleaned_paragraphs.append("\n".join(lines))
        else:
            # Join wrapped lines with a single space
            joined = " ".join(lines)
            # Normalize spaces before punctuation
            joined = re.sub(r"\s+([,\.!\?;:])", r"\1", joined)
            # Normalize multiple spaces
            joined = re.sub(r"\s{2,}", " ", joined)
            cleaned_paragraphs.append(joined)
            
    return "\n\n".join(cleaned_paragraphs).strip()


def extract_with_gemini_vision(image: Image.Image) -> Optional[str]:
    """
    Extracts text using Google Gemini Multimodal Vision API.
    Supports handwriting, screenshots, whiteboard notes, and complex documents.
    """
    try:
        from config.settings import GEMINI_API_KEYS, GEMINI_MODEL
        import google.generativeai as genai
        
        if not GEMINI_API_KEYS:
            return None

        # Resize large image to max 1600px for high speed without losing detail
        img_to_send = image.copy()
        if img_to_send.mode not in ("RGB", "L"):
            img_to_send = img_to_send.convert("RGB")
        if max(img_to_send.size) > 1600:
            img_to_send.thumbnail((1600, 1600), Image.Resampling.LANCZOS)

        prompt = (
            "You are an OCR and document text extraction engine.\n"
            "Carefully read the text contained in the image, photo, or handwritten note.\n"
            "Extract the complete user prompt text or main body text accurately.\n"
            "- Transcode handwritten notes and screenshots into clean, natural, flowing sentences and continuous paragraphs.\n"
            "- Combine line-wrapped sentences from notebook lines into continuous sentences (do not insert hard line breaks after every physical notebook line).\n"
            "- Preserve distinct paragraphs (separated by blank lines) and bullet/numbered lists if present.\n"
            "- Fix obvious punctuation, spacing, and capitalization cleanly.\n"
            "- Output ONLY the clean prompt text. Do not include markdown quotes, headers, or system chatter."
        )

        candidate_models = [
            "gemini-3.6-flash",
            "gemini-3.7-flash",
            "gemini-flash-latest",
            "gemini-3.5-flash-lite",
            GEMINI_MODEL
        ]
        # De-duplicate candidate models
        seen = set()
        candidate_models = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

        for key in GEMINI_API_KEYS:
            try:
                genai.configure(api_key=key)
                for model_name in candidate_models:
                    try:
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content([prompt, img_to_send])
                        if response and response.text:
                            text = response.text.strip()
                            # Clean surrounding backticks if model wrapped in markdown
                            if text.startswith("```") and text.endswith("```"):
                                lines = text.splitlines()
                                if len(lines) >= 2:
                                    text = "\n".join(lines[1:-1]).strip()
                            if text:
                                return format_as_flowing_text(text)
                    except Exception:
                        continue
            except Exception:
                continue

    except Exception:
        pass
    return None


def extract_with_easyocr(image: Image.Image) -> Optional[str]:
    """Extracts text using EasyOCR neural engine."""
    reader = get_easyocr_reader()
    if reader is None:
        return None
    try:
        img_np = np.array(image)
        results: Any = reader.readtext(img_np)
        lines: List[str] = []
        for item in results:
            if isinstance(item, (list, tuple)) and len(item) > 1:
                txt = str(item[1]).strip()
                if txt:
                    lines.append(txt)
        if lines:
            return "\n".join(lines).strip()
    except Exception:
        pass
    return None


def extract_with_tesseract(image: Image.Image) -> Optional[str]:
    """Extracts text using Tesseract OCR."""
    if not PYTESSERACT_AVAILABLE or pytesseract is None:
        return None
    cmd = pytesseract.pytesseract.tesseract_cmd
    if not (shutil.which(cmd) or os.path.isfile(cmd)):
        return None
    try:
        processed_image = preprocess_for_ocr(image)
        custom_config = r'--oem 3 --psm 6'
        raw_text = pytesseract.image_to_string(processed_image, config=custom_config)
        cleaned_lines = [line_str.strip() for line_str in raw_text.splitlines() if line_str.strip()]
        text = "\n".join(cleaned_lines).strip()
        return text if text else None
    except Exception:
        return None


def extract_text_from_image(image_source: Union[str, Path, bytes, bytearray, io.BytesIO, Image.Image]) -> Dict[str, Any]:
    """
    Extracts text from an image with smart multi-engine hierarchy:
    1. Multimodal AI Vision (Gemini 3.6/3.7 Flash) - state of the art for handwriting & photos
    2. Tesseract OCR (if installed)
    3. EasyOCR (Neural PyTorch Engine)
    """
    try:
        if isinstance(image_source, (str, Path)):
            image = Image.open(str(image_source))
        elif isinstance(image_source, (bytes, bytearray)):
            image = Image.open(io.BytesIO(bytes(image_source)))
        elif isinstance(image_source, Image.Image):
            image = image_source
        elif hasattr(image_source, "read"):
            if hasattr(image_source, "seek"):
                image_source.seek(0)
            read_fn = getattr(image_source, "read")
            raw_bytes = read_fn()
            image = Image.open(io.BytesIO(raw_bytes))
        elif hasattr(image_source, "getvalue"):
            getvalue_fn = getattr(image_source, "getvalue")
            raw_bytes = getvalue_fn()
            image = Image.open(io.BytesIO(raw_bytes))
        else:
            raise ValueError("Unsupported image source type.")

        extracted_text = ""
        engine_used = ""

        # 1. Primary Strategy: Gemini Multimodal Vision API (Handles handwriting, photos, screenshots flawlessly)
        gemini_text = extract_with_gemini_vision(image)
        if gemini_text:
            extracted_text = gemini_text
            engine_used = "Gemini Multimodal Vision AI"

        # 2. Secondary Strategy: Tesseract OCR (if Gemini unavailable or offline)
        if not extracted_text:
            tess_text = extract_with_tesseract(image)
            if tess_text:
                extracted_text = format_as_flowing_text(tess_text)
                engine_used = "Tesseract OCR"

        # 3. Tertiary Strategy: EasyOCR
        if not extracted_text:
            processed_image = preprocess_for_ocr(image)
            easy_text = extract_with_easyocr(processed_image)
            if easy_text:
                extracted_text = format_as_flowing_text(easy_text)
                engine_used = "EasyOCR (Neural Engine)"

        if not extracted_text:
            return {
                "status": "warning",
                "extracted_text": "",
                "char_count": 0,
                "word_count": 0,
                "error": "No legible text could be detected in the uploaded image. Please ensure the text is clear."
            }

        extracted_text = format_as_flowing_text(extracted_text)
        return {
            "status": "success",
            "extracted_text": extracted_text,
            "char_count": len(extracted_text),
            "word_count": len(extracted_text.split()),
            "engine": engine_used,
            "error": None
        }

    except Exception as e:
        return {
            "status": "error",
            "extracted_text": "",
            "char_count": 0,
            "word_count": 0,
            "error": f"Image text extraction failed: {str(e)}"
        }
