"""
PromptCraft Document Processor Module
-------------------------------------
Extracts clean, structured text from external reference documents:
- PDF (.pdf) via PyMuPDF (fitz)
- Word Documents (.docx) via python-docx
- Plain Text (.txt) with multi-encoding fallback

Supports both filesystem file paths and in-memory byte streams (Streamlit uploads).
"""

import io
import re
from pathlib import Path
from typing import Dict, Any, Union, Optional, List
try:
    import pymupdf as fitz  # type: ignore (PyMuPDF modern import)
except ImportError:
    import fitz  # type: ignore (PyMuPDF fallback)
import docx  # type: ignore (python-docx)

from utils.validators import validate_document_file


def clean_document_text(raw_text: str) -> str:
    """
    Cleans extracted document text by removing excessive blank lines,
    page break artifacts, and carriage return characters.
    """
    if not raw_text:
        return ""
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace multiple horizontal spaces with a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Replace 3 or more consecutive newlines with 2 newlines
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_text_from_pdf(file_source: Union[str, Path, bytes, io.BytesIO]) -> Dict[str, Any]:
    """
    Extracts text from a PDF file path or byte stream using PyMuPDF (fitz).
    
    Returns:
        Dictionary containing extracted text, page count, and status.
    """
    try:
        if isinstance(file_source, (str, Path)):
            doc = fitz.open(str(file_source))
        elif isinstance(file_source, bytes):
            doc = fitz.open(stream=file_source, filetype="pdf")
        elif hasattr(file_source, "read"):
            # Streamlit UploadedFile or BytesIO
            byte_content = file_source.read() if hasattr(file_source, "read") else file_source.getvalue()
            doc = fitz.open(stream=byte_content, filetype="pdf")
        else:
            raise ValueError(f"Unsupported file source type: {type(file_source)}")
            
        page_count = len(doc)
        pages_text: List[str] = []
        
        for page_num in range(page_count):
            page = doc.load_page(page_num)
            text_val = page.get_text("text")
            if isinstance(text_val, str) and text_val.strip():
                pages_text.append(text_val.strip())
                
        doc.close()
        full_text = "\n\n".join(pages_text)
        cleaned = clean_document_text(full_text)
        
        return {
            "status": "success",
            "page_count": page_count,
            "text": cleaned,
            "error": None
        }
    except Exception as e:
        return {
            "status": "error",
            "page_count": 0,
            "text": "",
            "error": f"Failed to parse PDF: {str(e)}"
        }


def extract_text_from_docx(file_source: Union[str, Path, bytes, io.BytesIO]) -> Dict[str, Any]:
    """
    Extracts text from a DOCX file path or byte stream using python-docx.
    
    Returns:
        Dictionary containing extracted text, paragraph count, and status.
    """
    try:
        if isinstance(file_source, (str, Path)):
            doc = docx.Document(str(file_source))
        elif isinstance(file_source, bytes):
            doc = docx.Document(io.BytesIO(file_source))
        elif hasattr(file_source, "read"):
            byte_content = file_source.read()
            doc = docx.Document(io.BytesIO(byte_content))
        else:
            raise ValueError(f"Unsupported file source type: {type(file_source)}")
            
        paragraphs: List[str] = []
        for p in doc.paragraphs:
            if p.text.strip():
                paragraphs.append(p.text.strip())
                
        # Also extract table text if present
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    paragraphs.append(" | ".join(row_text))
                    
        full_text = "\n\n".join(paragraphs)
        cleaned = clean_document_text(full_text)
        
        return {
            "status": "success",
            "paragraph_count": len(paragraphs),
            "text": cleaned,
            "error": None
        }
    except Exception as e:
        return {
            "status": "error",
            "paragraph_count": 0,
            "text": "",
            "error": f"Failed to parse DOCX: {str(e)}"
        }


def extract_text_from_txt(file_source: Union[str, Path, bytes, io.BytesIO]) -> Dict[str, Any]:
    """
    Extracts text from a TXT file with fallback encodings (UTF-8, Latin-1, CP1252).
    """
    try:
        raw_bytes: bytes = b""
        if isinstance(file_source, (str, Path)):
            with open(file_source, "rb") as f:
                raw_bytes = f.read()
        elif isinstance(file_source, bytes):
            raw_bytes = file_source
        elif hasattr(file_source, "read"):
            raw_bytes = file_source.read()
        else:
            raise ValueError(f"Unsupported file source type: {type(file_source)}")
            
        # Try encodings sequentially
        text = ""
        for encoding in ["utf-8", "utf-16", "latin-1", "cp1252"]:
            try:
                text = raw_bytes.decode(encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue
                
        cleaned = clean_document_text(text)
        return {
            "status": "success",
            "text": cleaned,
            "error": None
        }
    except Exception as e:
        return {
            "status": "error",
            "text": "",
            "error": f"Failed to parse TXT: {str(e)}"
        }


def process_document(
    file_source: Union[str, Path, bytes, io.BytesIO],
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Master function to process an uploaded document or file path.
    Automatically detects file extension and applies the appropriate parser.
    
    Args:
        file_source: File path, raw bytes, or Streamlit UploadedFile buffer.
        filename: Optional filename (required if passing raw bytes or stream).
        
    Returns:
        Structured document extraction result dictionary.
    """
    # Determine filename
    actual_filename = ""
    if filename:
        actual_filename = filename
    elif isinstance(file_source, (str, Path)):
        actual_filename = Path(file_source).name
    elif hasattr(file_source, "name"):
        actual_filename = getattr(file_source, "name", "uploaded_document")
    else:
        actual_filename = "document.txt"
        
    # Validate extension
    is_valid, err_msg = validate_document_file(actual_filename)
    if not is_valid:
        return {
            "status": "error",
            "filename": actual_filename,
            "file_type": "unknown",
            "extracted_text": "",
            "word_count": 0,
            "char_count": 0,
            "error": err_msg
        }
        
    ext = "." + actual_filename.rsplit(".", 1)[-1].lower()
    
    if ext == ".pdf":
        result = extract_text_from_pdf(file_source)
        file_type = "pdf"
    elif ext == ".docx":
        result = extract_text_from_docx(file_source)
        file_type = "docx"
    elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
        from backend.ocr_service import extract_text_from_image
        ocr_res = extract_text_from_image(file_source)
        result = {
            "status": ocr_res["status"],
            "text": ocr_res.get("extracted_text", ""),
            "page_count": 1,
            "error": ocr_res.get("error")
        }
        file_type = "image"
    else:
        result = extract_text_from_txt(file_source)
        file_type = "txt"
        
    text = result.get("text", "")
    words = len(text.split()) if text else 0
    chars = len(text)
    
    return {
        "status": result["status"],
        "filename": actual_filename,
        "file_type": file_type,
        "extracted_text": text,
        "text": text,
        "word_count": words,
        "char_count": chars,
        "page_count": result.get("page_count", 1),
        "error": result.get("error")
    }
