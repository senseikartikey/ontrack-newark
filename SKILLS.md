# SKILLS.md — Reusable Project Workflows

These are repeatable workflows for this project, implemented as real Claude Code skills in `.claude/skills/`. Invoke with `/deploy-check`, `/ingest-verify`, or `/demo-prep`.

## `deploy-check`
Runs before shipping anything to production. Lints and builds `/frontend`, runs `/backend` tests, checks `/ingestion` for syntax errors, and confirms `CLAUDE.md`/`AGENTS.md` haven't drifted from reality (e.g. a new directory or agent that isn't documented). Use it as the last step before a `devops-engineer-agent` deploy.

## `ingest-verify`
Sanity-checks the ingestion pipeline's latest data before a demo or before trusting the ML pipeline: row counts in the last N hours, freshness (is the poller actually running), and obvious gaps (a line with zero records). Use it any time the dashboard looks stale or before rehearsing a live demo.

## `demo-prep`
Spins up the stack locally (or confirms the deployed URLs are live), opens the landing page, and walks through the demo script from `docs/demo-script.md`. Use it the day before a meetup/conference talk, not the morning of.

## Adding a new skill
When a workflow gets repeated three times, promote it to a skill here rather than re-explaining it to an agent each time. Keep skills small and single-purpose — one workflow, one skill.
