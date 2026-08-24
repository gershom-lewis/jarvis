"""
Iris — read-only knowledge tools. Lets her search and read Gershom's project
docs/code/brain so she can actually speak to any project (not just her memo).

GOVERNED (per the RBAC / SEEC model):
  • READ-ONLY. No writes, no actions.
  • SCOPED — only the allowed project roots below.
  • Secrets & client data BLOCKED — never reads .env / keys / credentials, and
    skips generated/report/client folders.
Free: plain local file search, no embeddings / vector DB.
"""

import os

ALLOWED_ROOTS = [
    r"C:\Users\gersh\OneDrive\Desktop\Eleven Bridges Business Docs",
    r"C:\Users\gersh\OneDrive\Desktop\Client Delivery Playbook",
    r"C:\Users\gersh\.claude\brain",
    r"C:\Users\gersh\guardian",
    r"C:\Users\gersh\agent-readiness",
    r"C:\Users\gersh\vannah",
    r"C:\Users\gersh\python-bridge",
    r"C:\Users\gersh\jarvis",
]
TEXT_EXT = (".md", ".html", ".txt", ".py", ".js", ".ts", ".json")
SECRET_HINTS = (".env", "secret", "credential", "apikey", "api_key", ".key", ".pem",
                "token", "password", ".ppk")
SKIP_DIRS = {"node_modules", ".git", "__pycache__", "reports", "businesses",
             ".venv", "venv", "dist", "build", "filed", "inbox"}
_ROOTS_ABS = [os.path.abspath(r) for r in ALLOWED_ROOTS]


def _blocked(path: str) -> bool:
    base = os.path.basename(path).lower()
    return any(h in base for h in SECRET_HINTS)


def _allowed(path: str) -> bool:
    ap = os.path.abspath(path)
    return any(ap.startswith(r) for r in _ROOTS_ABS) and not _blocked(ap)


def search_docs(query: str, max_results: int = 6) -> str:
    terms = [t for t in query.lower().split() if len(t) > 2] or [query.lower().strip()]
    hits = []
    scanned = 0
    for root in ALLOWED_ROOTS:
        if not os.path.isdir(root):
            continue
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if d.lower() not in SKIP_DIRS]
            for fn in fns:
                if not fn.lower().endswith(TEXT_EXT):
                    continue
                path = os.path.join(dp, fn)
                if _blocked(path):
                    continue
                scanned += 1
                if scanned > 1500:
                    break
                try:
                    txt = open(path, encoding="utf-8", errors="ignore").read()
                except Exception:
                    continue
                low = txt.lower()
                name_score = sum(3 for t in terms if t in fn.lower())
                content_score = sum(low.count(t) for t in terms)
                score = name_score * 10 + content_score
                if score > 0:
                    idx = -1
                    for t in terms:
                        j = low.find(t)
                        if j != -1:
                            idx = j
                            break
                    snip = ""
                    if idx != -1:
                        s = max(0, idx - 100)
                        snip = " ".join(txt[s:s + 260].split())
                    hits.append((score, path, snip))
    if not hits:
        return "No matching docs found. Try different keywords."
    hits.sort(reverse=True)
    lines = [f"- {p}\n  …{snip}…" for _s, p, snip in hits[:max_results]]
    return "Top matches (use read_doc on a path for the full text):\n" + "\n".join(lines)


def read_doc(path: str, max_chars: int = 6000) -> str:
    if not _allowed(path):
        return "Access denied — that path is outside Gershom's project docs, or looks like a secret."
    if not os.path.isfile(path):
        return f"Not found: {path}"
    try:
        txt = open(path, encoding="utf-8", errors="ignore").read()
    except Exception as exc:
        return f"Could not read it: {exc}"
    if len(txt) > max_chars:
        txt = txt[:max_chars] + "\n…(truncated)…"
    return txt


def run_tool(name: str, args: dict) -> str:
    try:
        if name == "search_docs":
            return search_docs(str(args.get("query", "")))
        if name == "read_doc":
            return read_doc(str(args.get("path", "")))
    except Exception as exc:
        return f"Tool error: {exc}"
    return f"Unknown tool: {name}"


# Anthropic tool schemas
TOOL_SCHEMAS = [
    {
        "name": "search_docs",
        "description": ("Search Gershom's project docs, code, and brain for a topic. "
                        "Use this whenever he asks about the status or details of ANY "
                        "project (Guardian, Vannah, Savannah, the dashboard, SEEC, a doc, "
                        "etc.). Returns matching file paths + snippets."),
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "keywords to search for"}},
            "required": ["query"],
        },
    },
    {
        "name": "read_doc",
        "description": ("Read the full text of one of Gershom's files by its path (use a "
                        "path returned by search_docs). Do this to get the details before "
                        "you answer."),
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "the file path to read"}},
            "required": ["path"],
        },
    },
]
