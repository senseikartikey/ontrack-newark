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
              40.7342°N <span className="marginalia-accent">·</span> 74.1645°W
            </div>
            <div>NEWARK PENN STATION</div>
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
              Your train is late.
              <br />
              You already knew that.
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.15 }}
              className="mt-6 max-w-md text-base leading-relaxed"
              style={{ color: "var(--paper-dim)" }}
            >
              NJ Transit tells you a train is delayed after you&apos;re already
              standing on the platform. OnTrack Newark predicts delay risk on
              Newark-area rail lines before you leave the house.
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
              className="mt-10 max-w-sm"
            >
              <HeroLiveStat />
            </motion.div>
          </div>
        </div>
      </section>

      {/* The problem */}
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
          <p className="marginalia mb-6">§ 01 — THE PROBLEM</p>
          <p
            className="type-monumental text-2xl md:text-4xl max-w-3xl"
            style={{ color: "var(--paper)" }}
          >
            Every Newark commuter has a story about a delay that had no
            warning. NJ Transit&apos;s own real-time feed already knows a
            train is running behind — it just doesn&apos;t tell you what
            tomorrow&apos;s 8:14 is likely to do.
          </p>
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
                body: "Live status and predicted risk, per line, refreshed continuously.",
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
              I&apos;m an AI data analyst and international student living in
              Newark. I ride these lines. NJ Transit&apos;s data is public and
              genuinely good — nobody had built the forward-looking layer on
              top of it yet, so I did. This is an active build: the ingestion
              pipeline is live, the prediction model ships once enough real
              delay history has accumulated. Follow the build in the{" "}
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
