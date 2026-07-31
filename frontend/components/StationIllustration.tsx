/**
 * Flat silhouette illustration in the reference's register (radiating sunburst
 * lines, soft cloud shapes, thick dark silhouette forms against a pastel block) --
 * built by hand from primitives since no image-generation tool is connected yet
 * (see ENGINEERING_LOG.md, 2026-07-31, on the Higgsfield MCP). Depicts the actual
 * product subject -- a train arriving at a Newark station platform -- rather than
 * a generic abstract shape, so it stays specific to OnTrack Newark.
 */
export default function StationIllustration() {
  const arcs = [90, 140, 190, 240, 290];

  return (
    <svg
      viewBox="0 0 640 520"
      className="w-full h-auto"
      role="img"
      aria-label="Illustration of a train arriving at a Newark rail platform"
    >
      <g opacity={0.35} stroke="var(--ink)" strokeWidth={1.5} fill="none">
        {arcs.map((r) => (
          <circle key={r} cx="320" cy="480" r={r} />
        ))}
      </g>

      {/* clouds */}
      <g fill="var(--ink)" opacity={0.08}>
        <ellipse cx="120" cy="120" rx="70" ry="26" />
        <ellipse cx="520" cy="90" rx="90" ry="30" />
      </g>

      {/* platform canopy */}
      <path d="M 80 300 L 560 300 L 520 260 L 120 260 Z" fill="var(--ink)" />
      <rect x="150" y="300" width="14" height="150" fill="var(--ink)" />
      <rect x="476" y="300" width="14" height="150" fill="var(--ink)" />

      {/* platform */}
      <rect x="40" y="450" width="560" height="26" rx="4" fill="var(--ink)" />

      {/* train body */}
      <g>
        <path
          d="M 130 330
             Q 130 310 150 310
             L 470 310
             Q 500 310 500 340
             L 500 430
             Q 500 450 480 450
             L 150 450
             Q 130 450 130 430
             Z"
          fill="var(--ink)"
        />
        {/* nose */}
        <path d="M 500 340 Q 530 345 534 380 Q 530 415 500 430 Z" fill="var(--ink)" />
        {/* headlight */}
        <circle cx="522" cy="382" r="7" fill="var(--rose)" />

        {/* windows */}
        {[170, 225, 280, 335, 390, 440].map((x) => (
          <rect key={x} x={x} y="330" width="34" height="40" rx="8" fill="var(--lavender)" />
        ))}

        {/* stripe */}
        <rect x="130" y="405" width="370" height="8" fill="var(--rose)" />

        {/* wheels */}
        {[180, 280, 380, 460].map((x) => (
          <circle key={x} cx={x} cy="455" r="14" fill="var(--ink)" />
        ))}
      </g>

      {/* sparkle accents */}
      <Sparkle x={100} y={200} size={16} />
      <Sparkle x={560} y={200} size={12} />
      <Sparkle x={580} y={340} size={10} />
    </svg>
  );
}

function Sparkle({ x, y, size }: { x: number; y: number; size: number }) {
  return (
    <path
      d={`M ${x} ${y - size} L ${x + size * 0.28} ${y - size * 0.28} L ${x + size} ${y} L ${x + size * 0.28} ${y + size * 0.28} L ${x} ${y + size} L ${x - size * 0.28} ${y + size * 0.28} L ${x - size} ${y} L ${x - size * 0.28} ${y - size * 0.28} Z`}
      fill="var(--ink)"
      opacity={0.5}
    />
  );
}
