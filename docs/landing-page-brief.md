# Landing Page Design Brief

OnTrack Newark's landing page is the piece that gets shown to people first — at meetups, at conferences, on a resume/portfolio link. It needs to read as belonging next to the best real SaaS landing pages (the caliber curated on `saaslandingpage.com` — think Linear, Vercel, Raycast, Attio), not a templated AI-generated site.

## Avoid (the "AI slop" tells)
- Purple-to-blue gradient blobs behind the hero, generic 3D-robot/neural-network stock icons, or stock photography.
- Default Inter-everywhere with no typographic personality; center-aligned everything.
- Cookie-cutter 3-icon feature grid with rounded gradient cards and no real content behind them.
- A generic "Trusted by" logo row with fake/placeholder logos.
- Vague marketing copy ("Revolutionize your commute with AI") instead of specific, honest claims.

## Do instead
- **Hero shows the real product, not a stock illustration.** But "real" doesn't mean flat or static — the first build (all-monochrome, one blue accent, zero motion, terminal box as the only hero visual) came back as boring, not restrained, and needed a real correction (2026-07-30). Real can be vivid: an animated, color-coded diagram of the actual Newark rail network (the lines, the two hub stations, small dots moving along each line) is *more* authentic than a plain data table, not less, and it's a far better hero visual than a flat panel.
- **Color is not the enemy of credibility.** Use the full categorical palette from the `dataviz` skill for line identity (each line keeps one fixed hue everywhere — hero map, dashboard pills, badges) — this is real information encoding, not decoration, so it earns its vividness. A slow-drifting multi-hue aurora glow behind the hero (blues/magentas/violets from the same palette, not an arbitrary purple blob) adds atmosphere without becoming generic, because it's built from the same system as everything else on the page.
- **Motion is expected, not optional.** Scroll-reveal on every section (fade + slide up), a staggered hero entrance, hover lift/glow on cards and buttons, and a continuously-animated hero visual. Respect `prefers-reduced-motion`, but the default experience should feel alive.
- **Confident, expressive typography**: a genuinely bold display face (Bricolage Grotesque, not a safe/subdued choice), large size contrast, and a gradient-text treatment on the hero's key phrase — pulled from the same categorical hues, so it reads as part of the same system rather than a bolted-on marketing gradient.
- **Dark-mode-first** (Linear/Vercel/Raycast register) is still the base register, but "dark-mode-first" was never meant to mean "colorless" — it's the surface the color and motion sit on top of.
- **Scroll-driven "how it works"** (ingest → predict → display) with per-step accent colors, not three identical gray cards.
- **A real, legible architecture diagram** instead of a stock graphic — now with a distinct accent color per pipeline stage.
- **Founder note styled like a devlog/terminal snippet**, not a generic "About the team" card — fits the personal international-student/AI-analyst story better than corporate boilerplate.
- Fully responsive, light/dark theme-aware.

## Still avoid, even with more color/motion
The correction above is not a license to drift back toward slop from the other direction — still no gradient blobs *unrelated* to the product's own palette, no stock icons, no decorative animation that doesn't tie to real content, no fake logos, no vague copy. The bar is "specific and authentic to this product," not "restrained." Both a boring gray page and a generic purple-blob-and-3D-icon page fail that bar the same way.

## Structure (rough section order)
1. Hero — tagline, one-line problem statement, live mini reliability stat/chart, primary CTA to the live dashboard, secondary CTA to GitHub.
2. The problem, stated specifically (not "commuting is hard" — the actual Newark–NYC delay pain point, in numbers once real data exists).
3. How it works — scroll-driven ingest → predict → display sequence.
4. Architecture diagram.
5. Founder note (devlog/terminal styled).
6. Footer with links.

Owned by `frontend-engineer-agent`; kept in sync by `docs-writer-agent` if the direction evolves. Don't change the direction unilaterally — check with Kartikey first, this is the piece he cares most about getting right.
