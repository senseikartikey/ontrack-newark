# Landing Page Design Brief

OnTrack Newark's landing page is the piece that gets shown to people first — at meetups, at conferences, on a resume/portfolio link.

## Current direction (as of 2026-07-31)

Reference: [Web design for SAS Design Studio, by Władysław for Zajno](https://dribbble.com/shots/24257855-Web-design-for-SAS-Design-Studio) — an illustrated creative-agency register, not a minimal dev-tool one. Concretely:

- **Tinted-ink dark sections** (`--ink`, a near-black with a violet undertone — never pure `#000`, per the `impeccable` skill's rule) alternating with bold pastel color-block sections (`--lavender`, `--rose`).
- **Film grain texture** (`.grain` utility in `globals.css`, an SVG fractal-noise tile) over every section — this is what keeps flat color blocks from reading as generic/flat-slop.
- **A hand-built flat silhouette illustration** as the primary hero-adjacent visual (`components/StationIllustration.tsx`) — a train arriving at a Newark platform, radiating sunburst arcs, soft cloud shapes, sparkle accents — depicting the actual product subject, not an abstract shape. Built by hand from SVG primitives because no image-generation tool was connected when this was built; if the Higgsfield MCP (`.mcp.json`) gets connected in a future session, revisit whether a generated illustration in this same style should replace it.
- **A floating pill nav** (`components/PillNav.tsx`), fixed top-center, rounded-full, dark, with a rose CTA pill.
- **An oversized lowercase wordmark divider** section (`wordmark` utility class) — the "ontrack" full-bleed moment, echoing the reference's own wordmark section.
- **Real per-line identity color** (`lib/lineColors.ts`, from the `dataviz` skill's categorical palette) still carried through the hero line-code legend, the "how it works" step accents, the pipeline diagram, and the dashboard's line pills — the one piece of the earlier direction that stays, because it's genuine data encoding, not decoration.
- **Motion throughout**: staggered hero entrance, scroll-reveal per section, scroll-linked parallax on the illustration, hover interactions — via the `motion` (Framer Motion) library.
- Bold display type: Bricolage Grotesque, set lowercase for the wordmark treatment.

### Rules borrowed from `impeccable` and `taste-skill` (applied by hand, not installed)
- Tint blacks/grays — `--ink` has a violet undertone, never `#000`/`#111` flat gray.
- Never gray text on a colored background — founder-note text on the rose section sits inside a dark `--ink` card, not directly on rose.
- No bounce/elastic easing — all transitions use `easeOut` or spring with high damping.
- Push the "taste dials" high for this page: DESIGN_VARIANCE and MOTION_INTENSITY both high (asymmetric-enough layout, real scroll/parallax motion), VISUAL_DENSITY moderate (this is a landing page, not a dashboard).

## Design history (why it looks like this)
1. **v1 (2026-07-30, restrained)**: near-monochrome, one blue accent, zero animation, terminal-box-only hero visual. Came back as boring/generic — the brief had conflated "avoid AI slop" with "stay minimal."
2. **v2 (2026-07-30, color + motion added)**: kept the dev-tool register but added a full categorical palette, an animated SVG rail-line map, aurora background glow, motion-driven scroll reveals. Better, but still read as a developer-tool page, not a designed brand page.
3. **v3 (2026-07-31, current)**: full pivot to the illustrated creative-agency register above, after the user pointed to a specific Dribbble reference. The lesson compounding across v1→v3: "good taste" here means specific, textured, and confidently designed — not restrained, and not generic either register.

## Structure (current section order)
1. Pill nav (fixed).
2. Hero — ink + grain, oversized lowercase headline, rose accent line, CTA, line-code legend, live status panel.
3. Illustration block — lavender + grain, the station illustration, scroll-parallax.
4. The problem — ink + grain, one honest specific claim.
5. How it works — ink + grain, 3 accent-colored steps + pipeline diagram.
6. Big wordmark divider — ink + grain, "ontrack" in lavender.
7. Founder note — rose + grain, dark terminal-styled card.
8. Footer — ink + grain.

Owned by `frontend-engineer-agent`; kept in sync by `docs-writer-agent` if the direction evolves. Don't change the direction unilaterally — check with Kartikey first, this is the piece he cares most about getting right.
