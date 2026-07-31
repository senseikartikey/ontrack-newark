import Link from "next/link";
import HeroLiveStat from "@/components/HeroLiveStat";
import PipelineDiagram from "@/components/PipelineDiagram";
import ThemeToggle from "@/components/ThemeToggle";

export default function LandingPage() {
  return (
    <div className="flex-1 flex flex-col">
      <header className="border-b border-[var(--border)]">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <span className="font-display font-bold text-lg tracking-tight">
            OnTrack Newark
          </span>
          <nav className="flex items-center gap-5 text-sm text-[var(--text-secondary)]">
            <a
              href="https://github.com"
              className="hover:text-[var(--text-primary)] transition-colors"
            >
              GitHub
            </a>
            <Link
              href="/dashboard"
              className="rounded-md bg-[var(--accent)] text-white px-3 py-1.5 font-medium hover:opacity-90 transition-opacity"
            >
              Live dashboard
            </Link>
            <ThemeToggle />
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-6 py-20 md:py-28 grid md:grid-cols-[1.2fr_1fr] gap-12 items-center">
        <div>
          <h1 className="font-display font-bold text-4xl md:text-5xl leading-[1.1] tracking-tight">
            Your train is late.
            <br />
            <span style={{ color: "var(--accent)" }}>You already knew that.</span>
          </h1>
          <p className="mt-6 text-[var(--text-secondary)] text-lg leading-relaxed max-w-md">
            NJ Transit tells you a train is delayed after you&apos;re already standing on
            the platform. OnTrack Newark predicts delay risk on Newark-area rail lines
            before you leave the house, using NJ Transit&apos;s own public data.
          </p>
          <div className="mt-8 flex items-center gap-4">
            <Link
              href="/dashboard"
              className="rounded-md bg-[var(--accent)] text-white px-5 py-2.5 font-medium hover:opacity-90 transition-opacity"
            >
              View live dashboard
            </Link>
            <span className="font-mono text-xs text-[var(--text-muted)]">
              Newark Penn · Newark Broad St
            </span>
          </div>
        </div>
        <div className="flex md:justify-end">
          <HeroLiveStat />
        </div>
      </section>

      {/* Problem */}
      <section className="border-t border-[var(--border)]">
        <div className="max-w-5xl mx-auto px-6 py-16">
          <p className="font-mono text-xs text-[var(--text-muted)] uppercase tracking-wider">
            The problem
          </p>
          <p className="mt-4 text-2xl md:text-3xl font-display font-medium leading-snug max-w-2xl">
            Every Newark commuter has a story about a delay that had no warning. NJ
            Transit&apos;s own real-time feed already knows a train is running behind —
            it just doesn&apos;t tell you what tomorrow&apos;s 8:14 is likely to do.
          </p>
        </div>
      </section>

      {/* How it works */}
      <section className="border-t border-[var(--border)]">
        <div className="max-w-5xl mx-auto px-6 py-16">
          <p className="font-mono text-xs text-[var(--text-muted)] uppercase tracking-wider mb-6">
            How it works
          </p>
          <div className="grid md:grid-cols-3 gap-6 mb-10">
            <Step
              n="01"
              title="Ingest"
              body="Poll NJ Transit's public GTFS-RT feed and NWS weather every 60-120s. Every reading lands in Postgres, timestamped."
            />
            <Step
              n="02"
              title="Predict"
              body="A model trained on accumulated delay history, weather, and time-of-day scores upcoming departures for delay risk."
            />
            <Step
              n="03"
              title="Display"
              body="Live status and predicted risk, per line, refreshed continuously — the dashboard your commute deserves."
            />
          </div>
          <PipelineDiagram />
        </div>
      </section>

      {/* Founder note */}
      <section className="border-t border-[var(--border)]">
        <div className="max-w-5xl mx-auto px-6 py-16">
          <p className="font-mono text-xs text-[var(--text-muted)] uppercase tracking-wider mb-6">
            Why I&apos;m building this
          </p>
          <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] font-mono text-sm p-6 max-w-2xl leading-relaxed">
            <p className="text-[var(--text-muted)]">$ cat founder_note.txt</p>
            <p className="mt-3 text-[var(--text-secondary)]">
              I&apos;m an AI data analyst and international student living in Newark. I
              ride these lines. NJ Transit&apos;s data is public and genuinely good —
              nobody had built the forward-looking layer on top of it yet, so I did.
              This is an active build: the ingestion pipeline is live, the prediction
              model ships once enough real delay history has accumulated. Follow the
              build in the{" "}
              <a
                href="https://github.com"
                className="underline hover:text-[var(--text-primary)]"
              >
                GitHub repo
              </a>
              &apos;s engineering log.
            </p>
          </div>
        </div>
      </section>

      <footer className="border-t border-[var(--border)] mt-auto">
        <div className="max-w-5xl mx-auto px-6 py-8 flex items-center justify-between text-xs text-[var(--text-muted)] font-mono">
          <span>Built on public NJ Transit + NWS data. No PII collected.</span>
          <a href="https://github.com" className="hover:text-[var(--text-primary)]">
            GitHub
          </a>
        </div>
      </footer>
    </div>
  );
}

function Step({ n, title, body }: { n: string; title: string; body: string }) {
  return (
    <div className="border-l-2 border-[var(--border)] pl-4">
      <span className="font-mono text-xs" style={{ color: "var(--accent)" }}>
        {n}
      </span>
      <h3 className="font-display font-semibold text-lg mt-1">{title}</h3>
      <p className="text-[var(--text-secondary)] text-sm mt-2 leading-relaxed">{body}</p>
    </div>
  );
}
