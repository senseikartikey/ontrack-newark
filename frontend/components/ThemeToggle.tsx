"use client";

import { useEffect, useSyncExternalStore } from "react";

type Theme = "dark" | "light";

const STORAGE_KEY = "theme";
const THEME_EVENT = "ontrack-theme-change";

function subscribe(callback: () => void) {
  window.addEventListener(THEME_EVENT, callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener(THEME_EVENT, callback);
    window.removeEventListener("storage", callback);
  };
}

function getSnapshot(): Theme {
  return (window.localStorage.getItem(STORAGE_KEY) as Theme | null) ?? "dark";
}

function getServerSnapshot(): Theme {
  return "dark";
}

function setStoredTheme(theme: Theme) {
  window.localStorage.setItem(STORAGE_KEY, theme);
  window.dispatchEvent(new Event(THEME_EVENT));
}

export default function ThemeToggle() {
  // localStorage is an external store, not React state -- useSyncExternalStore
  // (rather than an effect + setState) is the correct primitive here and keeps
  // tabs in sync via the "storage" event for free.
  const theme = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  return (
    <button
      onClick={() => setStoredTheme(theme === "dark" ? "light" : "dark")}
      className="font-mono text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors border border-[var(--border)] rounded-full px-3 py-1"
      aria-label="Toggle color theme"
    >
      {theme === "dark" ? "○ dark" : "● light"}
    </button>
  );
}
