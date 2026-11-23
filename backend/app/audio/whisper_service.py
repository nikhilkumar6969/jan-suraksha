"""
Offline AI Speech-to-Text Service using OpenAI Whisper Medium (faster-whisper)
100% Local Inference with Zero Cloud/API Dependencies.
Optimized for Hindi, English, Hinglish, and Multilingual Indian Audio.
"""

import os
import sys
import tempfile
import logging
import threading
import ctypes
from pathlib import Path
from typing import Optional, Union, BinaryIO, Tuple, Dict, Any

# Ensure PyAV compatibility across all versions (strip metadata_errors kwargs in av 19+)
try:
    import av
    _orig_av_open = av.open
    def _safe_av_open(*args, **kwargs):
        kwargs.pop("metadata_errors", None)
        return _orig_av_open(*args, **kwargs)
    av.open = _safe_av_open
except Exception:
    pass

logger = logging.getLogger("suraksha.whisper")

# Model Configuration
MODEL_NAME = os.getenv("WHISPER_MODEL_NAME", "medium")
DEFAULT_MODEL_REL_PATH = os.getenv("WHISPER_MODEL_PATH", "./models/whisper-medium")

SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".webm", ".ogg", ".aac"}

_WHISPER_MODEL_INSTANCE = None
_MODEL_LOCK = threading.Lock()

def resolve_model_path() -> Path:
    """
    Resolves the local storage path for Whisper Medium.
    Checks explicit environment path, current working dir, project root, and backend root.
    """
    configured = Path(DEFAULT_MODEL_REL_PATH)
    if configured.is_absolute():
        return configured

    # Try relative to cwd
    p_cwd = Path.cwd() / configured
    if p_cwd.exists() and is_model_available(p_cwd):
        return p_cwd

    # Try relative to project root (hackasol/models/whisper-medium)
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    p_proj = project_root / "models" / "whisper-medium"
    if p_proj.exists() and is_model_available(p_proj):
        return p_proj

    # Try backend root (hackasol/backend/models/whisper-medium)
    backend_root = Path(__file__).resolve().parent.parent.parent
    p_backend = backend_root / "models" / "whisper-medium"
    if p_backend.exists() and is_model_available(p_backend):
        return p_backend

    # Default to project_root / models / whisper-medium
    return p_proj

def is_model_available(model_dir: Path) -> bool:
    """
    Checks whether the Whisper Medium model files are present locally.
    CTranslate2 models contain model.bin, vocabulary.json/txt, and config.json.
    """
    if not model_dir.exists() or not model_dir.is_dir():
        return False

    has_weights = (model_dir / "model.bin").exists() or any(model_dir.glob("*.safetensors"))
    has_config = (model_dir / "config.json").exists()
    has_vocab = (model_dir / "vocabulary.json").exists() or (model_dir / "vocabulary.txt").exists() or (model_dir / "tokenizer.json").exists()

    return has_weights and (has_config or has_vocab)

def is_cuda_usable() -> bool:
    """
    Verifies that CUDA is available AND runtime cublas libraries are present on system PATH.
    """
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() <= 0:
            return False
        # Check if cublas runtime library can actually be loaded on Windows
        if sys.platform == "win32":
            try:
                ctypes.CDLL("cublas64_12.dll")
                return True
            except OSError:
                return False
        return True
    except Exception:
        return False

def get_optimal_device_and_compute() -> Tuple[str, str]:
    """
    Selects CUDA FP16 if an NVIDIA GPU with usable runtime DLLs is available,
    else CPU INT8 for fast, robust local inference.
    """
    if is_cuda_usable():
        logger.info("NVIDIA GPU with CUDA runtime detected. Using CUDA FP16.")
        return "cuda", "float16"

    logger.info("Using CPU INT8 mode for local Whisper Medium inference.")
    return "cpu", "int8"

def get_whisper_model(auto_download: bool = False):
    """
    Thread-safe singleton model loader for Whisper Medium.
    Loads once into memory and reuses for subsequent requests.
    """
    global _WHISPER_MODEL_INSTANCE
    if _WHISPER_MODEL_INSTANCE is not None:
        return _WHISPER_MODEL_INSTANCE

    with _MODEL_LOCK:
        if _WHISPER_MODEL_INSTANCE is not None:
            return _WHISPER_MODEL_INSTANCE

        from faster_whisper import WhisperModel, download_model

        model_dir = resolve_model_path()

        if not is_model_available(model_dir):
            if auto_download:
                logger.info(f"Whisper Medium model not found locally. Initiating one-time download into {model_dir}...")
                model_dir.mkdir(parents=True, exist_ok=True)
                download_model(MODEL_NAME, output_dir=str(model_dir))
            else:
                raise FileNotFoundError(
                    f"Whisper Medium model was not found at '{model_dir}'. "
                    f"Please download it locally by running: python backend/scripts/download_whisper_medium.py"
                )

        device, compute_type = get_optimal_device_and_compute()
        logger.info(f"Loading Whisper Medium from '{model_dir}' on {device} ({compute_type})...")

        try:
            model = WhisperModel(
                str(model_dir),
                device=device,
                compute_type=compute_type,
                local_files_only=True
            )
        except Exception as err:
            if device == "cuda":
                logger.warning(f"CUDA initialization failed ({err}). Falling back to CPU int8...")
                model = WhisperModel(
                    str(model_dir),
                    device="cpu",
                    compute_type="int8",
                    local_files_only=True
                )
            else:
                raise err

        _WHISPER_MODEL_INSTANCE = model
        logger.info("Whisper Medium model loaded successfully and ready for inference.")
        return _WHISPER_MODEL_INSTANCE

def transcribe_audio(
    audio_input: Union[bytes, BinaryIO, str, Path],
    filename: Optional[str] = None,
    language: Optional[str] = None,
    beam_size: int = 5,
    temperature: float = 0.0,
    vad_filter: bool = True
) -> Dict[str, Any]:
    """
    Transcribes audio offline using Whisper Medium.

    Parameters:
    - audio_input: Raw audio bytes, file path, or binary stream
    - filename: Original filename for extension hint (.mp3, .wav, .webm, etc.)
    - language: "hi", "en", or None/"auto" for automatic detection
    - beam_size: Beam search width (default 5 for highest accuracy)
    - temperature: Sampling temperature (default 0.0 for deterministic output)
    - vad_filter: Voice activity filter to strip non-speech background audio

    Returns:
    {
        "success": bool,
        "text": str,
        "language": str,
        "language_probability": float,
        "duration": float,
        "error": Optional[str]
    }
    """
    # 1. Validate Audio Presence
    if audio_input is None:
        return {
            "success": False,
            "error": "No audio file provided.",
            "text": "",
            "language": "",
            "language_probability": 0.0,
            "duration": 0.0
        }

    # Extract bytes if needed
    if isinstance(audio_input, (str, Path)):
        p = Path(audio_input)
        if not p.exists() or p.stat().st_size == 0:
            return {
                "success": False,
                "error": "Audio file does not exist or is empty.",
                "text": "",
                "language": "",
                "language_probability": 0.0,
                "duration": 0.0
            }
        audio_bytes = p.read_bytes()
        suffix = p.suffix.lower() or ".wav"
    elif hasattr(audio_input, "read"):
        audio_bytes = audio_input.read()
        suffix = Path(filename or "audio.wav").suffix.lower() or ".wav"
    elif isinstance(audio_input, bytes):
        audio_bytes = audio_input
        suffix = Path(filename or "audio.wav").suffix.lower() or ".wav"
    else:
        return {
            "success": False,
            "error": "Unsupported audio input type.",
            "text": "",
            "language": "",
            "language_probability": 0.0,
            "duration": 0.0
        }

    if len(audio_bytes) == 0:
        return {
            "success": False,
            "error": "Audio payload is empty (0 bytes).",
            "text": "",
            "language": "",
            "language_probability": 0.0,
            "duration": 0.0
        }

    # Validate extension
    if suffix not in SUPPORTED_AUDIO_EXTENSIONS:
        suffix = ".wav"

    # Normalize language parameter
    target_lang = None
    if language:
        clean_lang = language.strip().lower()
        if clean_lang not in {"auto", "none", ""}:
            target_lang = clean_lang

    # 2. Load Model
    try:
        model = get_whisper_model(auto_download=False)
    except FileNotFoundError as fnf:
        return {
            "success": False,
            "error": str(fnf),
            "text": "",
            "language": "",
            "language_probability": 0.0,
            "duration": 0.0
        }
    except Exception as me:
        return {
            "success": False,
            "error": f"Failed to initialize Whisper Medium model: {str(me)}",
            "text": "",
            "language": "",
            "language_probability": 0.0,
            "duration": 0.0
        }

    # 3. Transcribe via Temp File for Clean Audio Stream Demuxing
    temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        temp_file.write(audio_bytes)
        temp_file.flush()
        temp_file.close()

        segments, info = model.transcribe(
            temp_file.name,
            beam_size=beam_size,
            temperature=temperature,
            vad_filter=vad_filter,
            language=target_lang
        )

        text_pieces = []
        for segment in segments:
            clean_seg = segment.text.strip()
            if clean_seg:
                text_pieces.append(clean_seg)

        transcription_text = " ".join(text_pieces)

        return {
            "success": True,
            "text": transcription_text,
            "language": info.language if info else (target_lang or "unknown"),
            "language_probability": round(float(info.language_probability), 4) if info else 1.0,
            "duration": round(float(info.duration), 2) if info else 0.0
        }
    except Exception as te:
        logger.error(f"Whisper transcription failed: {te}", exc_info=True)
        return {
            "success": False,
            "error": f"Transcription error: {str(te)}",
            "text": "",
            "language": "",
            "language_probability": 0.0,
            "duration": 0.0
        }
    finally:
        try:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
        except OSError:
            pass
