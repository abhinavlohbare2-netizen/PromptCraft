"""
PromptCraft Voice Transcription Service
---------------------------------------
Transcribes voice recordings to text using:
1. Pure Python WAV decoding + Whisper (Zero ffmpeg dependency)
2. Gemini Flash Multimodal Audio API (Cloud fallback)
3. SpeechRecognition Google engine (Fallback)
"""

import io
import os
from typing import Dict, Any, Union, Optional
import numpy as np

_whisper_model = None


def get_whisper_model(model_name: str = "base"):
    """Lazy loader for Whisper model."""
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper  # type: ignore
            _whisper_model = whisper.load_model(model_name)
        except Exception:
            return None
    return _whisper_model


def load_audio_scipy(audio_bytes: bytes) -> Optional[np.ndarray]:
    """
    Decodes WAV audio bytes into a 16kHz mono float32 NumPy array
    purely with scipy/numpy, bypassing ffmpeg completely.
    """
    try:
        import scipy.io.wavfile as wavfile  # type: ignore
        from scipy import signal  # type: ignore
        sample_rate, data = wavfile.read(io.BytesIO(audio_bytes))
        
        # Convert to float32 normalized between -1.0 and 1.0
        if data.dtype == np.int16:
            audio_float = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            audio_float = data.astype(np.float32) / 2147483648.0
        elif data.dtype == np.uint8:
            audio_float = (data.astype(np.float32) - 128.0) / 128.0
        else:
            audio_float = data.astype(np.float32)

        # Convert stereo to mono
        if len(audio_float.shape) > 1:
            audio_float = audio_float.mean(axis=1)

        # Resample to 16,000 Hz if necessary
        if sample_rate != 16000 and len(audio_float) > 0:
            target_samples = int(len(audio_float) * 16000 / sample_rate)
            resampled = signal.resample(audio_float, target_samples)
            if isinstance(resampled, tuple):
                resampled = resampled[0]
            audio_float = np.asarray(resampled, dtype=np.float32)

        return np.asarray(audio_float, dtype=np.float32)
    except Exception:
        return None


def transcribe_with_gemini(audio_bytes: bytes) -> Optional[str]:
    """Fallback: Transcribes audio using Google Gemini Multimodal Audio API."""
    try:
        from config.settings import GEMINI_API_KEYS, GEMINI_MODEL
        import google.generativeai as genai  # type: ignore
        
        if not GEMINI_API_KEYS:
            return None

        prompt = (
            "Transcribe the spoken words in this audio recording accurately into text. "
            "Return ONLY the verbatim transcribed text, without any additional explanations."
        )

        candidate_models = [
            "gemini-3.6-flash",
            "gemini-3.7-flash",
            "gemini-flash-latest",
            GEMINI_MODEL
        ]
        seen = set()
        candidate_models = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

        for key in GEMINI_API_KEYS:
            try:
                genai.configure(api_key=key)  # type: ignore
                for model_name in candidate_models:
                    try:
                        model = genai.GenerativeModel(model_name)  # type: ignore
                        response = model.generate_content([
                            prompt,
                            {"mime_type": "audio/wav", "data": audio_bytes}
                        ])
                        if response and response.text:
                            text = response.text.strip()
                            if text:
                                return text
                    except Exception:
                        continue
            except Exception:
                continue
    except Exception:
        pass
    return None


def transcribe_audio(audio_source: Union[bytes, io.BytesIO, str, Any]) -> Dict[str, Any]:
    """
    Master function to transcribe audio bytes/stream to text.
    """
    try:
        if isinstance(audio_source, (bytes, bytearray)):
            audio_bytes = bytes(audio_source)
        elif isinstance(audio_source, str):
            if os.path.exists(audio_source):
                with open(audio_source, "rb") as f:
                    audio_bytes = f.read()
            else:
                return {"status": "error", "text": "", "error": "Invalid audio file path."}
        elif hasattr(audio_source, "read"):
            if hasattr(audio_source, "seek"):
                audio_source.seek(0)
            audio_bytes = audio_source.read()
        elif hasattr(audio_source, "getvalue"):
            audio_bytes = audio_source.getvalue()
        else:
            return {"status": "error", "text": "", "error": "Invalid audio data received."}

        if not audio_bytes or len(audio_bytes) < 100:
            return {"status": "error", "text": "", "error": "Audio recording is empty or too short."}

        # 1. Primary Strategy: Pure-Python WAV decoding + Whisper
        audio_np = load_audio_scipy(audio_bytes)
        if audio_np is not None:
            model = get_whisper_model("base")
            if model is not None:
                try:
                    from backend.ocr_service import format_as_flowing_text
                    result = model.transcribe(audio_np, fp16=False, temperature=0.0)
                    raw_text = result.get("text", "") if isinstance(result, dict) else ""
                    text = str(raw_text).strip()
                    if text:
                        return {
                            "status": "success",
                            "text": format_as_flowing_text(text),
                            "engine": "OpenAI Whisper",
                            "error": None
                        }
                except Exception:
                    pass

        # 2. Secondary Strategy: Gemini Audio API
        gemini_text = transcribe_with_gemini(audio_bytes)
        if gemini_text:
            from backend.ocr_service import format_as_flowing_text
            return {
                "status": "success",
                "text": format_as_flowing_text(gemini_text),
                "engine": "Gemini Multimodal Audio AI",
                "error": None
            }

        # 3. Tertiary Strategy: SpeechRecognition
        try:
            import speech_recognition as sr  # type: ignore
            r = sr.Recognizer()
            with io.BytesIO(audio_bytes) as audio_file:
                with sr.AudioFile(audio_file) as source:
                    audio_data = r.record(source)
                    text = r.recognize_google(audio_data)
                    if text:
                        return {
                            "status": "success",
                            "text": text.strip(),
                            "engine": "Google Speech API",
                            "error": None
                        }
        except Exception:
            pass

        return {
            "status": "error",
            "text": "",
            "error": "Could not recognize speech in the audio. Please speak clearly into your mic and try again."
        }

    except Exception as e:
        return {
            "status": "error",
            "text": "",
            "error": f"Audio processing error: {str(e)}"
        }
