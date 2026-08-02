"use client";

import Link from "next/link";
import { motion } from "motion/react";

export default function TopNav() {
  return (
    <motion.header
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="absolute top-0 left-0 right-0 z-30"
    >
      <div className="max-w-6xl mx-auto px-6 md:px-10 py-6 flex items-center justify-between">
        <span
          className="font-mono text-xs tracking-[0.25em]"
          style={{ color: "var(--paper)" }}
        >
          ONTRACK
        </span>
        <div className="flex items-center gap-6">
          <Link
            href="/board"
            className="font-mono text-xs tracking-[0.15em]"
            style={{ color: "var(--paper-dim)" }}
          >
            LIVE BOARD
          </Link>
          <Link
            href="/hub"
            className="font-mono text-xs tracking-[0.15em]"
            style={{ color: "var(--paper-dim)" }}
          >
            TRANSFERS
          </Link>
          <Link
            href="/ny-penn"
            className="font-mono text-xs tracking-[0.15em]"
            style={{ color: "var(--paper-dim)" }}
          >
            NY PENN TRACKS
          </Link>
          <Link
            href="/dashboard"
            className="font-mono text-xs tracking-[0.15em] pb-1 border-b"
            style={{ color: "var(--paper)", borderColor: "var(--paper)" }}
          >
            VIEW DASHBOARD
          </Link>
        </div>
      </div>
    </motion.header>
  );
}
