/**
 * Per-line color identity, using the `dataviz` skill's validated categorical palette
 * (dark-mode steps). Slots 6 (green) and 8 (red) are deliberately skipped -- they sit
 * too close to the status palette's good/critical hues (on-time/delayed), and a line's
 * identity color must never be mistaken for a delay status. This is categorical
 * encoding, not decoration: each Newark-area line keeps one fixed hue everywhere it
 * appears (landing page rail map, dashboard pills, line badges).
 */
export const LINE_COLORS: Record<string, string> = {
  NEC: "#3987e5", // slot 1: blue
  NJCL: "#d95926", // slot 2: orange
  NJCLL: "#d95926", // same physical line as NJCL
  RARV: "#199e70", // slot 3: aqua
  BNTN: "#c98500", // slot 4: yellow
  BNTNM: "#c98500", // same physical line as BNTN
  MNE: "#d55181", // slot 5: magenta
  MNEG: "#9085e9", // slot 7: violet
};

export function colorForLine(code: string): string {
  return LINE_COLORS[code] ?? "#898781";
}
