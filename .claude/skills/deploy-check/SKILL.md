---
name: deploy-check
description: Pre-deploy sanity check across all layers of OnTrack Newark (lint/build frontend, test backend, check ingestion, verify docs haven't drifted). Use before any devops-engineer-agent deploy.
---

# deploy-check

Run before shipping any change to production. Go through each step; stop and report if any step fails rather than deploying anyway.

1. **Frontend** (`/frontend`): run the lint script and a production build (`npm run lint`, `npm run build` or equivalent once the app is scaffolded). A build failure blocks deploy.
2. **Backend** (`/backend`): run the test suite (`pytest` once scaffolded). Also import the FastAPI app to catch startup errors early.
3. **Ingestion** (`/ingestion`): run a syntax/import check on the poller scripts; if a test suite exists, run it.
4. **Docs drift check**: confirm every top-level directory (`/ingestion`, `/backend`, `/ml`, `/frontend`, `/infra`) is still listed correctly in `CLAUDE.md`'s directory map and that every agent referenced in `AGENTS.md` still has a matching file in `.claude/agents/`. If a directory or agent was added/removed without updating these docs, flag it and fix before deploying.
5. **Secrets check**: confirm no `.env` file or literal API key/connection string is staged for commit (`git status` + a quick scan of the diff).

Report a short pass/fail summary per step. Only proceed to deploy once all steps pass.
