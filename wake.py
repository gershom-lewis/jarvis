"""
Iris — v0.2 wake word ("Hey Iris"). Always-listening, hands-free.

HARDENED (automation-hardening standard, since the mic is always on):
  • The listen loop never dies silently — mic/transcription hiccups are caught
    and it keeps listening.
  • Ctrl+C stops it cleanly.
  • It only calls the Claude API when the wake word actually triggers a command,
    so cost stays controlled.
  • It's a foreground app you start/stop — nothing to persist across reboot.

Wake detection uses local Whisper (free, no extra keys). It's not the lowest-CPU
option — a dedicated engine like Picovoice Porcupine is — but it works today with
zero setup. We can swap in Porcupine later for lighter always-on CPU.
"""

import collections
import time

import numpy as np
import sounddevice as sd

from brain import Brain
from stt import transcribe
from tts import speak

SR = 16000
BLOCK = int(SR * 0.03)  # 30 ms frames
WAKE_WORDS = ("iris", "irises", "irish", "hey iris")  # tolerate common mis-hears


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x))) + 1e-9)


def calibrate(seconds: float = 1.0) -> float:
    """Measure ambient noise, set a speech threshold above it."""
    frames = []
    with sd.InputStream(samplerate=SR, channels=1, dtype="float32") as s:
        for _ in range(int(seconds / 0.03)):
            data, _ = s.read(BLOCK)
            frames.append(data.copy())
    ambient = _rms(np.concatenate(frames).flatten())
    return max(0.014, ambient * 3.0)


def record_utterance(threshold: float, max_sec: float = 9.0,
                     silence_sec: float = 0.8, preroll_sec: float = 0.3) -> np.ndarray:
    """Wait for speech, record until ~silence, return the audio."""
    pre = collections.deque(maxlen=max(1, int(preroll_sec / 0.03)))
    rec: list = []
    started = False
    silent = 0.0
    t0 = time.time()
    with sd.InputStream(samplerate=SR, channels=1, dtype="float32") as s:
        while True:
            data, _ = s.read(BLOCK)
            block = data.copy().flatten()
            energy = _rms(block)
            if not started:
                pre.append(block)
                if energy > threshold:
                    started = True
                    rec.extend(pre)
                    rec.append(block)
                    t0 = time.time()
            else:
                rec.append(block)
                silent = silent + 0.03 if energy < threshold else 0.0
                if silent >= silence_sec or (time.time() - t0) > max_sec:
                    break
    if not rec:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(rec).flatten().astype(np.float32)


def _command_after_wake(text: str) -> str:
    """Return whatever was said after the wake word, if anything."""
    low = text.lower()
    for w in ("hey iris", "iris"):
        i = low.find(w)
        if i != -1:
            return text[i + len(w):].strip(" ,.!?-")
    return ""


def wake_loop() -> None:
    print("=" * 54)
    print("  Iris — wake-word mode  (say: 'Hey Iris …')")
    print("=" * 54)
    brain = Brain()
    print("  Calibrating the mic — stay quiet for a second…")
    threshold = calibrate()
    speak("Wake word active. Just say, hey Iris.")
    print(f"  Listening for 'Iris'…  (Ctrl+C to stop)   [threshold {threshold:.3f}]")

    while True:
        try:
            heard = transcribe(record_utterance(threshold))
            if not heard:
                continue
            if not any(w in heard.lower() for w in WAKE_WORDS):
                continue  # wasn't addressed to Iris — ignore

            cmd = _command_after_wake(heard)
            if len(cmd) < 2:          # they just said "Hey Iris" — ask for the command
                speak("Yes?")
                cmd = transcribe(record_utterance(threshold))
            if not cmd:
                continue

            print(f"  You: {cmd}")
            reply = brain.ask(cmd)
            print(f"  Iris: {reply}")
            speak(reply)
        except KeyboardInterrupt:
            print("\n  Wake word off. Talk soon.")
            break
        except Exception as exc:  # never die silently
            print(f"  (hiccup: {exc} — still listening)")
            continue
