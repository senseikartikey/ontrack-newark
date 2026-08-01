# Landing Page Design Brief

OnTrack Newark's landing page is the piece that gets shown to people first — at meetups, at conferences, on a resume/portfolio link.

## Current direction (v4, as of 2026-08-01)

References: [zajno.com](https://zajno.com/) for overall studio polish, plus a specific methodology example (a prompt/brief for a fictional "Kestrel" analytics landing page) demonstrating: **one monumental image** (processed — halftone/dither/grain/linework — never raw stock photography), **technical marginalia** (coordinates, plate numbers, timestamps, IDs), **type at extremes** (monumental display or tiny mono labels, little in between), **near-monochrome ground with a single warm accent**. Explicit "never" list from that methodology: purple gradients, glossy 3D SaaS blobs, untextured stock photography, rounded-everything friendliness, icon-grid feature rows, Inter/system-font-only typography, evenly-distributed colorful palettes.

Concretely, on this page:
- **`--ink`** (`#0c0a08`, warm near-black, never pure `#000`) is the only background across every section — no more color-block sections (no lavender/rose).
- **`--signal`** (`#c9772e`, a warm amber) is the *one* accent — chosen because it evokes platform/signal lighting, not an arbitrary brand color. Used sparingly: step numbers, the live-status connected dot, hover states.
- **`HeroScene.tsx`**: the real monumental hero image, as of 2026-08-01 — see "Imagery" below for how it was sourced and processed.
- **Technical marginalia** in the hero: `PLATE II — TRANSIT LEDGER`, Newark Broad Street's real coordinates (matching the hero photo's actual location), `LIVE SINCE 2026-07-30` — small mono type, per the methodology's "type at extremes" rule.
- **`TopNav.tsx`**: flat, minimal — wordmark + one underlined text link. No floating pill (that was v3's device; it read as "friendly SaaS," which conflicts with this register).
- **`PipelineDiagram.tsx`**: a mono "ledger" list (numbered rows, hairline dividers) instead of colored cards — evokes the methodology's "transaction-ID chips" device without literally copying Direction 1's palette.
- **Wordmark divider**: outlined/ghost text (`-webkit-text-stroke`, transparent fill) rather than a solid color fill — reads as editorial/architectural rather than a bold brand moment, fitting the quieter register.
- **Per-line identity colors** (`lib/lineColors.ts`) are now **dashboard-only**. Showing 6 categorical colors on the landing page would violate "never evenly-distributed colorful palettes" — the landing page is a marketing/brand surface and stays near-monochrome; the dashboard is a utility surface where color-as-data-encoding is legitimate and stays.

### Imagery — real photo, properly licensed (2026-08-01)
Kartikey initially proposed an Alstom corporate press photo (from alstom.com marketing material) as the hero image. Flagged and declined: it's Alstom's copyrighted commercial photography with no license grant, and using a manufacturer's official press photo risked implying an Alstom/NJ Transit endorsement of this project that doesn't exist. Kartikey agreed to find a properly-licensed alternative instead.

Found on Wikimedia Commons: **[NJ Transit ALP-46 #4655 at Newark Broad Street](https://commons.wikimedia.org/wiki/File:ALP-46_NJT_4655_at_Newark_Broad_St.JPG)**, by Lexcie, licensed **CC BY-SA 3.0** — the actual Newark Broad Street clock tower is visible in frame, which is why the marginalia coordinates were corrected to that station (previously said Newark Penn). Original is a daytime shot; heavily desaturated, darkened, and warmed via CSS filters (`grayscale`/`sepia`/`contrast`/`brightness`) plus the page's existing grain texture to match the "processed, never raw" rule and the dark register — this counts as a derivative work, so attribution (photographer + license + link, per ShareAlike terms) is shown as a small credit in the hero's corner, not buried in a footnote. Downloaded, resized to 2400px wide and re-compressed (2.8MB → ~490KB) before committing, rather than serving the original file size.

If ever revisited: Kartikey's own phone photo of these lines would still be the more authentic option, and remains open for a future swap (same component, same treatment).

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
