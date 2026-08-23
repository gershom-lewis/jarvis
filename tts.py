"""
JARVIS — mouth. Natural neural text-to-speech via Microsoft edge-tts (free, no
API key, genuinely human-sounding). Falls back to the built-in Windows voice if
edge-tts can't reach the network. Cost: $0.

Change the voice with the JARVIS_VOICE env var, or edit VOICE below.
  Female (natural): en-US-JennyNeural · en-US-AriaNeural · en-US-AvaNeural
                    en-US-EmmaNeural · en-US-MichelleNeural
  Male   (natural): en-US-GuyNeural · en-US-AndrewNeural · en-US-BrianNeural
"""

import asyncio
import os
import tempfile

import edge_tts

VOICE = os.environ.get("JARVIS_VOICE", "en-US-AriaNeural")
_TMP = os.path.join(tempfile.gettempdir(), "jarvis_tts.mp3")


async def _synth(text: str, path: str, voice: str) -> None:
    await edge_tts.Communicate(text, voice).save(path)


def speak(text: str) -> None:
    if not text:
        return
    try:
        asyncio.run(_synth(text, _TMP, VOICE))
        from playsound import playsound
        playsound(_TMP)
    except Exception as exc:
        print(f"  (neural voice unavailable: {exc} — falling back to local voice)")
        _fallback(text)


def _fallback(text: str) -> None:
    """Offline safety net: the built-in Windows voice (Zira)."""
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
