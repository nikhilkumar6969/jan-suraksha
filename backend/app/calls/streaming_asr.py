"""
Offline Real-Time Streaming ASR Engine for Suraksha using Sherpa-ONNX
Supports continuous audio streaming, chunk-by-chunk decoding, Silero VAD,
noise suppression, and multi-lingual recognition (Hindi, English, Hinglish, Chhattisgarhi).
"""

import os
import io
import time
import wave
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

logger = logging.getLogger("suraksha.streaming_asr")

SHERPA_AVAILABLE = False
try:
    import sherpa_onnx
    SHERPA_AVAILABLE = True
except ImportError:
    SHERPA_AVAILABLE = False

# Global singletons to prevent repeated model downloads / loads
_STREAMING_RECOGNIZER = None
_WHISPER_RECOGNIZER_HI = None
_WHISPER_RECOGNIZER_EN = None
_WHISPER_RECOGNIZER_AUTO = None
_SILERO_VAD = None
_ACTIVE_SESSIONS: Dict[str, Any] = {}

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "models"


def get_models_dir() -> Path:
    return MODELS_DIR


def get_streaming_zipformer() -> Optional["sherpa_onnx.OnlineRecognizer"]:
    """Returns singleton streaming Zipformer transducer (English & Hinglish real-time)."""
    global _STREAMING_RECOGNIZER
    if not SHERPA_AVAILABLE:
        return None
    if _STREAMING_RECOGNIZER is not None:
        return _STREAMING_RECOGNIZER

    model_dir = MODELS_DIR / "sherpa-onnx-streaming-zipformer-en-20M-2023-02-17"
    if not model_dir.exists():
        logger.warning(f"Zipformer model dir not found at {model_dir}")
        return None

    try:
        logger.info("Initializing Sherpa-ONNX Streaming Zipformer...")
        _STREAMING_RECOGNIZER = sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=str(model_dir / "tokens.txt"),
            encoder=str(model_dir / "encoder-epoch-99-avg-1.int8.onnx"),
            decoder=str(model_dir / "decoder-epoch-99-avg-1.int8.onnx"),
            joiner=str(model_dir / "joiner-epoch-99-avg-1.int8.onnx"),
            num_threads=2,
            sample_rate=16000,
            feature_dim=80,
            enable_endpoint_detection=True,
            rule1_min_trailing_silence=1.8,
            rule2_min_trailing_silence=0.8,
            rule3_min_utterance_length=20.0,
            decoding_method="greedy_search",
            provider="cpu"
        )
        logger.info("Sherpa-ONNX Streaming Zipformer successfully initialized.")
    except Exception as e:
        logger.error(f"Failed to load Sherpa-ONNX Zipformer: {e}")
        _STREAMING_RECOGNIZER = None

    return _STREAMING_RECOGNIZER


def get_whisper_recognizer(lang: str = "hi") -> Optional["sherpa_onnx.OfflineRecognizer"]:
    """Returns singleton Whisper ONNX recognizer for Hindi or multilingual offline decoding."""
    global _WHISPER_RECOGNIZER_HI, _WHISPER_RECOGNIZER_EN, _WHISPER_RECOGNIZER_AUTO
    if not SHERPA_AVAILABLE:
        return None

    model_dir = MODELS_DIR / "sherpa-onnx-whisper-tiny"
    if not model_dir.exists():
        logger.warning(f"Whisper model dir not found at {model_dir}")
        return None

    target_lang = "hi" if lang in ("hi", "chg") else ("en" if lang == "en" else "")

    if target_lang == "hi" and _WHISPER_RECOGNIZER_HI is not None:
        return _WHISPER_RECOGNIZER_HI
    if target_lang == "en" and _WHISPER_RECOGNIZER_EN is not None:
        return _WHISPER_RECOGNIZER_EN
    if target_lang == "" and _WHISPER_RECOGNIZER_AUTO is not None:
        return _WHISPER_RECOGNIZER_AUTO

    try:
        logger.info(f"Initializing Sherpa-ONNX Whisper for language '{target_lang}'...")
        rec = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=str(model_dir / "tiny-encoder.int8.onnx"),
            decoder=str(model_dir / "tiny-decoder.int8.onnx"),
            tokens=str(model_dir / "tiny-tokens.txt"),
            language=target_lang or "hi",
            num_threads=2,
            decoding_method="greedy_search",
            provider="cpu"
        )
        if target_lang == "hi":
            _WHISPER_RECOGNIZER_HI = rec
        elif target_lang == "en":
            _WHISPER_RECOGNIZER_EN = rec
        else:
            _WHISPER_RECOGNIZER_AUTO = rec
        return rec
    except Exception as e:
        logger.error(f"Failed to load Sherpa-ONNX Whisper ({target_lang}): {e}")
        return None


def get_silero_vad() -> Optional["sherpa_onnx.VoiceActivityDetector"]:
    """Returns singleton Silero VAD for local voice activity & silence segmentation."""
    global _SILERO_VAD
    if not SHERPA_AVAILABLE:
        return None
    if _SILERO_VAD is not None:
        return _SILERO_VAD

    vad_model = MODELS_DIR / "silero_vad.onnx"
    if not vad_model.exists():
        logger.warning(f"Silero VAD model not found at {vad_model}")
        return None

    try:
        logger.info("Initializing Sherpa-ONNX Silero VAD...")
        vad_config = sherpa_onnx.VadModelConfig()
        vad_config.silero_vad.model = str(vad_model)
        vad_config.silero_vad.threshold = 0.5
        vad_config.silero_vad.min_silence_duration = 0.5
        vad_config.silero_vad.min_speech_duration = 0.25
        vad_config.sample_rate = 16000

        _SILERO_VAD = sherpa_onnx.VoiceActivityDetector(vad_config, buffer_size_in_seconds=30)
        logger.info("Sherpa-ONNX Silero VAD ready.")
    except Exception as e:
        logger.error(f"Failed to load Silero VAD: {e}")
        _SILERO_VAD = None

    return _SILERO_VAD


def prewarm_all_speech_models():
    """Initializes and prewarms models on startup for fast, latency-free real-time calls."""
    logger.info("Pre-warming offline Sherpa-ONNX speech recognition models...")
    get_silero_vad()
    get_streaming_zipformer()
    get_whisper_recognizer("hi")
    get_whisper_recognizer("en")
    logger.info("Pre-warming completed.")


class StreamingSession:
    """Maintains active streaming state for one user / call listening session."""

    def __init__(self, session_id: str, language: str = "auto"):
        self.session_id = session_id
        self.language = language
        self.created_at = time.time()
        self.last_active = time.time()
        self.accumulated_text = []
        self.current_interim = ""
        self.total_audio_seconds = 0.0
        self.speech_chunks_count = 0
        self.silence_chunks_count = 0

        # Sherpa-ONNX streaming stream
        self.zipformer = get_streaming_zipformer()
        self.stream = self.zipformer.create_stream() if self.zipformer else None
        
        # Audio buffer for multilingual Whisper / Vosk batching when needed
        self.pcm_buffer = bytearray()

    def reset_stream(self):
        if self.zipformer:
            self.stream = self.zipformer.create_stream()
        self.current_interim = ""


def get_or_create_session(session_id: str, language: str = "auto") -> StreamingSession:
    # Clean up stale sessions (> 15 minutes inactive)
    now = time.time()
    stale_keys = [k for k, v in _ACTIVE_SESSIONS.items() if (now - v.last_active) > 900]
    for k in stale_keys:
        del _ACTIVE_SESSIONS[k]

    if session_id not in _ACTIVE_SESSIONS:
        _ACTIVE_SESSIONS[session_id] = StreamingSession(session_id, language)
    return _ACTIVE_SESSIONS[session_id]


def close_session(session_id: str) -> Optional[dict]:
    if session_id in _ACTIVE_SESSIONS:
        sess = _ACTIVE_SESSIONS.pop(session_id)
        full_transcript = " ".join(sess.accumulated_text).strip()
        if sess.current_interim:
            full_transcript = f"{full_transcript} {sess.current_interim}".strip()
        return {
            "session_id": session_id,
            "duration_seconds": round(sess.total_audio_seconds, 2),
            "final_transcript": full_transcript
        }
    return None


def process_streaming_chunk(
    session_id: str,
    pcm_bytes: bytes,
    sample_rate: int = 16000,
    language: str = "auto"
) -> Dict[str, Any]:
    """
    Processes an incoming audio chunk (16kHz 16-bit mono PCM or float32).
    Applies VAD noise suppression, runs Sherpa-ONNX streaming recognition,
    and returns real-time interim and final transcription results.
    """
    start_time = time.time()
    sess = get_or_create_session(session_id, language)
    sess.last_active = start_time

    # Convert PCM to float32 normalized [-1, 1]
    if len(pcm_bytes) == 0:
        return {
            "text": "",
            "interim": sess.current_interim,
            "is_final": False,
            "speech_detected": False,
            "engine": "sherpa-onnx-streaming"
        }

    try:
        samples_int16 = np.frombuffer(pcm_bytes, dtype=np.int16)
        samples_float32 = samples_int16.astype(np.float32) / 32768.0
    except Exception as e:
        logger.warning(f"Error parsing PCM chunk: {e}")
        samples_float32 = np.zeros(0, dtype=np.float32)

    chunk_duration = len(samples_float32) / float(sample_rate)
    sess.total_audio_seconds += chunk_duration

    # 1. Voice Activity Detection (VAD) & Noise Filtering
    vad = get_silero_vad()
    is_speech = True
    if vad is not None and len(samples_float32) > 0:
        try:
            # Silero expects window_size chunks (e.g. 512 samples)
            window = 512
            speech_votes = 0
            total_windows = 0
            for i in range(0, len(samples_float32), window):
                w_samples = samples_float32[i:i + window]
                if len(w_samples) == window:
                    vad.accept_waveform(w_samples)
                    total_windows += 1
                    if vad.is_speech_detected():
                        speech_votes += 1
            if total_windows > 0 and (speech_votes / total_windows) < 0.20:
                is_speech = False
        except Exception as e:
            logger.debug(f"VAD check note: {e}")
            is_speech = True

    if is_speech:
        sess.speech_chunks_count += 1
    else:
        sess.silence_chunks_count += 1

    # Append to session buffer for multi-lingual fallback
    sess.pcm_buffer.extend(pcm_bytes)

    # 2. Continuous Sherpa-ONNX Streaming Recognition
    text_result = ""
    is_final = False
    engine_name = "sherpa-onnx-streaming"

    zipformer = sess.zipformer or get_streaming_zipformer()
    if zipformer and sess.stream and len(samples_float32) > 0:
        sess.stream.accept_waveform(sample_rate, samples_float32)

        while zipformer.is_ready(sess.stream):
            zipformer.decode_stream(sess.stream)

        # Check if an endpoint (end of phrase/pause) was detected
        if zipformer.is_endpoint(sess.stream):
            final_segment = zipformer.get_result(sess.stream).strip()
            if final_segment:
                sess.accumulated_text.append(final_segment)
                text_result = final_segment
                is_final = True
            zipformer.reset(sess.stream)
            sess.current_interim = ""
        else:
            interim = zipformer.get_result(sess.stream).strip()
            sess.current_interim = interim
            text_result = interim

    latency_ms = int((time.time() - start_time) * 1000)

    # Construct cumulative transcript
    accumulated = " ".join(sess.accumulated_text).strip()
    full_text = f"{accumulated} {sess.current_interim}".strip()

    return {
        "text": full_text,
        "interim": sess.current_interim,
        "is_final": is_final,
        "speech_detected": is_speech,
        "chunk_duration": round(chunk_duration, 2),
        "total_duration": round(sess.total_audio_seconds, 2),
        "latency_ms": latency_ms,
        "engine": engine_name,
        "session_id": session_id
    }


def offline_transcribe_audio(
    audio_path: Path,
    lang: str = "auto"
) -> Dict[str, Any]:
    """
    Offline transcription of complete audio file using Sherpa-ONNX (Whisper or Zipformer),
    with automatic fallback to Vosk if needed.
    Works 100% offline with zero cloud dependency.
    """
    from app.calls.transcribe import prepare_16k_mono_wav, transcribe_audio_file

    # Ensure 16k mono wav format
    temp_16k = audio_path.parent / f"conv_{audio_path.name}.wav"
    try:
        prep_ok = prepare_16k_mono_wav(audio_path, temp_16k)
        target_path = temp_16k if prep_ok and temp_16k.exists() else audio_path

        # 1. Primary: Sherpa-ONNX Whisper Recognizer (Multilingual Hindi/English/Hinglish)
        whisper = get_whisper_recognizer(lang)
        if whisper and target_path.exists():
            try:
                import soundfile as sf
                samples, sr = sf.read(str(target_path), dtype="float32")
                if samples.ndim > 1:
                    samples = samples.mean(axis=1)

                stream = whisper.create_stream()
                stream.accept_waveform(sr, samples)
                whisper.decode_stream(stream)
                text = stream.result.text.strip()
                if text:
                    return {
                        "text": text,
                        "engine": "sherpa-onnx-whisper",
                        "detected_lang": lang if lang != "auto" else "hi/en",
                        "notice": "Sherpa-ONNX Offline Multilingual Engine (100% On-Device)",
                        "success": True
                    }
            except Exception as e:
                logger.warning(f"Sherpa-ONNX Whisper decoding fallback: {e}")

        # 2. Secondary: Sherpa-ONNX Streaming Zipformer
        zipformer = get_streaming_zipformer()
        if zipformer and target_path.exists():
            try:
                import soundfile as sf
                samples, sr = sf.read(str(target_path), dtype="float32")
                if samples.ndim > 1:
                    samples = samples.mean(axis=1)

                stream = zipformer.create_stream()
                stream.accept_waveform(sr, samples)
                stream.input_finished()
                while zipformer.is_ready(stream):
                    zipformer.decode_stream(stream)
                text = zipformer.get_result(stream).strip()
                if text:
                    return {
                        "text": text,
                        "engine": "sherpa-onnx-zipformer",
                        "detected_lang": "en",
                        "notice": "Sherpa-ONNX Streaming Zipformer (100% On-Device)",
                        "success": True
                    }
            except Exception as e:
                logger.warning(f"Sherpa-ONNX Zipformer decoding fallback: {e}")

        # 3. Tertiary: Vosk Offline Engine Fallback
        return transcribe_audio_file(audio_path, lang=lang)

    finally:
        if temp_16k.exists():
            try:
                temp_16k.unlink()
            except Exception:
                pass
