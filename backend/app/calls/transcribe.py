"""
Offline Call Audio Transcriber for Suraksha using Vosk & SoundFile
Handles audio decoding, stereo-to-mono, 16kHz resampling, and offline Vosk ASR.
"""

import os
import wave
import json
import logging
from pathlib import Path
from typing import Optional, Dict

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
            _MODEL_CACHE[path_str] = vosk.Model(path_str)
        except Exception as e:
            logger.error(f"Failed to load Vosk model from {path_str}: {e}")
            return None
    return _MODEL_CACHE[path_str]

def prepare_16k_mono_wav(input_path: Path, output_path: Path) -> bool:
    """
    Decodes input audio (WAV, MP3, OGG, FLAC) and converts to 16kHz mono 16-bit PCM WAV.
    Uses soundfile + scipy.
    """
    try:
        import soundfile as sf
        import numpy as np

        data, sr = sf.read(str(input_path))
        
        # 1. Convert stereo/multichannel to mono
        if data.ndim > 1:
            data = data.mean(axis=1)

        # 2. Resample to 16000 Hz if needed
        if sr != 16000:
            try:
                import scipy.signal
                num_samples = int(len(data) * 16000 / sr)
                data = scipy.signal.resample(data, num_samples)
            except Exception:
                # Simple linear interpolation fallback
                old_indices = np.arange(len(data))
                new_indices = np.linspace(0, len(data) - 1, int(len(data) * 16000 / sr))
                data = np.interp(new_indices, old_indices, data)

        # 3. Normalize & clamp to int16 PCM
        data_int16 = np.clip(data * 32767.0, -32768.0, 32767.0).astype(np.int16)
        
        # 4. Write as standard 16kHz mono 16-bit PCM WAV
        sf.write(str(output_path), data_int16, 16000, subtype='PCM_16')
        return True
    except Exception as e:
        logger.warning(f"SoundFile conversion failed: {e}. Trying standard wave fallback.")
        
        # Fallback for already valid WAV files
        try:
            with wave.open(str(input_path), "rb") as wf_in:
                if wf_in.getnchannels() == 1 and wf_in.getframerate() in [8000, 16000] and wf_in.getsampwidth() == 2:
                    # Already valid PCM 16-bit mono
                    import shutil
                    shutil.copyfile(str(input_path), str(output_path))
                    return True
        except Exception:
            pass

        return False

def transcribe_audio_file(file_path: Path, lang: str = "hi") -> dict:
    """
    Transcribe audio file using local Vosk ASR engine.
    Returns:
        {
            "success": bool,
            "text": str,
            "notice": str
        }
    """
    if not VOSK_AVAILABLE:
        return {
            "success": False,
            "text": "",
            "notice": "Vosk library not available in environment. Please paste or type call transcript."
        }

    model_path = find_vosk_model(lang=lang)
    if not model_path:
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
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or rate not in [8000, 16000]:
            return {
                "success": False,
                "text": "",
                "notice": "Audio conversion could not produce 16kHz mono PCM. Please paste or upload transcript below."
            }

        model = get_or_load_vosk_model(model_path)
        if not model:
            return {
                "success": False,
                "text": "",
                "notice": "Could not initialize offline Vosk model."
            }

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
        full_transcript = " ".join(results).strip()

        if full_transcript:
            return {
                "success": True,
                "text": full_transcript,
                "notice": f"Successfully transcribed offline with Vosk ({model_path.name})."
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
