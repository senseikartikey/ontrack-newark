"use client";

import { useRef } from "react";
import Link from "next/link";
import { motion, useScroll, useTransform } from "motion/react";
import HeroLiveStat from "@/components/HeroLiveStat";
import PillNav from "@/components/PillNav";
import PipelineDiagram from "@/components/PipelineDiagram";
import StationIllustration from "@/components/StationIllustration";
import { LINE_COLORS } from "@/lib/lineColors";

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  show: { opacity: 1, y: 0 },
};

const STEP_ACCENTS = ["#e7b8c4", "#b9aee0", "#f4f2f8"];

export default function LandingPage() {
  const illustrationRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: illustrationRef,
    offset: ["start end", "end start"],
  });
  const illustrationY = useTransform(scrollYProgress, [0, 1], [40, -40]);

  return (
    <div className="flex-1 flex flex-col">
      <PillNav />

      {/* Hero */}
      <section className="section-ink grain overflow-hidden pt-36 pb-24 md:pt-44 md:pb-32">
        <div className="relative max-w-5xl mx-auto px-6 text-center">
          <motion.div
            initial="hidden"
            animate="show"
            variants={{ show: { transition: { staggerChildren: 0.12 } } }}
          >
            <motion.h1
              variants={fadeUp}
              transition={{ duration: 0.6, ease: "easeOut" }}
              className="wordmark text-6xl md:text-8xl mx-auto max-w-4xl"
            >
              your train is late.
              <br />
              <span style={{ color: "var(--rose)" }}>you already knew that.</span>
            </motion.h1>
            <motion.p
              variants={fadeUp}
              transition={{ duration: 0.6, ease: "easeOut" }}
              className="mt-8 text-white/70 text-lg leading-relaxed max-w-lg mx-auto"
            >
              NJ Transit tells you a train is delayed after you&apos;re already standing
              on the platform. OnTrack Newark predicts delay risk on Newark-area rail
              lines before you leave the house, using NJ Transit&apos;s own public data.
            </motion.p>
            <motion.div
              variants={fadeUp}
              transition={{ duration: 0.6, ease: "easeOut" }}
              className="mt-10 flex flex-col items-center gap-6"
            >
              <motion.div whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.98 }}>
                <Link
                  href="/dashboard"
                  className="inline-block rounded-full px-7 py-3.5 font-semibold text-base transition-shadow"
                  style={{ background: "var(--rose)", color: "var(--ink)" }}
                >
                  View live dashboard
                </Link>
              </motion.div>
              <div className="flex items-center gap-3 font-mono text-xs text-white/50 flex-wrap justify-center">
                {["NEC", "NJCL", "RARV", "BNTN", "MNE", "MNEG"].map((code) => (
                  <span key={code} className="flex items-center gap-1.5">
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
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-14 flex justify-center"
          >
            <HeroLiveStat />
          </motion.div>
        </div>
      </section>

      {/* Illustration block */}
      <section className="section-lavender grain overflow-hidden" ref={illustrationRef}>
        <div className="relative max-w-4xl mx-auto px-6 py-20">
          <motion.div style={{ y: illustrationY }}>
            <StationIllustration />
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
        className="section-ink grain"
      >
        <div className="relative max-w-5xl mx-auto px-6 py-20">
          <p className="font-mono text-xs text-white/40 uppercase tracking-wider">
            The problem
          </p>
          <p className="mt-4 text-2xl md:text-4xl font-display font-medium leading-snug max-w-2xl">
            Every Newark commuter has a story about a delay that had no warning. NJ
            Transit&apos;s own real-time feed already knows a train is running behind —
            it just doesn&apos;t tell you what tomorrow&apos;s 8:14 is likely to do.
          </p>
        </div>
      </motion.section>

      {/* How it works */}
      <section id="how" className="section-ink grain border-t border-white/10">
        <div className="relative max-w-5xl mx-auto px-6 py-20">
          <motion.p
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="font-mono text-xs text-white/40 uppercase tracking-wider mb-8"
          >
            How it works
          </motion.p>
          <div className="grid md:grid-cols-3 gap-6 mb-12">
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

      {/* Big wordmark divider */}
      <section className="section-ink grain border-t border-white/10 flex items-center justify-center py-24 md:py-32">
        <motion.span
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="wordmark text-7xl md:text-[10rem]"
          style={{ color: "var(--lavender)" }}
        >
          ontrack
        </motion.span>
      </section>

      {/* Founder note */}
      <motion.section
        id="why"
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "-80px" }}
        variants={fadeUp}
        transition={{ duration: 0.6 }}
        className="section-rose grain"
      >
        <div className="relative max-w-5xl mx-auto px-6 py-20">
          <p className="font-mono text-xs text-[var(--ink)]/50 uppercase tracking-wider mb-6">
            Why I&apos;m building this
          </p>
          <div className="rounded-2xl bg-[var(--ink)] text-white/90 font-mono text-sm p-7 max-w-2xl leading-relaxed">
            <p className="text-white/40">$ cat founder_note.txt</p>
            <p className="mt-3">
              I&apos;m an AI data analyst and international student living in Newark. I
              ride these lines. NJ Transit&apos;s data is public and genuinely good —
              nobody had built the forward-looking layer on top of it yet, so I did.
              This is an active build: the ingestion pipeline is live, the prediction
              model ships once enough real delay history has accumulated. Follow the
              build in the{" "}
              <a href="https://github.com" className="underline hover:text-white">
                GitHub repo
              </a>
              &apos;s engineering log.
            </p>
          </div>
        </div>
      </motion.section>

      <footer className="section-ink grain border-t border-white/10 mt-auto">
        <div className="relative max-w-5xl mx-auto px-6 py-8 flex items-center justify-between text-xs text-white/40 font-mono">
          <span>Built on public NJ Transit + NWS data. No PII collected.</span>
          <a href="https://github.com" className="hover:text-white">
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
      <h3 className="font-display font-semibold text-lg mt-1 text-white">{title}</h3>
      <p className="text-white/60 text-sm mt-2 leading-relaxed">{body}</p>
    </motion.div>
  );
}
