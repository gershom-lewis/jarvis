"""
JARVIS — brain. Loads JARVIS's identity (SOUL/IDENTITY/USER, falling back to Big
Chief's), keeps the conversation in memory, and reasons with Claude.

The API key is read from jarvis/.env and never printed. Only spoken/typed text
crosses back and forth — never the key.
"""

import os
from datetime import datetime
from anthropic import Anthropic

from tools import TOOL_SCHEMAS, run_tool

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
        "You are Iris, Gershom's voice assistant — the spoken voice of his Eleven "
        "Bridges AI team. You run on the JARVIS system; your name is Iris (named "
        "for the Greek goddess of the rainbow bridge, fitting for Eleven Bridges). "
        "Chain of command: Gershom talks to YOU; you report to Big Chief, his AI "
        "Chief of Staff, who coordinates the whole team of specialist agents. You "
        "help Gershom directly and hand larger work to Big Chief and the team. "
        "You are being spoken OUT LOUD by a text-to-speech voice, so: keep replies "
        "SHORT and natural — 1 to 3 sentences unless he asks for detail. Never use "
        "markdown, bullet characters, asterisks, or emoji (they get read aloud and "
        "sound wrong). Be calm, competent, a little wry, and always honest — if you "
        "don't know or can't do something, say so plainly. You are the voice of his "
        "AI executive team; speak like a sharp chief of staff who has his back."
    )
    ctx_path = os.path.join(HERE, "context.md")
    context = ""
    if os.path.exists(ctx_path):
        try:
            context = open(ctx_path, encoding="utf-8").read()
        except Exception:
            context = ""

    parts = [base]
    if identity:
        parts.append("--- Your identity and who you serve ---\n" + identity)
    if context:
        parts.append("--- Gershom's live world (what's going on right now — know this) ---\n" + context)
    return "\n\n".join(parts)


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
            now = datetime.now().strftime("%A, %B %d, %Y, %I:%M %p")
        except Exception:
            now = ""
        dated_system = (
            f"Right now it is {now} (Gershom's local time). Use this whenever asked "
            "the date, day, or time — state it plainly, never guess.\n\n" + self.system
        )
        # Tool-use loop: she can search + read Gershom's docs before answering.
        for _ in range(4):  # bounded rounds
            try:
                msg = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    system=dated_system,
                    messages=self.history,
                    tools=TOOL_SCHEMAS,
                )
            except Exception as exc:
                return f"I hit a snag reaching my brain: {exc}"

            self.history.append({"role": "assistant", "content": msg.content})
            tool_uses = [b for b in msg.content if getattr(b, "type", None) == "tool_use"]
            if not tool_uses:
                return "".join(
                    b.text for b in msg.content if getattr(b, "type", None) == "text"
                ).strip()

            results = []
            for tu in tool_uses:
                out = run_tool(tu.name, tu.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": str(out)[:8000],
                })
            self.history.append({"role": "user", "content": results})

        return "I dug through your docs but couldn't pull that together cleanly — ask me a different way?"
