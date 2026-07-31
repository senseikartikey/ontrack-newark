# Landing Page Design Brief

OnTrack Newark's landing page is the piece that gets shown to people first — at meetups, at conferences, on a resume/portfolio link. It needs to read as belonging next to the best real SaaS landing pages (the caliber curated on `saaslandingpage.com` — think Linear, Vercel, Raycast, Attio), not a templated AI-generated site.

## Avoid (the "AI slop" tells)
- Purple-to-blue gradient blobs behind the hero, generic 3D-robot/neural-network stock icons, or stock photography.
- Default Inter-everywhere with no typographic personality; center-aligned everything.
- Cookie-cutter 3-icon feature grid with rounded gradient cards and no real content behind them.
- A generic "Trusted by" logo row with fake/placeholder logos.
- Vague marketing copy ("Revolutionize your commute with AI") instead of specific, honest claims.

## Do instead
- **Hero shows the real product, not an illustration.** Embed a live (or realistic) mini chart/ticker of actual Newark line reliability directly in the hero — a real data product's strongest asset is real data, on screen, immediately.
- **Dark-mode-first, developer/data-tool aesthetic** (Linear/Vercel/Raycast register): near-monochrome base palette, a single high-contrast accent color reused meaningfully — tie it to the product's own on-time-green/delay-red semantics rather than an arbitrary brand color.
- **Confident, specific typography**: one distinctive display face for headlines (not default system sans), tight tracking, strong size contrast between headline and body.
- **Scroll-driven "how it works"** (ingest → predict → display) as a real narrative section, not three static icons — e.g. a horizontally-scrolling or step-revealed sequence showing actual data moving through the pipeline.
- **A real, legible architecture diagram** (mermaid, styled to match the page theme) instead of a stock graphic.
- **Founder note styled like a devlog/terminal snippet**, not a generic "About the team" card — fits the personal international-student/AI-analyst story better than corporate boilerplate.
- Fully responsive, light/dark theme-aware, fast — no heavy unused animation libraries.

## Structure (rough section order)
1. Hero — tagline, one-line problem statement, live mini reliability stat/chart, primary CTA to the live dashboard, secondary CTA to GitHub.
2. The problem, stated specifically (not "commuting is hard" — the actual Newark–NYC delay pain point, in numbers once real data exists).
3. How it works — scroll-driven ingest → predict → display sequence.
4. Architecture diagram.
5. Founder note (devlog/terminal styled).
6. Footer with links.

Owned by `frontend-engineer-agent`; kept in sync by `docs-writer-agent` if the direction evolves. Don't change the direction unilaterally — check with Kartikey first, this is the piece he cares most about getting right.
