"""
Offline Real-Time Streaming ASR Engine for Suraksha using Sherpa-ONNX
Supports continuous audio streaming, chunk-by-chunk decoding, Silero VAD,
noise suppression, and multi-lingual recognition (Hindi, English, Hinglish, Chhattisgarhi).
"""

import os
import io
import time
import json
import wave
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from collections import Counter
import numpy as np

logger = logging.getLogger("suraksha.streaming_asr")


def clean_repeated_hallucinations(text: str) -> str:
    """
    Cleans repetitive hallucinations and looping tokens common in autoregressive ASR models.
    Collapses stutter loops ('Good. Good. Good.' -> 'Good.'), deduplicates identical consecutive phrases,
    and removes trailing silence hallucination artifacts ('... Good. Good.').
    """
    if not text or not isinstance(text, str):
        return ""

    cleaned = text

    # 1. Deduplicate consecutive identical phrases or sentences (case-insensitive)
    cleaned = re.sub(r'([^.?!]+[.?!])(?:\s*\1)+', r'\1', cleaned, flags=re.IGNORECASE)

    # 2. Strip trailing repeated filler hallucinations (3+ repeats of 'Good.', 'Thank you.', 'Okay.', etc.)
    cleaned = re.sub(r'(?:\s*(?:Good|Thank you|Bye|Okay|Yes|No)[.!?]?){3,}\s*$', '', cleaned, flags=re.IGNORECASE)

    # 3. Collapse repetitive single-word loops: 'Good. Good. Good. Good.' -> 'Good.'
    cleaned = re.sub(r'\b([A-Za-z\u0900-\u097F]+)(?:[.,!?])?(?:\s+\1(?:[.,!?])?){2,}', r'\1.', cleaned, flags=re.IGNORECASE)

    # 4. Collapse adjacent identical words: 'the the' -> 'the'
    cleaned = re.sub(r'\b([A-Za-z\u0900-\u097F]+)\s+\1\b', r'\1', cleaned, flags=re.IGNORECASE)

    # 5. Clean excessive spaces
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
    return cleaned


def is_hallucination_loop(text: str) -> bool:
    """Detects whether recognized text is dominated by an artificial repetition loop."""
    if not text:
        return False
    tokens = re.findall(r'\b[A-Za-z\u0900-\u097F]+\b', text.lower())
    if len(tokens) >= 5:
        counts = Counter(tokens)
        most_common_word, most_common_count = counts.most_common(1)[0]
        if (most_common_count / float(len(tokens))) > 0.35:
            return True
    return False


def trim_trailing_silence(pcm_bytes: bytes, sample_rate: int = 16000, silence_threshold_rms: float = 120.0) -> bytes:
    """Trims trailing silence from 16kHz Int16 PCM buffer to prevent Whisper from looping on empty audio."""
    if len(pcm_bytes) < sample_rate * 2:
        return pcm_bytes
    samples = np.frombuffer(pcm_bytes, dtype=np.int16)
    frame_size = int(sample_rate * 0.1)  # 100ms frames
    last_sound_idx = len(samples)
    for i in range(len(samples) - frame_size, 0, -frame_size):
        frame = samples[i:i + frame_size]
        rms = np.sqrt(np.mean(frame.astype(np.float64) ** 2))
        if rms >= silence_threshold_rms:
            # Keep up to active sound + 0.5s margin
            last_sound_idx = min(len(samples), i + frame_size + int(sample_rate * 0.5))
            break
    else:
        return pcm_bytes
    return samples[:last_sound_idx].tobytes()

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

        # Sherpa-ONNX streaming Zipformer
        self.zipformer = get_streaming_zipformer()
        self.stream = self.zipformer.create_stream() if self.zipformer else None

        # Vosk Streaming Recognizers for Hindi and Indian English (lazily loaded on demand)
        self.vosk_rec_hi = None
        self.vosk_rec_en = None
        try:
            import vosk
            from app.calls.transcribe import find_vosk_model, get_or_load_vosk_model
            if language in ("hi", "chg"):
                m_hi = get_or_load_vosk_model(find_vosk_model("hi"))
                if m_hi:
                    self.vosk_rec_hi = vosk.KaldiRecognizer(m_hi, 16000)
                    self.vosk_rec_hi.SetWords(True)
            elif language == "en":
                m_en = get_or_load_vosk_model(find_vosk_model("en"))
                if m_en:
                    self.vosk_rec_en = vosk.KaldiRecognizer(m_en, 16000)
                    self.vosk_rec_en.SetWords(True)
        except Exception as ex:
            logger.debug(f"Vosk streaming init notice: {ex}")

        # Audio buffer for multilingual Whisper batching
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
        # Flush final results from Vosk
        if sess.vosk_rec_hi:
            try:
                fin_hi = json.loads(sess.vosk_rec_hi.FinalResult()).get("text", "").strip()
                if fin_hi and fin_hi not in sess.accumulated_text:
                    sess.accumulated_text.append(fin_hi)
            except Exception:
                pass
        if sess.vosk_rec_en:
            try:
                fin_en = json.loads(sess.vosk_rec_en.FinalResult()).get("text", "").strip()
                if fin_en and fin_en not in sess.accumulated_text:
                    sess.accumulated_text.append(fin_en)
            except Exception:
                pass

        full_transcript = clean_repeated_hallucinations(" ".join(sess.accumulated_text).strip())
        if sess.current_interim and sess.current_interim not in full_transcript:
            full_transcript = clean_repeated_hallucinations(f"{full_transcript} {sess.current_interim}".strip())

        # Run multilingual Whisper final pass only if audio buffer was captured and not silent
        trimmed_buffer = trim_trailing_silence(bytes(sess.pcm_buffer))
        if len(trimmed_buffer) >= 16000 * 2:
            try:
                whisper = get_whisper_recognizer(sess.language)
                if whisper:
                    samples_int16 = np.frombuffer(trimmed_buffer, dtype=np.int16)
                    samples_float32 = samples_int16.astype(np.float32) / 32768.0

                    # Chunk into <= 25-second windows to conform with Sherpa-ONNX 30s limit
                    win_size = int(25.0 * 16000)
                    w_parts = []
                    for s_idx in range(0, len(samples_float32), win_size):
                        w_chunk = samples_float32[s_idx:s_idx + win_size]
                        if len(w_chunk) < 8000:
                            continue
                        w_stream = whisper.create_stream()
                        w_stream.accept_waveform(16000, w_chunk)
                        whisper.decode_stream(w_stream)
                        w_seg = clean_repeated_hallucinations(w_stream.result.text.strip())
                        if w_seg and not is_hallucination_loop(w_seg):
                            w_parts.append(w_seg)

                    w_combined = clean_repeated_hallucinations(" ".join(w_parts).strip())
                    # Only accept Whisper text if it is meaningful, non-hallucinatory, and at least as complete
                    if w_combined and not is_hallucination_loop(w_combined) and len(w_combined.split()) >= len(full_transcript.split()):
                        full_transcript = w_combined
            except Exception as ex:
                logger.debug(f"Session close Whisper note: {ex}")

        # Wipe in-memory PCM audio buffer to prevent memory leakage
        if hasattr(sess, "pcm_buffer"):
            sess.pcm_buffer.clear()
        sess.stream = None
        return {
            "session_id": session_id,
            "duration_seconds": round(sess.total_audio_seconds, 2),
            "final_transcript": full_transcript,
            "text": full_transcript,
            "transcript": full_transcript
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

    # Append to rolling session buffer (capped at 30 seconds to prevent memory accumulation)
    sess.pcm_buffer.extend(pcm_bytes)
    MAX_ROLLING_BUFFER_BYTES = 30 * 16000 * 2  # 30 seconds at 16kHz Int16 (960 KB)
    if len(sess.pcm_buffer) > MAX_ROLLING_BUFFER_BYTES:
        sess.pcm_buffer = sess.pcm_buffer[-MAX_ROLLING_BUFFER_BYTES:]

    # 2. Continuous Real-time Streaming Recognition (Sherpa-ONNX Zipformer / Vosk)
    text_result = ""
    is_final = False
    engine_name = "sherpa-onnx-streaming"

    if language in ("hi", "chg") and sess.vosk_rec_hi:
        try:
            if sess.vosk_rec_hi.AcceptWaveform(pcm_bytes):
                v_res = json.loads(sess.vosk_rec_hi.Result())
                if v_res.get("text"):
                    v_text = clean_repeated_hallucinations(v_res["text"].strip())
                    if v_text and (not sess.accumulated_text or sess.accumulated_text[-1].lower() != v_text.lower()):
                        sess.accumulated_text.append(v_text)
                        text_result = v_text
                        is_final = True
            else:
                v_part = json.loads(sess.vosk_rec_hi.PartialResult())
                sess.current_interim = clean_repeated_hallucinations(v_part.get("partial", "").strip())
                text_result = sess.current_interim
        except Exception as e:
            logger.debug(f"Vosk streaming error: {e}")
    else:
        zipformer = sess.zipformer or get_streaming_zipformer()
        if zipformer and sess.stream and len(samples_float32) > 0:
            sess.stream.accept_waveform(sample_rate, samples_float32)

            while zipformer.is_ready(sess.stream):
                zipformer.decode_stream(sess.stream)

            # Check if an endpoint (end of phrase/pause) was detected
            if zipformer.is_endpoint(sess.stream):
                final_segment = zipformer.get_result(sess.stream).strip()
                clean_seg = clean_repeated_hallucinations(final_segment)
                if clean_seg and not is_hallucination_loop(clean_seg):
                    if not sess.accumulated_text or sess.accumulated_text[-1].lower() != clean_seg.lower():
                        sess.accumulated_text.append(clean_seg)
                        text_result = clean_seg
                        is_final = True
                zipformer.reset(sess.stream)
                sess.current_interim = ""
            else:
                interim = zipformer.get_result(sess.stream).strip()
                clean_interim = clean_repeated_hallucinations(interim)
                if not is_hallucination_loop(clean_interim):
                    sess.current_interim = clean_interim
                    text_result = clean_interim
                else:
                    sess.current_interim = ""
                    text_result = ""

    latency_ms = int((time.time() - start_time) * 1000)

    # Construct cumulative transcript
    accumulated = clean_repeated_hallucinations(" ".join(sess.accumulated_text).strip())
    full_text = clean_repeated_hallucinations(f"{accumulated} {sess.current_interim}".strip())

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
    with automatic chunking for long audio (> 25s) and fallback to Vosk if needed.
    Works 100% offline with zero cloud dependency.
    """
    from app.calls.transcribe import prepare_16k_mono_wav, transcribe_audio_file

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

                duration_sec = len(samples) / float(sr)
                window_size = int(25.0 * sr)  # 25-second windows to safely stay under 30s Sherpa limit

                chunk_texts = []
                for start_idx in range(0, len(samples), window_size):
                    chunk = samples[start_idx:start_idx + window_size]
                    if len(chunk) < int(0.5 * sr):
                        continue
                    stream = whisper.create_stream()
                    stream.accept_waveform(sr, chunk)
                    whisper.decode_stream(stream)
                    seg_text = clean_repeated_hallucinations(stream.result.text.strip())
                    if seg_text and not is_hallucination_loop(seg_text):
                        chunk_texts.append(seg_text)

                combined_whisper_text = clean_repeated_hallucinations(" ".join(chunk_texts).strip())
                if combined_whisper_text and len(combined_whisper_text.split()) >= 4:
                    return {
                        "text": combined_whisper_text,
                        "engine": "sherpa-onnx-whisper",
                        "detected_lang": lang if lang != "auto" else "hi/en",
                        "notice": f"Sherpa-ONNX Offline Multilingual Engine (100% On-Device • {len(chunk_texts)} windows processed)",
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
                text = clean_repeated_hallucinations(zipformer.get_result(stream).strip())
                if text and len(text.split()) >= 4:
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
        vosk_res = transcribe_audio_file(audio_path, lang=lang)
        if vosk_res and vosk_res.get("text"):
            vosk_res["text"] = clean_repeated_hallucinations(vosk_res["text"])
        return vosk_res

    finally:
        if temp_16k.exists():
            try:
                temp_16k.unlink()
            except Exception:
                pass
