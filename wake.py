"""
Iris — v0.2 wake word ("Hey Iris") + conversation mode. Always-listening, hands-free.

HARDENED for reliability (the listening side is the flaky part, not the brain/voice):
  • ONE persistent mic stream for the whole session (no open/close glitches).
  • ADAPTIVE noise floor — the trigger threshold tracks your room, so it doesn't
    miss you in a quiet room or fire on background noise.
  • NOISE GUARD — ignores blips that are too short/quiet (no answering to nothing).
  • She STOPS listening while she talks, then flushes the mic — so she never hears
    her own voice and false-triggers.
  • Never dies silently; Ctrl+C stops cleanly; API fires only on a real command.

Mic: set MIC_DEVICE (index or name) to use a specific mic. List them with
`python jarvis.py --mics`. Accuracy: set WHISPER_MODEL (small / small.en / medium).
"""

import collections
import os
import time

import numpy as np
import sounddevice as sd

from brain import Brain
from stt import transcribe
from tts import speak

SR = 16000
BLOCK = int(SR * 0.03)  # 30 ms
WAKE_WORDS = ("hey iris", "iris", "irises", "irish")
FOLLOWUP_SECONDS = 8

_MIC = os.environ.get("MIC_DEVICE")
if _MIC is not None and _MIC.strip().isdigit():
    _MIC = int(_MIC.strip())


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x))) + 1e-9)


def _flush(stream, secs: float = 0.25) -> None:
    """Discard whatever's buffered (e.g. the tail of Iris's own reply)."""
    for _ in range(int(secs / 0.03)):
        try:
            stream.read(BLOCK)
        except Exception:
            break


def _read_utterance(stream, thr_fn, wait_timeout=None,
                    max_sec=12.0, silence_sec=0.9, preroll_sec=0.35) -> np.ndarray:
    """Read from the live stream: wait for speech, capture until ~silence.
    Returns empty if it times out waiting, or if the clip is just noise."""
    pre = collections.deque(maxlen=max(1, int(preroll_sec / 0.03)))
    rec: list = []
    started = False
    silent = 0.0
    speech_frames = 0
    t_wait = time.time()
    t_rec = time.time()
    while True:
        data, _ = stream.read(BLOCK)
        block = np.asarray(data, dtype=np.float32).flatten()
        energy = _rms(block)
        thr = thr_fn(energy, started)
        if not started:
            pre.append(block)
            if energy > thr:
                started = True
                rec.extend(pre)
                rec.append(block)
                speech_frames = 1
                t_rec = time.time()
            elif wait_timeout is not None and (time.time() - t_wait) > wait_timeout:
                return np.zeros(0, dtype=np.float32)
        else:
            rec.append(block)
            if energy > thr:
                speech_frames += 1
                silent = 0.0
            else:
                silent += 0.03
            if silent >= silence_sec or (time.time() - t_rec) > max_sec:
                break
    if not rec:
        return np.zeros(0, dtype=np.float32)
    audio = np.concatenate(rec).flatten().astype(np.float32)
    # noise guard: need enough real speech, not a blip
    if len(audio) / SR < 0.35 or speech_frames < 8:
        return np.zeros(0, dtype=np.float32)
    return audio


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

    try:
        stream = sd.InputStream(samplerate=SR, channels=1, dtype="float32",
                                device=_MIC, blocksize=BLOCK)
        stream.start()
    except Exception as exc:
        print(f"  Could not open the mic: {exc}")
        print("  Tip: list mics with  python jarvis.py --mics  then set MIC_DEVICE in .env")
        return

    # Calibrate ambient noise from the live stream, then keep adapting it.
    amb = []
    for _ in range(int(1.0 / 0.03)):
        d, _ = stream.read(BLOCK)
        amb.append(_rms(np.asarray(d, dtype=np.float32).flatten()))
    noise = [max(0.004, float(np.median(amb)))]

    def thr_fn(energy: float, started: bool) -> float:
        if not started and energy < noise[0] * 1.5:      # adapt only during quiet
            noise[0] = 0.97 * noise[0] + 0.03 * energy
        return max(0.010, noise[0] * 3.2)

    speak("Wake word active. Just say, hey Iris.")
    print(f"  Listening for 'Hey Iris'…  (Ctrl+C to stop)   [noise {noise[0]:.4f}]")

    in_convo = False
    try:
        while True:
            try:
                if in_convo:
                    audio = _read_utterance(stream, thr_fn, wait_timeout=FOLLOWUP_SECONDS)
                    if len(audio) == 0:
                        in_convo = False
                        print("  … back to 'Hey Iris'.")
                        continue
                    cmd = transcribe(audio)
                else:
                    heard = transcribe(_read_utterance(stream, thr_fn))
                    if not heard or not any(w in heard.lower() for w in WAKE_WORDS):
                        continue
                    cmd = _command_after_wake(heard)
                    if len(cmd) < 2:
                        # stop mic while she prompts, then flush so she doesn't hear herself
                        stream.stop(); speak("Yes?"); stream.start(); _flush(stream)
                        cmd = transcribe(_read_utterance(stream, thr_fn, wait_timeout=FOLLOWUP_SECONDS))

                if not cmd:
                    in_convo = False
                    continue

                print(f"  You: {cmd}")
                reply = brain.ask(cmd)
                print(f"  Iris: {reply}")
                # stop listening while she speaks; flush her echo before follow-up
                stream.stop()
                speak(reply)
                stream.start()
                _flush(stream)
                in_convo = True
            except KeyboardInterrupt:
                raise
            except Exception as exc:  # never die silently
                print(f"  (hiccup: {exc} — still listening)")
                in_convo = False
                try:
                    if not stream.active:
                        stream.start()
                except Exception:
                    pass
                continue
    except KeyboardInterrupt:
        print("\n  Wake word off. Talk soon.")
    finally:
        try:
            stream.stop(); stream.close()
        except Exception:
            pass
