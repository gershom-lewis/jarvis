# Your GitHub Portfolio — Explained (Q&A)

> Plain-English answers to the three questions every founder asks about putting
> code on GitHub — plus a cheat-sheet for describing these repos to a client or a
> hiring manager. Filed here so it lives with the work it describes.

---

## The 30-second cheat sheet — what to say

**Umbrella line:**
> "I build read-only, governed AI tools that assess and assist small businesses —
> and the code's public, you can look."

**The repos, one line each** ([github.com/gershom-lewis](https://github.com/gershom-lewis)):

| Repo | Say this |
|------|----------|
| **guardian** | "A read-only AI network-security auditor — scans a network, scores it, reports what's exposed, and never changes anything." |
| **agent-readiness** | "Scores how *AI-ready* a business is — what AI says about them when a buyer asks — and hands them a report." |
| **vannah-concierge** | "An AI website concierge on Cloudflare's edge — chats with visitors, captures leads, key stays server-side." |
| **python-bridge** | "Email triage with Claude — sorts mail into reply / escalate / stop." |
| **jarvis** | "A voice AI assistant you talk to — local speech in and out, a Claude brain, and read-only tools so it knows the business — all governed." |

---

## Q1 — How do I describe these tools when I talk about them?

Use the one-liners above. The pattern for each: **what it does → who it's for →
the governance line** ("read-only," "key stays server-side," "never changes
anything"). That governance phrase is the differentiator. For depth, walk through
**one** repo's README — start with **guardian**, it's the most complete.

## Q2 — Can people see and copy the code?

**Yes — and that's the point of a portfolio.** A public repo can be viewed and
copied (the MIT license permits reuse). What can't be copied: the **secrets**
(`.env`, keys, private context — all git-ignored and never pushed), the data,
the clients, the deployment, or the person who builds and governs it. Proprietary
client work goes in a **private** repo; portfolio pieces stay public.

## Q3 — When the agent improves, do the updates go up?

**Yes — automatically, with full history.** Every `commit` + `push` lands as a
new version with a changelog. GitHub keeps every version; you can diff and roll
back anytime.

---

*Why it matters: open code is a credibility engine — a copyable skeleton, but the
value (the builder + governance + clients + deployment) stays yours.*
