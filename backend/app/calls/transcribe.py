"""
Offline Call Audio Transcriber for Suraksha using Vosk & SoundFile
Supports dual-pass auto-detection (Hindi & Indian English), audio decoding,
stereo-to-mono conversion, 16kHz resampling, and offline Vosk ASR.
"""

import os
import wave
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Tuple

logger = logging.getLogger("suraksha.transcribe")

VOSK_AVAILABLE = False
try:
    import vosk
    # Disable verbose Vosk C-level logging
    vosk.SetLogLevel(-1)
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

# In-memory model cache to avoid repeated disk reads
_MODEL_CACHE: Dict[str, "vosk.Model"] = {}

# Lexical dictionaries for language scoring & scam detection (English, Hinglish, Hindi, Chhattisgarhi)
SCAM_KEYWORDS_EN = {
    "police", "customs", "cbi", "arrest", "court", "warrant", "bank", "account",
    "kyc", "otp", "debit", "credit", "money", "laundering", "parcel", "narcotics",
    "drugs", "passports", "bail", "bond", "transfer", "urgent", "immediately",
    "disconnect", "inspector", "officer", "penalty", "charge", "verification",
    "anydesk", "teamviewer", "electricity", "bill", "power", "cut", "lock",
    "blocked", "suspended", "security", "legal", "action", "order", "call", "service",
    # Hinglish phonetic variants
    "paisa", "rupaye", "bijli", "line", "khata", "thana", "band", "batao",
    "bhejo", "karo", "kare", "kat", "pataw", "tor", "tola"
}

COMMON_WORDS_EN = {
    "this", "is", "from", "you", "are", "do", "not", "the", "and", "in", "to",
    "for", "your", "by", "have", "will", "be", "with", "hello", "sir", "madam",
    "today", "now", "please", "speaking", "department", "international", "number",
    # Hinglish grammar markers
    "aapka", "hai", "nahi", "raat", "turant", "bol", "raha", "hoon", "se", "ko"
}

SCAM_KEYWORDS_HI = {
    "पुलिस", "कस्टम", "कस्टम्स", "सीबीआई", "अरेस्ट", "गिरफ्तार", "थाना", "वारंट",
    "कोर्ट", "अदालत", "बैंक", "खाता", "केवाईसी", "ओटीपी", "डेबिट", "क्रेडिट",
    "पैसे", "रुपये", "लांड्रिंग", "पार्सल", "ड्रग्स", "नारकोटिक्स", "पासपोर्ट",
    "बेल", "बांड", "ट्रांसफर", "तुरंत", "अभी", "डिस्कनेक्ट", "फोन", "इंस्पेक्टर",
    "अधिकारी", "पेनल्टी", "चालान", "सत्यापन", "एनीडेस्क", "बिजली", "बिल",
    "काट", "बंद", "फ्रीज", "सुरक्षा", "कार्रवाई", "कानूनी", "अवैध",
    # Chhattisgarhi (CG) scam markers
    "पईसा", "पइसा", "तोर", "तोला", "कट जाही", "कटही", "पटाव", "डारव", "भेजव",
    "बताव", "झन", "संझा", "ककरो", "चरस", "गांजा", "महतारी"
}

COMMON_WORDS_HI = {
    "है", "हैं", "से", "का", "की", "के", "में", "पर", "को", "नहीं", "और",
    "यह", "वह", "किया", "गया", "रहा", "रहे", "रही", "बोल", "नमस्कार", "नमस्ते",
    "सर", "मैडम", "आप", "आपका", "आपके", "हूँ", "हम", "दिए", "करें", "करो",
    # Chhattisgarhi common tokens
    "हस", "हंव", "हे", "नइ", "बर", "म", "ल", "आए", "गे", "दिखत", "लगाके", "छुवव"
}

def find_vosk_model(lang: str = "hi") -> Optional[Path]:
    """Find appropriate Vosk model directory based on language preference."""
    models_dir = Path(__file__).resolve().parent.parent.parent / "models"
    
    if lang.startswith("en"):
        candidates = [
            models_dir / "vosk-model-small-en-in",
            models_dir / "vosk-model-small-hi",
            Path.home() / ".cache" / "vosk" / "vosk-model-small-en-in"
        ]
    else:
        candidates = [
            models_dir / "vosk-model-small-hi",
            models_dir / "vosk-model-small-en-in",
            Path.home() / ".cache" / "vosk" / "vosk-model-small-hi"
        ]

    for c in candidates:
        if c.exists() and (c / "am").exists():
            return c
    return None

def get_or_load_vosk_model(model_path: Path) -> Optional["vosk.Model"]:
    """Load and cache Vosk model instance."""
    path_str = str(model_path.resolve())
    if path_str not in _MODEL_CACHE:
        try:
            logger.info(f"Loading Vosk model into memory: {path_str}")
            _MODEL_CACHE[path_str] = vosk.Model(path_str)
        except Exception as e:
            logger.error(f"Failed to load Vosk model from {path_str}: {e}")
            return None
    return _MODEL_CACHE[path_str]

def prewarm_models():
    """Pre-warm both Hindi and English models on startup."""
    m_hi = find_vosk_model("hi")
    if m_hi:
        get_or_load_vosk_model(m_hi)
    m_en = find_vosk_model("en")
    if m_en:
        get_or_load_vosk_model(m_en)

def prepare_16k_mono_wav(input_path: Path, output_path: Path) -> bool:
    """
    Decodes ANY input audio format (WebM, M4A, AAC, MP3, OGG, Opus, AMR, WAV, etc.)
    and converts it to standard 16kHz mono 16-bit PCM WAV for Vosk ASR.
    Primary decoder: PyAV (FFmpeg bindings) - handles all containers and codecs.
    Fallback decoder: SoundFile + scipy / standard wave.
    """
    # 1. Primary: PyAV (Universal multi-format decoder)
    try:
        import av
        container = av.open(str(input_path))
        audio_streams = [s for s in container.streams if s.type == 'audio']
        if not audio_streams:
            container.close()
            raise ValueError("No audio streams found in file")

        resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)
        frames_count = 0
        with wave.open(str(output_path), 'wb') as out_wav:
            out_wav.setnchannels(1)
            out_wav.setsampwidth(2)
            out_wav.setframerate(16000)
            for frame in container.decode(audio=0):
                for resampled in resampler.resample(frame):
                    out_wav.writeframes(resampled.to_ndarray().tobytes())
                    frames_count += 1
        container.close()
        if frames_count > 0 and output_path.exists() and output_path.stat().st_size > 44:
            return True
    except Exception as e:
        logger.warning(f"PyAV audio decode fallback: {e}")

    # 2. Secondary: SoundFile + Scipy
    try:
        import soundfile as sf
        import numpy as np

        data, sr = sf.read(str(input_path))
        if data.ndim > 1:
            data = data.mean(axis=1)

        if sr != 16000:
            try:
                import scipy.signal
                num_samples = int(len(data) * 16000 / sr)
                data = scipy.signal.resample(data, num_samples)
            except Exception:
                old_indices = np.arange(len(data))
                new_indices = np.linspace(0, len(data) - 1, int(len(data) * 16000 / sr))
                data = np.interp(new_indices, old_indices, data)

        data_int16 = np.clip(data * 32767.0, -32768.0, 32767.0).astype(np.int16)
        sf.write(str(output_path), data_int16, 16000, subtype='PCM_16')
        return True
    except Exception as e:
        logger.warning(f"SoundFile decode fallback: {e}")

    # 3. Tertiary: Standard WAV file copy
    try:
        with wave.open(str(input_path), "rb") as wf_in:
            if wf_in.getnchannels() == 1 and wf_in.getframerate() in [8000, 16000] and wf_in.getsampwidth() == 2:
                import shutil
                shutil.copyfile(str(input_path), str(output_path))
                return True
    except Exception:
        pass

    return False

def _run_vosk_recognition(wav_path: Path, model: "vosk.Model", sample_rate: int) -> str:
    """Run KaldiRecognizer on 16kHz mono WAV stream."""
    try:
        wf = wave.open(str(wav_path), "rb")
        rate = wf.getframerate()
        rec = vosk.KaldiRecognizer(model, rate)
        rec.SetWords(True)

        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                part = json.loads(rec.Result())
                if part.get("text"):
                    results.append(part["text"])

        final_part = json.loads(rec.FinalResult())
        if final_part.get("text"):
            results.append(final_part["text"])

        wf.close()
        return " ".join(results).strip()
    except Exception as e:
        logger.warning(f"Recognition loop failed: {e}")
        return ""

def score_transcript_quality(text: str) -> Tuple[float, str]:
    """
    Score linguistic and semantic quality of recognized transcript.
    Returns (score, detected_lang: 'en'|'hi'|'unknown')
    """
    if not text:
        return 0.0, "unknown"

    tokens = [t.lower() for t in text.split()]
    total_words = len(tokens)
    if total_words == 0:
        return 0.0, "unknown"

    en_scam = sum(1 for w in tokens if w in SCAM_KEYWORDS_EN)
    en_common = sum(1 for w in tokens if w in COMMON_WORDS_EN)
    
    hi_scam = sum(1 for w in tokens if w in SCAM_KEYWORDS_HI)
    hi_common = sum(1 for w in tokens if w in COMMON_WORDS_HI)

    en_score = (en_scam * 3.5) + (en_common * 1.5) + (total_words * 0.1)
    hi_score = (hi_scam * 3.5) + (hi_common * 1.5) + (total_words * 0.1)

    if en_score > hi_score and en_score > 1.0:
        return en_score, "en"
    elif hi_score >= en_score and hi_score > 1.0:
        return hi_score, "hi"
    else:
        return max(en_score, hi_score, total_words * 0.1), "unknown"

def transcribe_audio_file(file_path: Path, lang: str = "auto") -> dict:
    """
    Transcribe audio file using offline Vosk ASR engine.
    Supports auto-detection between Hindi and Indian English.
    """
    if not VOSK_AVAILABLE:
        return {
            "success": False,
            "text": "",
            "notice": "Vosk library not available in environment. Please paste or type call transcript."
        }

    model_hi = find_vosk_model(lang="hi")
    model_en = find_vosk_model(lang="en")

    if not model_hi and not model_en:
        return {
            "success": False,
            "text": "",
            "notice": "Offline Vosk speech model not detected in backend/models/. You can paste or type call transcript directly."
        }

    converted_wav = file_path.parent / f"conv_{file_path.stem}.wav"
    try:
        success_conv = prepare_16k_mono_wav(file_path, converted_wav)
        target_path = converted_wav if success_conv and converted_wav.exists() else file_path

        wf = wave.open(str(target_path), "rb")
        rate = wf.getframerate()
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        wf.close()

        if channels != 1 or sampwidth != 2 or rate not in [8000, 16000]:
            return {
                "success": False,
                "text": "",
                "notice": "Audio conversion could not produce 16kHz mono PCM. Please paste or upload transcript below."
            }

        transcripts = {}

        # 1. Run transcription
        if lang == "en" and model_en:
            m = get_or_load_vosk_model(model_en)
            if m:
                transcripts["en"] = _run_vosk_recognition(target_path, m, rate)
        elif lang == "hi" and model_hi:
            m = get_or_load_vosk_model(model_hi)
            if m:
                transcripts["hi"] = _run_vosk_recognition(target_path, m, rate)
        else:
            # Auto-detect mode: Run both models or best first
            # Usually Indian scams use Hinglish / English terms (Police, Arrest, Customs, KYC)
            if model_en:
                m_en = get_or_load_vosk_model(model_en)
                if m_en:
                    transcripts["en"] = _run_vosk_recognition(target_path, m_en, rate)
            if model_hi:
                m_hi = get_or_load_vosk_model(model_hi)
                if m_hi:
                    transcripts["hi"] = _run_vosk_recognition(target_path, m_hi, rate)

        # 2. Evaluate and pick winning transcript
        best_text = ""
        best_lang = "unknown"
        best_score = -1.0

        for l_key, text in transcripts.items():
            score, detected_lang = score_transcript_quality(text)
            if score > best_score and len(text.strip()) > 0:
                best_score = score
                best_text = text
                best_lang = l_key

        # If user explicitly asked for 'hi' but it was gibberish while 'en' model has valid words, fallback gracefully
        if not best_text and model_en and "en" not in transcripts:
            m_en = get_or_load_vosk_model(model_en)
            if m_en:
                t_en = _run_vosk_recognition(target_path, m_en, rate)
                if len(t_en) > len(best_text):
                    best_text = t_en
                    best_lang = "en"

        if not best_text and model_hi and "hi" not in transcripts:
            m_hi = get_or_load_vosk_model(model_hi)
            if m_hi:
                t_hi = _run_vosk_recognition(target_path, m_hi, rate)
                if len(t_hi) > len(best_text):
                    best_text = t_hi
                    best_lang = "hi"

        if best_text:
            model_used_name = "Indian English (vosk-model-small-en-in)" if best_lang == "en" else "Hindi (vosk-model-small-hi)"
            return {
                "success": True,
                "text": best_text,
                "detected_lang": best_lang,
                "notice": f"Successfully extracted speech offline with Vosk [{model_used_name}]."
            }
        else:
            return {
                "success": False,
                "text": "",
                "notice": "Audio file processed, but no clear speech was recognized. Please paste conversation."
            }

    except Exception as e:
        logger.error(f"Error during audio transcription: {e}")
        return {
            "success": False,
            "text": "",
            "notice": f"Audio processing notice: {str(e)}. Please paste call transcript below."
        }
    finally:
        if converted_wav.exists():
            try:
                converted_wav.unlink()
            except Exception:
                pass
