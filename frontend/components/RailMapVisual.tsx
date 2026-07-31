import { LINE_COLORS } from "@/lib/lineColors";

/**
 * A stylized (not geographically literal) diagram of the Newark-area rail network --
 * the two hub stations with each line radiating out, color-coded per lib/lineColors.
 * Train dots animate continuously along each path via native SVG <animateMotion>, so
 * it's alive even with JavaScript disabled. This is the hero's real visual anchor:
 * an authentic representation of the actual product, not stock art.
 */
const LINES = [
  { code: "NEC", path: "M 260 250 C 340 200, 420 140, 520 90", label: "NEC" },
  { code: "NJCL", path: "M 260 250 C 330 300, 410 340, 500 400", label: "NJCL" },
  { code: "RARV", path: "M 260 250 C 190 300, 120 340, 40 400", label: "RARV" },
  { code: "BNTN", path: "M 420 190 C 470 140, 520 100, 580 60", label: "BNTN" },
  { code: "MNE", path: "M 420 190 C 480 230, 550 260, 620 300", label: "MNE" },
  { code: "MNEG", path: "M 420 190 C 360 140, 300 100, 240 50", label: "MNEG" },
];

export default function RailMapVisual() {
  return (
    <svg
      viewBox="0 0 680 460"
      className="w-full h-auto max-w-lg"
      role="img"
      aria-label="Diagram of Newark-area rail lines converging on Newark Penn Station and Newark Broad Street"
    >
      {LINES.map((line, i) => (
        <g key={line.code}>
          <path
            d={line.path}
            fill="none"
            stroke={LINE_COLORS[line.code]}
            strokeWidth={3}
            strokeLinecap="round"
            opacity={0.85}
          />
          <circle r={5} fill={LINE_COLORS[line.code]}>
            <animateMotion
              dur={`${4 + i * 0.6}s`}
              repeatCount="indefinite"
              path={line.path}
            />
          </circle>
        </g>
      ))}

      {/* Broad St hub */}
      <circle cx="420" cy="190" r="10" fill="var(--surface)" stroke="var(--text-primary)" strokeWidth={2} />
      <text x="420" y="170" textAnchor="middle" className="font-mono" fontSize="13" fill="var(--text-secondary)">
        NWK BROAD ST
      </text>

      {/* Penn Station hub (larger -- the bigger interchange) */}
      <circle cx="260" cy="250" r="14" fill="var(--surface)" stroke="var(--text-primary)" strokeWidth={2.5} />
      <text x="260" y="290" textAnchor="middle" className="font-mono" fontSize="14" fill="var(--text-primary)" fontWeight={600}>
        NWK PENN STATION
      </text>

      <line x1="260" y1="250" x2="420" y2="190" stroke="var(--border)" strokeWidth={2} strokeDasharray="4 4" />
    </svg>
  );
}
