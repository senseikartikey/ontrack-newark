"use client";

import Link from "next/link";
import { motion } from "motion/react";
import AuroraBackground from "@/components/AuroraBackground";
import HeroLiveStat from "@/components/HeroLiveStat";
import PipelineDiagram from "@/components/PipelineDiagram";
import RailMapVisual from "@/components/RailMapVisual";
import ThemeToggle from "@/components/ThemeToggle";
import { LINE_COLORS } from "@/lib/lineColors";

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  show: { opacity: 1, y: 0 },
};

const STEP_ACCENTS = ["#3987e5", "#d55181", "#9085e9"];

export default function LandingPage() {
  return (
    <div className="flex-1 flex flex-col">
      <motion.header
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="border-b border-[var(--border)] sticky top-0 z-20 backdrop-blur-md bg-[var(--page)]/70"
      >
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
              className="rounded-md bg-[var(--accent)] text-white px-3 py-1.5 font-medium hover:opacity-90 hover:shadow-[0_0_20px_-4px_var(--accent)] transition-all"
            >
              Live dashboard
            </Link>
            <ThemeToggle />
          </nav>
        </div>
      </motion.header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <AuroraBackground />
        <div className="relative max-w-5xl mx-auto px-6 py-20 md:py-28 grid md:grid-cols-[1.1fr_1fr] gap-12 items-center">
          <motion.div
            initial="hidden"
            animate="show"
            variants={{ show: { transition: { staggerChildren: 0.12 } } }}
          >
            <motion.h1
              variants={fadeUp}
              transition={{ duration: 0.6, ease: "easeOut" }}
              className="font-display font-extrabold text-5xl md:text-6xl leading-[1.05] tracking-tight"
            >
              Your train is late.
              <br />
              <span className="text-gradient">You already knew that.</span>
            </motion.h1>
            <motion.p
              variants={fadeUp}
              transition={{ duration: 0.6, ease: "easeOut" }}
              className="mt-6 text-[var(--text-secondary)] text-lg leading-relaxed max-w-md"
            >
              NJ Transit tells you a train is delayed after you&apos;re already standing on
              the platform. OnTrack Newark predicts delay risk on Newark-area rail lines
              before you leave the house, using NJ Transit&apos;s own public data.
            </motion.p>
            <motion.div
              variants={fadeUp}
              transition={{ duration: 0.6, ease: "easeOut" }}
              className="mt-8 flex items-center gap-4"
            >
              <motion.div whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.98 }}>
                <Link
                  href="/dashboard"
                  className="inline-block rounded-md bg-[var(--accent)] text-white px-5 py-2.5 font-medium shadow-[0_0_0px_0px_var(--accent)] hover:shadow-[0_0_28px_-4px_var(--accent)] transition-shadow"
                >
                  View live dashboard
                </Link>
              </motion.div>
              <div className="flex items-center gap-2 font-mono text-xs text-[var(--text-muted)]">
                {["NEC", "NJCL", "RARV", "BNTN", "MNE", "MNEG"].map((code) => (
                  <span key={code} className="flex items-center gap-1">
                    <span
                      className="inline-block w-2 h-2 rounded-full"
                      style={{ background: LINE_COLORS[code] }}
                    />
                    {code}
                  </span>
                ))}
              </div>
            </motion.div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.3, ease: "easeOut" }}
            className="relative flex flex-col items-center gap-4"
          >
            <RailMapVisual />
            <div className="self-end -mt-4 mr-2">
              <HeroLiveStat />
            </div>
          </motion.div>
        </div>
      </section>

      {/* Problem */}
      <motion.section
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "-80px" }}
        variants={fadeUp}
        transition={{ duration: 0.6 }}
        className="border-t border-[var(--border)]"
      >
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
      </motion.section>

      {/* How it works */}
      <section className="border-t border-[var(--border)]">
        <div className="max-w-5xl mx-auto px-6 py-16">
          <motion.p
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="font-mono text-xs text-[var(--text-muted)] uppercase tracking-wider mb-6"
          >
            How it works
          </motion.p>
          <div className="grid md:grid-cols-3 gap-6 mb-10">
            <Step
              n="01"
              accent={STEP_ACCENTS[0]}
              title="Ingest"
              body="Poll NJ Transit's public GTFS-RT feed and NWS weather every 60-120s. Every reading lands in Postgres, timestamped."
              delay={0}
            />
            <Step
              n="02"
              accent={STEP_ACCENTS[1]}
              title="Predict"
              body="A model trained on accumulated delay history, weather, and time-of-day scores upcoming departures for delay risk."
              delay={0.12}
            />
            <Step
              n="03"
              accent={STEP_ACCENTS[2]}
              title="Display"
              body="Live status and predicted risk, per line, refreshed continuously — the dashboard your commute deserves."
              delay={0.24}
            />
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

      {/* Founder note */}
      <motion.section
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "-80px" }}
        variants={fadeUp}
        transition={{ duration: 0.6 }}
        className="border-t border-[var(--border)]"
      >
        <div className="max-w-5xl mx-auto px-6 py-16">
          <p className="font-mono text-xs text-[var(--text-muted)] uppercase tracking-wider mb-6">
            Why I&apos;m building this
          </p>
          <div
            className="rounded-lg border border-[var(--border)] bg-[var(--surface)] font-mono text-sm p-6 max-w-2xl leading-relaxed"
            style={{ borderLeft: `3px solid ${STEP_ACCENTS[1]}` }}
          >
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
      </motion.section>

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

function Step({
  n,
  accent,
  title,
  body,
  delay,
}: {
  n: string;
  accent: string;
  title: string;
  body: string;
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
      whileHover={{ y: -4 }}
      className="pl-4"
      style={{ borderLeft: `2px solid ${accent}` }}
    >
      <span className="font-mono text-xs font-semibold" style={{ color: accent }}>
        {n}
      </span>
      <h3 className="font-display font-semibold text-lg mt-1">{title}</h3>
      <p className="text-[var(--text-secondary)] text-sm mt-2 leading-relaxed">{body}</p>
    </motion.div>
  );
}
