"""
Iris (JARVIS) — mouth. Tiered text-to-speech, best available first:

  1. ElevenLabs (premium, human-level) — used IF ELEVENLABS_API_KEY + ELEVENLABS_VOICE
     are set in .env. Small per-use cost; free starter tier available.
  2. Microsoft edge-tts neural (free, no key) — natural, needs internet.
  3. Built-in Windows voice (offline safety net).

Set the ElevenLabs voice by pasting a Voice ID from the ElevenLabs Voice Library
into ELEVENLABS_VOICE. Change the free voice with JARVIS_VOICE.
"""

import asyncio
import os
import tempfile

import edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
_TMP = os.path.join(tempfile.gettempdir(), "jarvis_tts.mp3")


def _load_env(path: str = os.path.join(HERE, ".env")) -> dict:
    values: dict = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8-sig"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                values[k.strip()] = v.strip().strip('"').strip("'")
    return values


_CFG = _load_env()
ELEVEN_KEY = _CFG.get("ELEVENLABS_API_KEY") or os.environ.get("ELEVENLABS_API_KEY")
ELEVEN_VOICE = _CFG.get("ELEVENLABS_VOICE", "")
EDGE_VOICE = _CFG.get("JARVIS_VOICE") or os.environ.get("JARVIS_VOICE", "en-US-AriaNeural")


def _play(path: str) -> None:
    from playsound import playsound
    playsound(path)


def speak(text: str) -> None:
    if not text:
        return
    if ELEVEN_KEY and ELEVEN_VOICE and _speak_elevenlabs(text):
        return
    if _speak_edge(text):
        return
    _speak_windows(text)


def _speak_elevenlabs(text: str) -> bool:
    """Premium human-level voice via the ElevenLabs REST API."""
    import requests
    try:
        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE}",
            headers={
                "xi-api-key": ELEVEN_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            json={
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
            timeout=30,
        )
        if resp.status_code == 200 and resp.content:
            with open(_TMP, "wb") as fh:
                fh.write(resp.content)
            _play(_TMP)
            return True
        print(f"  (ElevenLabs {resp.status_code}: {resp.text[:120]} — using free voice)")
    except Exception as exc:
        print(f"  (ElevenLabs error: {exc} — using free voice)")
    return False


def _speak_edge(text: str) -> bool:
    """Free neural voice via Microsoft edge-tts."""
    try:
        asyncio.run(edge_tts.Communicate(text, EDGE_VOICE).save(_TMP))
        _play(_TMP)
        return True
    except Exception as exc:
        print(f"  (neural voice unavailable: {exc} — using local voice)")
    return False


def _speak_windows(text: str) -> None:
    """Offline safety net: the built-in Windows voice."""
    import subprocess
    safe = text.replace("'", "''")
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Add-Type -AssemblyName System.Speech; "
         "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
         "try { $s.SelectVoice('Microsoft Zira Desktop') } catch {}; "
         f"$s.Rate = 1; $s.Speak('{safe}')"],
        check=False,
    )
