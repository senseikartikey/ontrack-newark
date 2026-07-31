/**
 * Crafted stand-in for the hero's "monumental image" -- no photography is
 * generated or sourced (see docs/landing-page-brief.md, v4). This is sized,
 * positioned, and toned exactly as the real thing will be, so a real photo
 * (Kartikey's own, or AI-generated once an image tool is connected) drops in
 * later with zero layout changes -- just swap this component for an <img>/
 * background-image with the same aspect and position.
 *
 * Composition: a dark vignette (evoking a platform/tunnel at night), one warm
 * signal-light glow off-center, and faint converging lines suggesting rail
 * perspective receding into the dark. Grain is layered on top via the
 * `.grain` utility on the parent section, not here.
 */
export default function HeroScene() {
  return (
    <div className="absolute inset-0 overflow-hidden" aria-hidden>
      {/* base vignette */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(120% 90% at 50% 115%, #241a10 0%, #120d09 45%, #0c0a08 75%)",
        }}
      />
      {/* signal glow */}
      <div
        className="absolute rounded-full"
        style={{
          width: "38rem",
          height: "38rem",
          left: "62%",
          top: "8%",
          background:
            "radial-gradient(circle, rgba(201,119,46,0.35) 0%, rgba(201,119,46,0.08) 45%, transparent 70%)",
          filter: "blur(20px)",
        }}
      />
      {/* converging rail lines */}
      <svg
        className="absolute inset-0 w-full h-full"
        viewBox="0 0 1200 800"
        preserveAspectRatio="xMidYMax slice"
      >
        {[-260, -140, -40, 60, 160, 280].map((offset) => (
          <line
            key={offset}
            x1={600 + offset * 2.6}
            y1="800"
            x2="600"
            y2="360"
            stroke="rgba(241,236,226,0.14)"
            strokeWidth="1.5"
          />
        ))}
        <line
          x1="0"
          y1="620"
          x2="1200"
          y2="620"
          stroke="rgba(241,236,226,0.08)"
          strokeWidth="1"
        />
      </svg>
      {/* bottom fade so overlaid text stays legible */}
      <div
        className="absolute inset-x-0 bottom-0 h-2/3"
        style={{
          background: "linear-gradient(to top, rgba(12,10,8,0.9), transparent)",
        }}
      />
    </div>
  );
}
