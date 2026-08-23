"""
JARVIS — mouth. Local text-to-speech via the built-in Windows voice (pyttsx3 / SAPI5).
Offline, free, no per-minute fees. Cost: $0.
"""

import pyttsx3

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 185)   # a touch faster than default
        _engine.setProperty("volume", 1.0)
        # Prefer a clearer default voice if more than one is installed.
        try:
            voices = _engine.getProperty("voices")
            if voices:
                _engine.setProperty("voice", voices[0].id)
        except Exception:
            pass
    return _engine


def speak(text: str) -> None:
    if not text:
        return
    engine = _get_engine()
    engine.say(text)
    engine.runAndWait()
