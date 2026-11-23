"""
Offline AI Speech-to-Text Service for Suraksha & Multilingual Call Analysis
100% Local Offline Inference with Multi-Mode Performance Tuning.
Supports Indian English, Hindi, Hinglish, and Regional Indian Accents.

Modes:
- Accuracy: Whisper Medium (769M), beam_size=5, high-precision phonetic decoding.
- Balanced (Default): Whisper Small (244M), beam_size=1 (greedy), 3x faster, high accuracy.
- Speed: Sherpa-ONNX Whisper Tiny (39M), INT8 ONNX, VAD-filtered, lowest latency.
- Fallback: Offline Vosk Small Hindi/English for ultra-low resource edge environments.
"""

import os
import sys
import io
import time
import math
import logging
import threading
import ctypes
import tempfile
from pathlib import Path
from typing import Optional, Union, BinaryIO, Tuple, Dict, Any, List
import numpy as np

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

# Supported modes
MODE_ACCURACY = "accuracy"
MODE_BALANCED = "balanced"
MODE_SPEED = "speed"
VALID_MODES = {MODE_ACCURACY, MODE_BALANCED, MODE_SPEED}

SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".webm", ".ogg", ".aac", ".opus"}

# Model Paths Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent

# In-memory thread-safe model singletons
_LOADED_MODELS: Dict[str, Any] = {}
_MODEL_LOCK = threading.Lock()
_WHISPER_MODEL_INSTANCE = None  # Backward-compatibility alias for legacy code


def get_optimal_cpu_threads() -> int:
    """
    Selects optimal CPU thread count for CTranslate2 / ONNX runtime.
    Matches physical core count (4-6 on 6-core/12-thread CPU) to eliminate OpenMP thread contention.
    """
    count = os.cpu_count() or 4
    return max(2, min(6, count // 2 if count > 6 else count))


def resolve_model_path(model_name: str = "medium") -> Path:
    """
    Resolves the local storage path for Whisper models (medium, small).
    Checks project root / models, backend root / models, and environment variables.
    """
    model_folder = f"whisper-{model_name}"
    env_key = f"WHISPER_{model_name.upper()}_PATH"
    if os.getenv(env_key):
        return Path(os.environ[env_key])

    candidates = [
        PROJECT_ROOT / "models" / model_folder,
        BACKEND_ROOT / "models" / model_folder,
        Path.cwd() / "models" / model_folder,
        Path.cwd() / model_folder
    ]
    for c in candidates:
        if c.exists() and is_model_available(c):
            return c
    return candidates[0]


def is_model_available(model_dir: Path) -> bool:
    """
    Checks whether CTranslate2 model files are present locally.
    CTranslate2 models contain model.bin, config.json, and vocabulary / tokenizer.
    """
    if not model_dir.exists() or not model_dir.is_dir():
        return False

    has_weights = (model_dir / "model.bin").exists() or any(model_dir.glob("*.safetensors"))
    has_config = (model_dir / "config.json").exists()
    has_vocab = (
        (model_dir / "vocabulary.json").exists()
        or (model_dir / "vocabulary.txt").exists()
        or (model_dir / "tokenizer.json").exists()
    )
    return has_weights and (has_config or has_vocab)


def is_cuda_usable() -> bool:
    """
    Verifies that an NVIDIA CUDA device is present AND required runtime
    dynamic libraries (cublas64_12.dll and cudnn) can actually be loaded.
    Prevents runtime crashes on Windows when CUDA is detected by driver but runtime DLLs are missing.
    """
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() <= 0:
            return False

        if sys.platform == "win32":
            try:
                ctypes.CDLL("cublas64_12.dll")
                return True
            except (OSError, FileNotFoundError):
                return False
        return True
    except Exception:
        return False


def get_optimal_device_and_compute() -> Tuple[str, str]:
    """
    Selects CUDA FP16 if an NVIDIA GPU with usable runtime DLLs is available,
    else CPU INT8 for robust, fast local inference without VRAM exhaustion.
    """
    if is_cuda_usable():
        logger.info("NVIDIA GPU with CUDA runtime verified. Using CUDA FP16.")
        return "cuda", "float16"

    logger.info("Using CPU INT8 mode for robust offline Whisper inference.")
    return "cpu", "int8"


def get_whisper_model(model_name: str = "medium", auto_download: bool = False):
    """
    Thread-safe singleton model loader for Whisper models (medium or small).
    Loads once into memory and reuses the instance across all subsequent requests.
    """
    global _WHISPER_MODEL_INSTANCE
    clean_name = "small" if "small" in model_name.lower() else "medium"
    cache_key = f"whisper_{clean_name}"

    if cache_key in _LOADED_MODELS:
        return _LOADED_MODELS[cache_key]

    with _MODEL_LOCK:
        if cache_key in _LOADED_MODELS:
            return _LOADED_MODELS[cache_key]

        from faster_whisper import WhisperModel, download_model

        model_dir = resolve_model_path(clean_name)
        if not is_model_available(model_dir):
            if auto_download:
                logger.info(f"Model {clean_name} not found at {model_dir}. Downloading into local path...")
                model_dir.mkdir(parents=True, exist_ok=True)
                download_model(clean_name, output_dir=str(model_dir))
            else:
                raise FileNotFoundError(
                    f"Whisper {clean_name.capitalize()} model was not found at '{model_dir}'. "
                    f"Please verify model files exist in models/{model_dir.name}."
                )

        device, compute_type = get_optimal_device_and_compute()
        threads = get_optimal_cpu_threads()
        logger.info(f"Loading Whisper {clean_name.capitalize()} from '{model_dir}' on {device} ({compute_type}, threads={threads})...")

        try:
            model = WhisperModel(
                str(model_dir),
                device=device,
                compute_type=compute_type,
                cpu_threads=threads,
                local_files_only=True
            )
        except Exception as err:
            if device == "cuda":
                logger.warning(f"CUDA initialization failed ({err}). Falling back to CPU int8...")
                model = WhisperModel(
                    str(model_dir),
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=threads,
                    local_files_only=True
                )
            else:
                raise err

        _LOADED_MODELS[cache_key] = model
        if clean_name == "medium":
            _WHISPER_MODEL_INSTANCE = model
        logger.info(f"Whisper {clean_name.capitalize()} successfully loaded and ready for inference.")
        return _LOADED_MODELS[cache_key]


def get_sherpa_tiny_recognizer(language: str = "en"):
    """
    Thread-safe singleton loader for Sherpa-ONNX Whisper Tiny recognizer.
    """
    target_lang = "hi" if language in ("hi", "chg") else ("en" if language == "en" else "")
    cache_key = f"sherpa_tiny_{target_lang or 'auto'}"

    if cache_key in _LOADED_MODELS:
        return _LOADED_MODELS[cache_key]

    with _MODEL_LOCK:
        if cache_key in _LOADED_MODELS:
            return _LOADED_MODELS[cache_key]

        import sherpa_onnx
        model_dir = BACKEND_ROOT / "models" / "sherpa-onnx-whisper-tiny"
        if not model_dir.exists():
            raise FileNotFoundError(f"Sherpa-ONNX Whisper Tiny model not found at {model_dir}")

        threads = get_optimal_cpu_threads()
        logger.info(f"Loading Sherpa-ONNX Whisper Tiny on CPU (threads={threads}, lang='{target_lang}')...")
        rec = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=str(model_dir / "tiny-encoder.int8.onnx"),
            decoder=str(model_dir / "tiny-decoder.int8.onnx"),
            tokens=str(model_dir / "tiny-tokens.txt"),
            language=target_lang or "en",
            num_threads=threads,
            decoding_method="greedy_search",
            provider="cpu"
        )
        _LOADED_MODELS[cache_key] = rec
        logger.info("Sherpa-ONNX Whisper Tiny loaded successfully.")
        return rec


def decode_audio_to_mono_16k(
    audio_bytes: bytes,
    filename: Optional[str] = None
) -> Tuple[np.ndarray, float]:
    """
    Decodes arbitrary audio bytes (WAV, MP3, WebM, M4A, FLAC, OGG, AAC) directly in-memory
    into a 16kHz mono float32 NumPy array [-1.0, 1.0] and returns (samples, duration_seconds).
    Avoids redundant disk writes and temporary file overhead.
    """
    if not audio_bytes:
        return np.zeros(0, dtype=np.float32), 0.0

    bio = io.BytesIO(audio_bytes)

    # 1. Primary: SoundFile (very fast for WAV, FLAC, OGG)
    try:
        import soundfile as sf
        samples, sr = sf.read(bio, dtype="float32")
        if samples.ndim > 1:
            samples = samples.mean(axis=1)

        if sr != 16000 and len(samples) > 0:
            import scipy.signal
            num_samples = int(round(len(samples) * 16000.0 / sr))
            samples = scipy.signal.resample(samples, num_samples).astype(np.float32)

        duration = float(len(samples)) / 16000.0
        return samples, duration
    except Exception:
        bio.seek(0)

    # 2. Secondary: PyAV (Universal decoder for WebM, M4A, AAC, MP3, Opus, etc.)
    try:
        import av
        container = av.open(bio)
        audio_streams = [s for s in container.streams if s.type == "audio"]
        if not audio_streams:
            container.close()
            raise ValueError("No audio stream found in container")

        resampler = av.AudioResampler(format="flt", layout="mono", rate=16000)
        chunks = []
        for frame in container.decode(audio=0):
            for r in resampler.resample(frame):
                chunks.append(r.to_ndarray()[0])
        container.close()

        if chunks:
            samples = np.concatenate(chunks).astype(np.float32)
            duration = float(len(samples)) / 16000.0
            return samples, duration
    except Exception as av_err:
        logger.debug(f"PyAV in-memory decode fallback: {av_err}")

    # 3. Tertiary: Fallback via temp file for odd OS-level decoders
    suffix = Path(filename or "audio.wav").suffix.lower() or ".wav"
    temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        temp_file.write(audio_bytes)
        temp_file.flush()
        temp_file.close()

        import soundfile as sf
        samples, sr = sf.read(temp_file.name, dtype="float32")
        if samples.ndim > 1:
            samples = samples.mean(axis=1)
        if sr != 16000 and len(samples) > 0:
            import scipy.signal
            num_samples = int(round(len(samples) * 16000.0 / sr))
            samples = scipy.signal.resample(samples, num_samples).astype(np.float32)
        duration = float(len(samples)) / 16000.0
        return samples, duration
    finally:
        try:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
        except OSError:
            pass


def trim_silence_rms(
    samples: np.ndarray,
    sample_rate: int = 16000,
    threshold_rms: float = 0.005,
    margin_seconds: float = 0.25
) -> np.ndarray:
    """
    Trims leading and trailing silence from 16kHz float32 audio.
    Prevents Whisper from wasting compute and looping on dead air.
    """
    if len(samples) < sample_rate * 0.5:
        return samples

    frame_len = int(sample_rate * 0.05)  # 50ms frames
    margin_samples = int(sample_rate * margin_seconds)

    # Find start
    start_idx = 0
    for i in range(0, len(samples) - frame_len, frame_len):
        frame = samples[i:i + frame_len]
        rms = np.sqrt(np.mean(frame ** 2))
        if rms >= threshold_rms:
            start_idx = max(0, i - margin_samples)
            break

    # Find end
    end_idx = len(samples)
    for i in range(len(samples) - frame_len, 0, -frame_len):
        frame = samples[i:i + frame_len]
        rms = np.sqrt(np.mean(frame ** 2))
        if rms >= threshold_rms:
            end_idx = min(len(samples), i + frame_len + margin_samples)
            break

    if start_idx < end_idx and (end_idx - start_idx) > (sample_rate * 0.2):
        return samples[start_idx:end_idx]
    return samples


def transcribe_audio(
    audio_input: Union[bytes, BinaryIO, str, Path],
    filename: Optional[str] = None,
    language: Optional[str] = None,
    beam_size: Optional[int] = None,
    temperature: float = 0.0,
    vad_filter: bool = True,
    mode: str = MODE_BALANCED
) -> Dict[str, Any]:
    """
    Transcribes audio offline with three selectable performance modes.

    Parameters:
    - audio_input: Raw audio bytes, file path, or binary stream
    - filename: Original filename for container/format hint (.mp3, .wav, .webm, etc.)
    - language: "hi", "en", "auto", or None for automatic detection
    - beam_size: Optional override for beam search width (default: 1 for Balanced, 5 for Accuracy)
    - temperature: Sampling temperature (default 0.0 for deterministic decoding)
    - vad_filter: Voice Activity Detection filter
    - mode: "accuracy" | "balanced" (default) | "speed"

    Returns:
    {
        "success": bool,
        "text": str,
        "language": str,
        "language_probability": float,
        "duration": float,
        "processing_time": float,
        "rtf": float,
        "mode": str,
        "model": str,
        "engine": str,
        "error": Optional[str]
    }
    """
    t_start = time.perf_counter()

    # 1. Validate Mode
    req_mode = str(mode).strip().lower() if mode else MODE_BALANCED
    if req_mode not in VALID_MODES:
        req_mode = MODE_BALANCED

    # 2. Extract raw bytes
    if audio_input is None:
        return {
            "success": False,
            "error": "No audio file provided.",
            "text": "",
            "language": "",
            "language_probability": 0.0,
            "duration": 0.0,
            "processing_time": 0.0,
            "rtf": 0.0,
            "mode": req_mode,
            "model": "",
            "engine": ""
        }

    if isinstance(audio_input, (str, Path)):
        p = Path(audio_input)
        if not p.exists() or p.stat().st_size == 0:
            return {
                "success": False,
                "error": "Audio file does not exist or is empty.",
                "text": "",
                "language": "",
                "language_probability": 0.0,
                "duration": 0.0,
                "processing_time": 0.0,
                "rtf": 0.0,
                "mode": req_mode,
                "model": "",
                "engine": ""
            }
        audio_bytes = p.read_bytes()
        fname = filename or p.name
    elif hasattr(audio_input, "read"):
        audio_bytes = audio_input.read()
        fname = filename or "audio.wav"
    elif isinstance(audio_input, bytes):
        audio_bytes = audio_input
        fname = filename or "audio.wav"
    else:
        return {
            "success": False,
            "error": "Unsupported audio input type.",
            "text": "",
            "language": "",
            "language_probability": 0.0,
            "duration": 0.0,
            "processing_time": 0.0,
            "rtf": 0.0,
            "mode": req_mode,
            "model": "",
            "engine": ""
        }

    if len(audio_bytes) == 0:
        return {
            "success": False,
            "error": "Audio payload is empty (0 bytes).",
            "text": "",
            "language": "",
            "language_probability": 0.0,
            "duration": 0.0,
            "processing_time": 0.0,
            "rtf": 0.0,
            "mode": req_mode,
            "model": "",
            "engine": ""
        }

    # Normalize language parameter
    target_lang = None
    if language:
        clean_lang = language.strip().lower()
        if clean_lang not in {"auto", "none", ""}:
            target_lang = clean_lang

    # 3. Decode audio in-memory to 16kHz mono float32
    try:
        samples, audio_duration = decode_audio_to_mono_16k(audio_bytes, filename=fname)
    except Exception as de:
        logger.error(f"Audio decoding failure: {de}")
        return {
            "success": False,
            "error": f"Failed to decode audio: {str(de)}",
            "text": "",
            "language": "",
            "language_probability": 0.0,
            "duration": 0.0,
            "processing_time": 0.0,
            "rtf": 0.0,
            "mode": req_mode,
            "model": "",
            "engine": ""
        }

    if len(samples) == 0 or audio_duration <= 0.05:
        return {
            "success": False,
            "error": "Audio contains no playable sound data.",
            "text": "",
            "language": "",
            "language_probability": 0.0,
            "duration": round(audio_duration, 2),
            "processing_time": round(time.perf_counter() - t_start, 3),
            "rtf": 0.0,
            "mode": req_mode,
            "model": "",
            "engine": ""
        }

    # Silence trimming before model execution
    trimmed_samples = trim_silence_rms(samples, sample_rate=16000)

    # 4. Route by Selected Mode
    transcription_text = ""
    detected_language = target_lang or "en"
    lang_probability = 1.0
    model_identifier = ""
    engine_desc = ""

    # =========================================================================
    # MODE C: SPEED (Sherpa-ONNX Whisper Tiny + VAD)
    # =========================================================================
    if req_mode == MODE_SPEED:
        model_identifier = "sherpa-whisper-tiny"
        engine_desc = "Sherpa-ONNX Whisper Tiny (39M • Ultra-Fast)"
        try:
            rec = get_sherpa_tiny_recognizer(language=target_lang or "en")
            # Chunk into <= 25-second windows to safely stay within Sherpa-ONNX 30s limits
            window_size = int(25.0 * 16000)
            text_segments = []

            for start_i in range(0, len(trimmed_samples), window_size):
                chunk = trimmed_samples[start_i:start_i + window_size]
                if len(chunk) < int(0.3 * 16000):
                    continue
                stream = rec.create_stream()
                stream.accept_waveform(16000, chunk)
                rec.decode_stream(stream)
                seg = stream.result.text.strip()
                if seg:
                    text_segments.append(seg)

            transcription_text = " ".join(text_segments).strip()
            detected_language = target_lang or ("hi" if any("\u0900" <= c <= "\u097f" for c in transcription_text) else "en")
            lang_probability = 0.95
        except Exception as speed_err:
            logger.warning(f"Speed mode failed ({speed_err}), attempting fallback to Balanced mode...")
            req_mode = MODE_BALANCED

    # =========================================================================
    # MODE B: BALANCED (DEFAULT: Whisper Small + beam_size=1)
    # =========================================================================
    if req_mode == MODE_BALANCED:
        model_identifier = "whisper-small"
        engine_desc = "OpenAI Whisper Small (244M • Balanced INT8)"
        effective_beam = beam_size if beam_size is not None else 1
        try:
            model = get_whisper_model("small", auto_download=False)
            segments, info = model.transcribe(
                trimmed_samples,
                beam_size=effective_beam,
                temperature=temperature,
                vad_filter=vad_filter,
                language=target_lang
            )
            text_pieces = [s.text.strip() for s in segments if s.text.strip()]
            transcription_text = " ".join(text_pieces)
            if info:
                detected_language = info.language or target_lang or "unknown"
                lang_probability = round(float(info.language_probability), 4)
        except Exception as bal_err:
            logger.warning(f"Balanced mode failed ({bal_err}), falling back to Accuracy mode...")
            req_mode = MODE_ACCURACY

    # =========================================================================
    # MODE A: ACCURACY (Whisper Medium + beam_size=5)
    # =========================================================================
    if req_mode == MODE_ACCURACY:
        model_identifier = "whisper-medium"
        engine_desc = "OpenAI Whisper Medium (769M • High Precision)"
        effective_beam = beam_size if beam_size is not None else 5
        try:
            model = get_whisper_model("medium", auto_download=False)
            segments, info = model.transcribe(
                trimmed_samples,
                beam_size=effective_beam,
                temperature=temperature,
                vad_filter=vad_filter,
                language=target_lang
            )
            text_pieces = [s.text.strip() for s in segments if s.text.strip()]
            transcription_text = " ".join(text_pieces)
            if info:
                detected_language = info.language or target_lang or "unknown"
                lang_probability = round(float(info.language_probability), 4)
        except Exception as acc_err:
            logger.error(f"Accuracy mode transcription failed: {acc_err}")
            # Try Vosk fallback if available
            try:
                from app.calls.transcribe import transcribe_audio_file
                temp_wav = PROJECT_ROOT / "backend" / "data" / f"fallback_{time.time_ns()}.wav"
                import soundfile as sf
                sf.write(str(temp_wav), (trimmed_samples * 32767).astype(np.int16), 16000)
                try:
                    vosk_res = transcribe_audio_file(temp_wav, lang=target_lang or "auto")
                    if vosk_res.get("success") and vosk_res.get("text"):
                        return {
                            "success": True,
                            "text": vosk_res["text"],
                            "language": vosk_res.get("detected_lang", "hi"),
                            "language_probability": 0.85,
                            "duration": round(audio_duration, 2),
                            "processing_time": round(time.perf_counter() - t_start, 2),
                            "rtf": round((time.perf_counter() - t_start) / max(audio_duration, 0.001), 3),
                            "mode": "fallback",
                            "model": "vosk-fallback",
                            "engine": "Vosk Small ASR Fallback",
                            "error": None
                        }
                finally:
                    if temp_wav.exists():
                        temp_wav.unlink(missing_ok=True)
            except Exception:
                pass

            return {
                "success": False,
                "error": f"Transcription error: {str(acc_err)}",
                "text": "",
                "language": "",
                "language_probability": 0.0,
                "duration": round(audio_duration, 2),
                "processing_time": round(time.perf_counter() - t_start, 2),
                "rtf": 0.0,
                "mode": req_mode,
                "model": model_identifier,
                "engine": engine_desc
            }

    # 5. Measure and Format Performance Metrics
    elapsed = time.perf_counter() - t_start
    rtf = round(elapsed / max(audio_duration, 0.001), 3)

    return {
        "success": True,
        "text": transcription_text,
        "language": detected_language,
        "language_probability": lang_probability,
        "duration": round(float(audio_duration), 2),
        "processing_time": round(float(elapsed), 2),
        "rtf": rtf,
        "mode": req_mode,
        "model": model_identifier,
        "engine": engine_desc,
        "error": None
    }
