# Landing Page Design Brief

OnTrack Newark's landing page is the piece that gets shown to people first — at meetups, at conferences, on a resume/portfolio link.

## Current direction (v4, as of 2026-08-01)

References: [zajno.com](https://zajno.com/) for overall studio polish, plus a specific methodology example (a prompt/brief for a fictional "Kestrel" analytics landing page) demonstrating: **one monumental image** (processed — halftone/dither/grain/linework — never raw stock photography), **technical marginalia** (coordinates, plate numbers, timestamps, IDs), **type at extremes** (monumental display or tiny mono labels, little in between), **near-monochrome ground with a single warm accent**. Explicit "never" list from that methodology: purple gradients, glossy 3D SaaS blobs, untextured stock photography, rounded-everything friendliness, icon-grid feature rows, Inter/system-font-only typography, evenly-distributed colorful palettes.

Concretely, on this page:
- **`--ink`** (`#0c0a08`, warm near-black, never pure `#000`) is the only background across every section — no more color-block sections (no lavender/rose).
- **`--signal`** (`#c9772e`, a warm amber) is the *one* accent — chosen because it evokes platform/signal lighting, not an arbitrary brand color. Used sparingly: step numbers, the live-status connected dot, hover states.
- **`HeroScene.tsx`**: a crafted CSS/SVG stand-in for the monumental hero image — a dark vignette, one warm glow (a distant signal light), and faint converging lines suggesting rail perspective receding into the dark. This is **not** a final asset — see "Imagery" below.
- **Technical marginalia** in the hero: `PLATE II — TRANSIT LEDGER`, real Newark Penn Station coordinates, `LIVE SINCE 2026-07-30` — small mono type, per the methodology's "type at extremes" rule.
- **`TopNav.tsx`**: flat, minimal — wordmark + one underlined text link. No floating pill (that was v3's device; it read as "friendly SaaS," which conflicts with this register).
- **`PipelineDiagram.tsx`**: a mono "ledger" list (numbered rows, hairline dividers) instead of colored cards — evokes the methodology's "transaction-ID chips" device without literally copying Direction 1's palette.
- **Wordmark divider**: outlined/ghost text (`-webkit-text-stroke`, transparent fill) rather than a solid color fill — reads as editorial/architectural rather than a bold brand moment, fitting the quieter register.
- **Per-line identity colors** (`lib/lineColors.ts`) are now **dashboard-only**. Showing 6 categorical colors on the landing page would violate "never evenly-distributed colorful palettes" — the landing page is a marketing/brand surface and stays near-monochrome; the dashboard is a utility surface where color-as-data-encoding is legitimate and stays.

### Imagery — explicitly deferred, not faked
Per the methodology's own instruction ("do NOT generate or source any imagery... reserve the hero slot... fill it with a flat CSS stand-in... so the real image drops in with zero layout changes"): no photo was generated or sourced for this page. `HeroScene.tsx` is sized and positioned exactly where a real image will go. Two real paths forward, in order of preference:
1. **Kartikey's own photo** of a Newark platform/train, ideally moody/dusk/night — most authentic, zero licensing concern, fits the founder-note "I ride these lines" story directly.
2. **AI-generated**, once the Higgsfield MCP (`.mcp.json`) is actually connected and approved.
Do not substitute a scraped/stock photo without an explicit license check — copyright risk on a public repo.

## Design history
1. **v1 (2026-07-30, restrained)**: near-monochrome, one blue accent, zero animation, terminal-box-only hero. Read as boring — conflated "avoid AI slop" with "stay minimal."
2. **v2 (2026-07-30, color + motion)**: full categorical palette, animated SVG rail-line map, aurora glow, scroll-driven motion. Still read as a developer-tool page, not a designed brand page.
3. **v3 (2026-07-31, illustrated creative-agency)**: full pivot per a Zajno Dribbble reference — film grain, lavender/rose color blocks, hand-built flat silhouette illustration, floating pill nav. Better received, but still not quite it.
4. **v4 (2026-08-01, current — dark/mysterious/monumental)**: per a second, more specific reference (zajno.com plus the Kestrel methodology example) — dropped the color blocks and illustration entirely in favor of near-monochrome + single accent, one monumental (crafted, not illustrated) hero scene, and technical marginalia. Compounding lesson across all four: a concrete visual reference (an actual screenshot/site) converges much faster than a verbal style description, and "good taste" here has turned out to mean *restraint in palette, extremity in typography* — the opposite axis from where v1's mistake was (v1 was restrained in the wrong dimension: motion and imagery, not palette).

## Structure (current section order)
1. Top nav (flat, absolute over hero).
2. Hero — `HeroScene` background, marginalia block, monumental headline, bordered CTA + text link, live status panel.
3. The problem — one honest, specific claim.
4. How it works — 3 steps (mono number + monumental short title) + the pipeline ledger list.
5. Wordmark divider — outlined "ontrack".
6. Founder note — terminal-styled card.
7. Footer.

Owned by `frontend-engineer-agent`; kept in sync by `docs-writer-agent` if the direction evolves. Don't change the direction unilaterally — check with Kartikey first, this is the piece he cares most about getting right.
