"""
JARVIS — ears. Push-to-talk mic capture + local speech-to-text (faster-whisper).
Runs entirely on this machine. No audio ever leaves the laptop. Cost: $0.
"""

import os
import queue
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
# Accuracy vs speed: small (default) · small.en (more accurate for English) · medium
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")
# Pick a specific mic by index/name; None = system default. List: python jarvis.py --mics
_MIC = os.environ.get("MIC_DEVICE")
if _MIC is not None and _MIC.strip().isdigit():
    _MIC = int(_MIC.strip())
_model = None


def get_model(size: str = WHISPER_MODEL):
    """Load the Whisper model once (cached after first use)."""
    global _model
    if _model is None:
        _model = WhisperModel(size, device="cpu", compute_type="int8")
    return _model


def record_until_enter() -> np.ndarray:
    """Record from the default mic until the user presses Enter (push-to-talk)."""
    frames: list = []
    q: "queue.Queue" = queue.Queue()

    def _cb(indata, _frames, _time, status):
        q.put(indata.copy())

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, device=_MIC,
                            dtype="float32", callback=_cb):
            input()  # blocks here while the mic records in the background
    except Exception as exc:
        print(f"  (mic error: {exc})")
        return np.zeros(0, dtype=np.float32)

    while not q.empty():
        frames.append(q.get())
    if not frames:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(frames, axis=0).flatten().astype(np.float32)


def transcribe(audio: np.ndarray, size: str = WHISPER_MODEL) -> str:
    """Turn recorded audio into text. Returns '' if nothing usable was captured."""
    if audio is None or len(audio) < int(SAMPLE_RATE * 0.3):  # under ~0.3s = nothing
        return ""
    model = get_model(size)
    segments, _info = model.transcribe(audio, language="en", vad_filter=True)
    return " ".join(seg.text for seg in segments).strip()
