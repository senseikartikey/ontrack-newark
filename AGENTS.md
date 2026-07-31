# AGENTS.md — Engineering Org Chart

OnTrack Newark is built by a small team of specialized Claude Code subagents instead of one generalist handling every layer shallowly. Each agent owns one directory/department, so quality stays high per domain. Kartikey acts as engineering lead and delegates work to the right specialist via the `Agent` tool, providing full context each time — subagents start every invocation cold, with no memory of prior sessions, so the brief must be self-contained (point them at `CLAUDE.md`, this file, and the relevant part of `ENGINEERING_LOG.md`).

Agent definitions live in `.claude/agents/*.md`.

**Known limitation (2026-07-30):** in the session that authored these files, the `Agent` tool did not recognize any of these custom subagent names (`Agent type '...' not found. Available agents: claude, claude-code-guide, Explore, general-purpose, Plan, statusline-setup`) — only a fixed built-in list was invokable. If you're picking this up in a new session, check whether `subagent_type: "data-engineer-agent"` (etc.) actually resolves before assuming real delegation is happening. If it still doesn't, work through each department's brief directly (as self-instruction) and say so plainly in `ENGINEERING_LOG.md` rather than implying a separate agent ran it — that's what happened for all Week 1/Week 2 work in this repo so far.

## The team

### `pm-agent`
**Owns**: root docs (`CLAUDE.md`, `AGENTS.md`, `SKILLS.md`, `ENGINEERING_LOG.md`).
**Responsibility**: breaks the roadmap into concrete tasks, decides which specialist handles what, keeps the four root docs accurate as the project evolves, and is the default agent to invoke when it's unclear who owns a piece of work.
**Invoke when**: starting a new week of the build sequence, or when work spans multiple agents and needs sequencing.

### `data-engineer-agent`
**Owns**: `/ingestion`.
**Responsibility**: GTFS-RT poller (vehicle positions, trip updates, service alerts), static GTFS loader, weather fetcher, DB schema/migrations, Supabase setup.
**Invoke when**: touching data collection, the DB schema, or anything upstream of the API.

### `backend-engineer-agent`
**Owns**: `/backend`.
**Responsibility**: FastAPI app — routers, prediction-serving endpoints, response caching. Reads from Postgres and from precomputed ML outputs; never talks to external APIs directly (that's ingestion's job).
**Invoke when**: adding/changing an API endpoint or backend business logic.

### `ml-engineer-agent`
**Owns**: `/ml`.
**Responsibility**: feature engineering, the v1 statistical baseline, the v2 LightGBM/XGBoost model, and honest evaluation (MAE vs baseline) written up for the README.
**Invoke when**: working on prediction quality, retraining, or evaluation.

### `frontend-engineer-agent`
**Owns**: `/frontend`.
**Responsibility**: the Next.js dashboard *and* the public landing page. Landing page must meet the design brief in the plan (no AI-slop clichés — see `docs/landing-page-brief.md`). Uses the `dataviz` and `artifact-design` skills for chart/visual quality.
**Invoke when**: any UI work, including the landing page.

### `devops-engineer-agent`
**Owns**: `/infra`.
**Responsibility**: GitHub Actions workflows (scheduled ingestion polling), Render/Vercel/Supabase configuration, deployment, secrets management guidance.
**Invoke when**: deploying, changing hosting config, or setting up scheduled jobs.

### `qa-engineer-agent`
**Owns**: cross-cutting (no single directory).
**Responsibility**: writes/runs tests for each layer, verifies end-to-end flows against the plan's Verification section, files bugs as `ENGINEERING_LOG.md` entries with root cause once diagnosed.
**Invoke when**: before a deploy, after a feature is "done" per its owning agent, or when something's misbehaving and needs triage.

### `docs-writer-agent`
**Owns**: `README.md`, `/docs` (diagrams, demo materials).
**Responsibility**: architecture diagrams (mermaid), the conference/meetup demo script and one-pager, keeping docs in sync with what actually got built.
**Invoke when**: wrapping up a milestone, or prepping for a demo.

## Collaboration protocol

1. **One directory, one owner.** If a task needs changes in two directories (e.g. a new API field the frontend needs to render), split it into two invocations — one per owning agent — rather than letting either agent edit outside its lane.
2. **Cold start every time.** Each `Agent` call briefs the subagent from scratch: what's being built, why, relevant file paths, and any constraint from `CLAUDE.md`/this file/the plan. Don't assume a subagent remembers a previous invocation unless you're resuming the same one via `SendMessage`.
3. **Log after, not instead of, doing.** After a meaningful unit of work lands, append an entry to `ENGINEERING_LOG.md` (date, agent, what changed, any issue + root cause + fix + lesson). This is what makes the next cold-start cheap.
4. **`pm-agent` is the tie-breaker.** If it's unclear who owns something or how to sequence dependent work, that's `pm-agent`'s job, not a guess.
