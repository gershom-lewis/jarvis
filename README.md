# 🎙️ JARVIS — a voice AI Chief of Staff

Talk to your AI instead of typing. JARVIS listens, reasons with Claude, and
answers **out loud** — a personal, movie-style voice assistant that actually
*thinks*, not a scripted command bot.

Built by [Eleven Bridges AI LLC](https://elevenbridges.com).

## Why it's different
Siri and Alexa run scripted commands. JARVIS puts a real **reasoning brain**
behind the voice, and runs its ears and mouth **locally** — so it's smarter than
the walled-garden assistants and costs pennies to run.

| Piece | Tech | Cost |
|-------|------|------|
| 👂 Ears (speech→text) | faster-whisper, on-device | **$0** — audio never leaves the machine |
| 🧠 Brain | Claude (Anthropic API), loaded with a Chief-of-Staff identity | pennies, only when you talk |
| 🔊 Mouth (text→speech) | Windows voice (pyttsx3 / SAPI5) | **$0** — no per-minute fees |

## Run it
```bash
pip install -r requirements.txt
cp .env.example .env        # add your ANTHROPIC_API_KEY
python jarvis.py
```
- Press **Enter**, speak, press **Enter** again to send.
- Or just **type** a message (works great without a mic).
- **`q`** to quit.

## Architecture
```
jarvis.py   the loop: capture → transcribe → reason → speak
stt.py      push-to-talk mic capture + local Whisper transcription
brain.py    loads JARVIS's identity (SOUL/IDENTITY/USER) + Claude conversation
tts.py      local text-to-speech
```
JARVIS speaks with a short, natural, no-markdown voice because it's read aloud;
its persona and knowledge come from a three-file identity (calm, competent, wry,
always honest).

## Design principles
- **Local-first + private.** STT and TTS run on-device; audio never leaves the machine.
- **Secrets stay in `.env`** (git-ignored) — never printed, never spoken.
- **Honest by rule.** It says "I don't know" rather than bluff, and confirms before anything irreversible.

## Roadmap
- **v0.2** — wake word ("Hey JARVIS"), always-listening (→ hardening gate).
- **v0.3** — a premium voice (ElevenLabs), barge-in.
- **v0.4** — route requests to the executive-team sub-agents; take approved actions.

## License
MIT
