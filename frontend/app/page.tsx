"use client";

import { motion } from "motion/react";
import HeroLiveStat from "@/components/HeroLiveStat";
import HeroScene from "@/components/HeroScene";
import PipelineDiagram from "@/components/PipelineDiagram";
import TopNav from "@/components/TopNav";

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  show: { opacity: 1, y: 0 },
};

export default function LandingPage() {
  return (
    <div className="flex-1 flex flex-col section-ink grain">
      {/* Hero -- one monumental image, technical marginalia, extreme type */}
      <section className="relative min-h-[92vh] flex items-end overflow-hidden">
        <HeroScene />
        <TopNav />

        <div className="relative w-full max-w-6xl mx-auto px-6 md:px-10 pb-16 md:pb-20 grid md:grid-cols-[auto_1fr] gap-10 items-end">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="marginalia hidden md:block whitespace-nowrap"
          >
            <div>PLATE II — TRANSIT LEDGER</div>
            <div>
              40.7476°N <span className="marginalia-accent">·</span> 74.1719°W
            </div>
            <div>NEWARK BROAD STREET</div>
            <div>LIVE SINCE 2026-07-30</div>
          </motion.div>

          <div>
            <motion.h1
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, ease: "easeOut" }}
              className="type-monumental text-5xl md:text-7xl max-w-2xl"
              style={{ color: "var(--paper)" }}
            >
              Know what&apos;s coming
              <br />
              before NJ Transit tells you.
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.15 }}
              className="mt-6 max-w-md text-base leading-relaxed"
              style={{ color: "var(--paper-dim)" }}
            >
              NJ Transit&apos;s app buries its own live board, skips transfers,
              and only tells you a train is late once you&apos;re already on
              the platform. OnTrack does all three — plus delay-risk
              prediction that gets smarter with real data — for every rail
              line in the state.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="mt-8 flex items-center gap-6 flex-wrap"
            >
              <a
                href="/dashboard"
                className="font-mono text-xs tracking-[0.1em] px-6 py-3 border transition-colors"
                style={{ borderColor: "var(--paper)", color: "var(--paper)" }}
              >
                VIEW LIVE DASHBOARD
              </a>
              <a
                href="#ledger"
                className="font-mono text-xs tracking-[0.1em]"
                style={{ color: "var(--paper-dim)" }}
              >
                READ THE LEDGER ↓
              </a>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="mt-10 max-w-md"
            >
              <HeroLiveStat />
            </motion.div>
          </div>
        </div>
      </section>

      {/* The problem, stated as concrete before/after pairs -- not a vague
          "every rider has a story" claim. Each pair maps directly to a real
          shipped page, so a first-time visitor knows what "Transfers" or
          "Live board" in the nav actually means before they ever click it. */}
      <motion.section
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "-80px" }}
        variants={fadeUp}
        transition={{ duration: 0.6 }}
        className="border-t"
        style={{ borderColor: "var(--hairline)" }}
      >
        <div className="max-w-6xl mx-auto px-6 md:px-10 py-20 md:py-28">
          <p className="marginalia mb-10">§ 01 — WHAT NJ TRANSIT&apos;S APP GETS WRONG</p>

          <div className="grid md:grid-cols-2 gap-x-12 gap-y-10 max-w-4xl">
            {[
              {
                gap: "Buries its own live departure board behind extra taps.",
                fix: "Every line, every station, one board — the way a physical sign works.",
                href: "/board",
              },
              {
                gap: "Doesn't show transfers up front anymore.",
                fix: "Search any two stations statewide, see what connects and when.",
                href: "/hub",
              },
              {
                gap: "Tells you a train is late only after you're on the platform.",
                fix: "Predicts delay risk before you leave, from real accumulated data — and gets more accurate as an ML model takes over from the statistical baseline.",
                href: "/dashboard",
              },
              {
                gap: "Riders don't trust its live data — trains vanish from tracking, timestamps go stale.",
                fix: "Flags it honestly when the underlying feed itself looks unreliable, instead of pretending it's fine.",
                href: "/dashboard",
              },
            ].map((item) => (
              <a key={item.gap} href={item.href} className="block group">
                <p
                  className="text-sm leading-relaxed"
                  style={{ color: "var(--paper-dim)" }}
                >
                  <span style={{ color: "var(--status-critical)" }}>NJ Transit: </span>
                  {item.gap}
                </p>
                <p
                  className="mt-2 text-base leading-relaxed font-medium group-hover:underline"
                  style={{ color: "var(--paper)" }}
                >
                  <span style={{ color: "var(--signal)" }}>OnTrack: </span>
                  {item.fix}
                </p>
              </a>
            ))}
          </div>
        </div>
      </motion.section>

      {/* How it works / ledger */}
      <section id="ledger" className="border-t" style={{ borderColor: "var(--hairline)" }}>
        <div className="max-w-6xl mx-auto px-6 md:px-10 py-20 md:py-28">
          <p className="marginalia mb-10">§ 02 — HOW IT WORKS</p>

          <div className="grid md:grid-cols-3 gap-8 mb-14">
            {[
              {
                n: "01",
                title: "Ingest",
                body: "Poll NJ Transit's public GTFS-RT feed and NWS weather every 5 minutes. Every reading lands in Postgres, timestamped.",
              },
              {
                n: "02",
                title: "Predict",
                body: "A model trained on accumulated delay history, weather, and time-of-day scores upcoming departures for delay risk.",
              },
              {
                n: "03",
                title: "Display",
                body: "Live status, predicted risk, station boards, and transfers — for any line, refreshed continuously.",
              },
            ].map((step, i) => (
              <motion.div
                key={step.n}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.12 }}
              >
                <p className="font-mono text-xs mb-2" style={{ color: "var(--signal)" }}>
                  {step.n}
                </p>
                <h3
                  className="type-monumental text-xl mb-2"
                  style={{ color: "var(--paper)" }}
                >
                  {step.title}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: "var(--paper-dim)" }}>
                  {step.body}
                </p>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={fadeUp}
            transition={{ duration: 0.6 }}
          >
            <PipelineDiagram />
          </motion.div>
        </div>
      </section>

      {/* Wordmark divider */}
      <section className="border-t flex items-center justify-center py-24 md:py-32" style={{ borderColor: "var(--hairline)" }}>
        <motion.span
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="type-monumental text-7xl md:text-[9rem]"
          style={{ color: "transparent", WebkitTextStroke: "1px var(--hairline)" }}
        >
          ontrack
        </motion.span>
      </section>

      {/* Founder note */}
      <motion.section
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "-80px" }}
        variants={fadeUp}
        transition={{ duration: 0.6 }}
        className="border-t"
        style={{ borderColor: "var(--hairline)" }}
      >
        <div className="max-w-6xl mx-auto px-6 md:px-10 py-20 md:py-28">
          <p className="marginalia mb-6">§ 03 — WHY I&apos;M BUILDING THIS</p>
          <div
            className="border font-mono text-sm p-7 max-w-2xl leading-relaxed"
            style={{ borderColor: "var(--hairline)", background: "var(--ink-raised)" }}
          >
            <p style={{ color: "var(--paper-dim)" }}>$ cat founder_note.txt</p>
            <p className="mt-3" style={{ color: "var(--paper)" }}>
              I&apos;m an AI data analyst and I ride these lines. No single
              app — not NJ Transit&apos;s, not any third-party one — combines
              a real live board, transfers, and delay prediction in one
              place, and none of them get smarter over time. NJ Transit&apos;s
              data is public and genuinely good, so I built the layer on top
              of it that actually solves the pain points riders complain
              about, statewide. This is an active build: the ingestion
              pipeline is live, the ML prediction model ships once enough
              real delay history has accumulated — until then, a statistical
              baseline holds the spot, honestly labeled as such. Follow the
              build in the{" "}
              <a
                href="https://github.com/senseikartikey/ontrack-newark"
                className="underline"
                style={{ color: "var(--paper)" }}
              >
                GitHub repo
              </a>
              &apos;s engineering log.
            </p>
          </div>
        </div>
      </motion.section>

      <footer className="border-t mt-auto" style={{ borderColor: "var(--hairline)" }}>
        <div
          className="max-w-6xl mx-auto px-6 md:px-10 py-8 flex items-center justify-between text-xs font-mono"
          style={{ color: "var(--paper-dim)" }}
        >
          <span>Built on public NJ Transit + NWS data. No PII collected.</span>
          <a
            href="https://github.com/senseikartikey/ontrack-newark"
            style={{ color: "var(--paper)" }}
          >
            GitHub
          </a>
        </div>
      </footer>
    </div>
  );
}
