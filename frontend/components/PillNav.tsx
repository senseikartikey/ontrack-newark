"use client";

import Link from "next/link";
import { motion } from "motion/react";

export default function PillNav() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="fixed top-5 left-1/2 -translate-x-1/2 z-30 pill-nav px-2 py-2 flex items-center gap-1"
    >
      <span className="font-display font-bold text-sm text-white px-3">
        OnTrack
      </span>
      <NavLink href="#how">How it works</NavLink>
      <NavLink href="#why">Why</NavLink>
      <Link
        href="/dashboard"
        className="rounded-full text-sm font-medium px-4 py-2 transition-colors"
        style={{ background: "var(--rose)", color: "var(--ink)" }}
      >
        Live dashboard
      </Link>
    </motion.div>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      className="hidden sm:inline-block text-sm text-white/70 hover:text-white transition-colors px-3 py-2 rounded-full hover:bg-white/10"
    >
      {children}
    </a>
  );
}
