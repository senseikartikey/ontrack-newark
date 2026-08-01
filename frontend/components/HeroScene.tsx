import Image from "next/image";

/**
 * The hero's monumental image -- a real photo, replacing the earlier crafted
 * CSS/SVG placeholder now that a properly-licensed one exists (see
 * docs/landing-page-brief.md).
 *
 * Photo: NJ Transit ALP-46 locomotive #4655 at Newark Broad Street (the
 * station's actual clock tower is visible) -- the same station named in the
 * hero's technical marginalia. By Lexcie, via Wikimedia Commons, licensed
 * CC BY-SA 3.0: https://commons.wikimedia.org/wiki/File:ALP-46_NJT_4655_at_Newark_Broad_St.JPG
 * Original is a daytime shot; darkened/desaturated/grain-processed here per
 * the brief's "processed, never raw" rule -- this is a derivative work under
 * the same license, credited below per its ShareAlike terms.
 */
export default function HeroScene() {
  return (
    <div className="absolute inset-0 overflow-hidden" aria-hidden>
      <Image
        src="/hero-newark-broad-st.jpg"
        alt=""
        fill
        priority
        sizes="100vw"
        style={{
          objectFit: "cover",
          objectPosition: "center 55%",
          filter: "grayscale(0.8) sepia(0.15) contrast(1.15) brightness(0.48)",
        }}
      />

      {/* dark scrim so overlaid marginalia/headline stay legible */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(to top, rgba(12,10,8,0.95), rgba(12,10,8,0.25) 45%, rgba(12,10,8,0.72))",
        }}
      />
      <div
        className="absolute inset-x-0 bottom-0 h-2/3"
        style={{ background: "linear-gradient(to top, rgba(12,10,8,0.92), transparent)" }}
      />

      {/* required CC BY-SA 3.0 attribution */}
      <a
        href="https://commons.wikimedia.org/wiki/File:ALP-46_NJT_4655_at_Newark_Broad_St.JPG"
        target="_blank"
        rel="noopener noreferrer"
        className="absolute bottom-2 right-3 font-mono text-[0.625rem] hover:underline"
        style={{ color: "rgba(241,236,226,0.4)" }}
      >
        Photo: Lexcie / CC BY-SA 3.0, adapted
      </a>
    </div>
  );
}
