# Engineering Log

Running, dated history of what was built and what was learned. Newest entry on top. One entry per meaningful unit of work — especially anything that broke.

**Entry format:**
```
## YYYY-MM-DD — <short title>
**Agent**: <which subagent, or "pm"/"kartikey">
**Did**: <what was built/changed>
**Issue**: <what broke, if anything — omit if nothing broke>
**Root cause**: <why it broke>
**Fix**: <what resolved it>
**Lesson**: <what to do differently next time — this is the part worth keeping>
```

---

## 2026-07-30 — Repo scaffold (Day 0)
**Agent**: pm-agent
**Did**: Created the `ontrack-newark` repo structure (`/ingestion`, `/backend`, `/ml`, `/frontend`, `/infra`), wrote `CLAUDE.md`, `AGENTS.md`, `SKILLS.md`, this log, the 8 `.claude/agents/*.md` subagent definitions, and the 3 `.claude/skills/*` workflows (`deploy-check`, `ingest-verify`, `demo-prep`). No feature code yet.
**Lesson**: Setting up the org/tooling scaffold before any feature work means every subsequent agent invocation has a stable place to get context from (`CLAUDE.md` + `AGENTS.md`) instead of re-deriving project structure each time. Worth the up-front time given agents start cold on every call.
