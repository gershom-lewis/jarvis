"""
Iris — v0.2 wake word ("Hey Iris") + conversation mode. Always-listening, hands-free.

HARDENED (automation-hardening standard, since the mic is always on):
  • The listen loop never dies silently — mic/transcription hiccups are caught
    and it keeps listening.
  • Ctrl+C stops it cleanly.
  • It only calls the Claude API when a wake word or an active follow-up fires,
    so cost stays controlled.
  • Foreground app you start/stop — nothing to persist across reboot.

Conversation mode: after Iris answers, she stays listening for a follow-up for a
few seconds (no wake word needed). If you go quiet, she drops back to waiting for
"Hey Iris".

Wake detection uses local Whisper (free, no keys). Swap in Picovoice Porcupine
later for lighter always-on CPU.
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
WAKE_WORDS = ("hey iris", "iris", "irises", "irish")  # tolerate common mis-hears
FOLLOWUP_SECONDS = 8  # how long she keeps listening after an answer


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x))) + 1e-9)


def calibrate(seconds: float = 1.0) -> float:
    frames = []
    with sd.InputStream(samplerate=SR, channels=1, dtype="float32") as s:
        for _ in range(int(seconds / 0.03)):
            data, _ = s.read(BLOCK)
            frames.append(data.copy())
    ambient = _rms(np.concatenate(frames).flatten())
    return max(0.014, ambient * 3.0)


def record_utterance(threshold: float, max_sec: float = 9.0, silence_sec: float = 0.8,
                     preroll_sec: float = 0.3, wait_timeout=None) -> np.ndarray:
    """Wait for speech, record until ~silence, return the audio. If wait_timeout is
    set and no speech starts within it, return an empty array."""
    pre = collections.deque(maxlen=max(1, int(preroll_sec / 0.03)))
    rec: list = []
    started = False
    silent = 0.0
    t_wait = time.time()
    t_rec = time.time()
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
                    t_rec = time.time()
                elif wait_timeout is not None and (time.time() - t_wait) > wait_timeout:
                    return np.zeros(0, dtype=np.float32)
            else:
                rec.append(block)
                silent = silent + 0.03 if energy < threshold else 0.0
                if silent >= silence_sec or (time.time() - t_rec) > max_sec:
                    break
    if not rec:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(rec).flatten().astype(np.float32)


def _command_after_wake(text: str) -> str:
    low = text.lower()
    for w in ("hey iris", "iris"):
        i = low.find(w)
        if i != -1:
            return text[i + len(w):].strip(" ,.!?-")
    return ""


def wake_loop() -> None:
    print("=" * 54)
    print("  Iris — wake word + conversation mode")
    print("=" * 54)
    brain = Brain()
    print("  Calibrating the mic — stay quiet for a second…")
    threshold = calibrate()
    speak("Wake word active. Just say, hey Iris.")
    print(f"  Listening for 'Hey Iris'…  (Ctrl+C to stop)   [threshold {threshold:.3f}]")

    in_convo = False
    while True:
        try:
            if in_convo:
                # follow-up window: listen for a command WITHOUT the wake word
                audio = record_utterance(threshold, wait_timeout=FOLLOWUP_SECONDS)
                if len(audio) == 0:
                    in_convo = False
                    print("  … back to 'Hey Iris'.")
                    continue
                cmd = transcribe(audio)
            else:
                heard = transcribe(record_utterance(threshold))
                if not heard or not any(w in heard.lower() for w in WAKE_WORDS):
                    continue  # not addressed to Iris
                cmd = _command_after_wake(heard)
                if len(cmd) < 2:          # they only said "Hey Iris"
                    speak("Yes?")
                    cmd = transcribe(record_utterance(threshold, wait_timeout=FOLLOWUP_SECONDS))

            if not cmd:
                in_convo = False
                continue

            print(f"  You: {cmd}")
            reply = brain.ask(cmd)
            print(f"  Iris: {reply}")
            speak(reply)
            in_convo = True  # stay open for a natural follow-up
        except KeyboardInterrupt:
            print("\n  Wake word off. Talk soon.")
            break
        except Exception as exc:  # never die silently
            print(f"  (hiccup: {exc} — still listening)")
            in_convo = False
            continue
