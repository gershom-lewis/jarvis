"""
JARVIS v0.1 — your voice AI Chief of Staff.

Talk to your AI instead of typing. Speech-to-text and text-to-speech run locally
(free); only the reasoning uses the Claude API (pennies, and only when you talk).

Run:  python jarvis.py
  • Press Enter, speak, press Enter again to send.
  • Or just type a message (great without a mic).
  • 'q' to quit.
"""

import sys

# Unattended/redirected consoles default to a legacy codepage; force UTF-8 so the
# status glyphs never crash the app.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from brain import Brain
from stt import record_until_enter, transcribe
from tts import speak


def main() -> int:
    print("=" * 54)
    print("  JARVIS — your voice Chief of Staff  (v0.1)")
    print("=" * 54)

    try:
        brain = Brain()
    except SystemExit as exc:
        print(f"  {exc}")
        return 1

    greeting = "Iris online and ready, Gershom. What do you need?"
    print(f"\nJARVIS: {greeting}")
    speak(greeting)

    while True:
        cmd = input("\n🎤 [Enter]=talk · type a message · 'q'=quit: ").strip()
        if cmd.lower() in ("q", "quit", "exit"):
            speak("Standing down. Talk soon.")
            break

        if cmd:
            text = cmd  # they typed
        else:
            print("🔴 Listening… press Enter when you're done speaking.")
            audio = record_until_enter()
            text = transcribe(audio)
            print(f"You: {text or '(didn’t catch that — try again)'}")

        if not text:
            continue

        reply = brain.ask(text)
        print(f"JARVIS: {reply}")
        speak(reply)

    return 0


if __name__ == "__main__":
    sys.exit(main())
