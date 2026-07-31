/**
 * Slow-drifting multi-hue glow behind the hero, built from the same categorical
 * palette used for line identity elsewhere on the page (not an arbitrary purple
 * blob) -- pure CSS animation (see .aurora-blob in globals.css), no JS cost.
 */
export default function AuroraBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden>
      <div className="aurora-blob aurora-blob-1" />
      <div className="aurora-blob aurora-blob-2" />
      <div className="aurora-blob aurora-blob-3" />
    </div>
  );
}
