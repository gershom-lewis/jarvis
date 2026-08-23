"""
JARVIS — brain. Loads JARVIS's identity (SOUL/IDENTITY/USER, falling back to Big
Chief's), keeps the conversation in memory, and reasons with Claude.

The API key is read from jarvis/.env and never printed. Only spoken/typed text
crosses back and forth — never the key.
"""

import os
from anthropic import Anthropic

HERE = os.path.dirname(os.path.abspath(__file__))
JARVIS_ID = r"C:\Users\gersh\.claude\brain\executive-team\jarvis\identity-files"
BIGCHIEF_ID = r"C:\Users\gersh\.claude\brain\executive-team\big-chief\identity-files"


def load_env(path: str = os.path.join(HERE, ".env")) -> dict:
    values: dict = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8-sig"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                values[k.strip()] = v.strip().strip('"').strip("'")
    return values


def _read_identity(folder: str) -> str:
    parts = []
    if os.path.isdir(folder):
        for name in ("SOUL.md", "IDENTITY.md", "USER.md"):
            p = os.path.join(folder, name)
            if os.path.exists(p):
                parts.append(open(p, encoding="utf-8").read())
    return "\n\n".join(parts)


def build_system() -> str:
    identity = _read_identity(JARVIS_ID) or _read_identity(BIGCHIEF_ID)
    base = (
        "You are Iris, Gershom's voice AI Chief of Staff for Eleven Bridges — you "
        "run on the JARVIS system, but your name is Iris (named for the Greek "
        "goddess of the rainbow bridge, fitting for Eleven Bridges). "
        "You are being spoken OUT LOUD by a text-to-speech voice, so: keep replies "
        "SHORT and natural — 1 to 3 sentences unless he asks for detail. Never use "
        "markdown, bullet characters, asterisks, or emoji (they get read aloud and "
        "sound wrong). Be calm, competent, a little wry, and always honest — if you "
        "don't know or can't do something, say so plainly. You are the voice of his "
        "AI executive team; speak like a sharp chief of staff who has his back."
    )
    if identity:
        return base + "\n\n--- Your identity and who you serve ---\n" + identity
    return base


class Brain:
    def __init__(self):
        env = load_env()
        key = env.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise SystemExit("No ANTHROPIC_API_KEY found — add it to jarvis/.env")
        self.client = Anthropic(api_key=key)
        self.model = env.get("MODEL", "claude-haiku-4-5")
        self.system = build_system()
        self.history: list = []

    def ask(self, text: str) -> str:
        self.history.append({"role": "user", "content": text})
        try:
            msg = self.client.messages.create(
                model=self.model,
                max_tokens=400,
                system=self.system,
                messages=self.history[-12:],  # last few turns of context
            )
        except Exception as exc:
            self.history.pop()  # don't keep the failed turn
            return f"I hit a snag reaching my brain: {exc}"
        reply = "".join(
            b.text for b in msg.content if getattr(b, "type", None) == "text"
        ).strip()
        self.history.append({"role": "assistant", "content": reply})
        return reply
